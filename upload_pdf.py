"""
Script per caricare PDF su Qdrant Vector Database usando LlamaIndex.
Estrae il testo dai PDF, lo divide in chunks, genera embeddings con OpenAI e li carica su Qdrant.
Riscritto con LlamaIndex per semplificare il codice.
"""

import os
import sys
from pathlib import Path
import logging
from dotenv import load_dotenv

# Carica variabili d'ambiente
load_dotenv('.env.local')
load_dotenv()

# Importa librerie LlamaIndex
try:
    from llama_index.core import VectorStoreIndex, SimpleDirectoryReader, StorageContext
    from llama_index.core.node_parser import SentenceSplitter
    from llama_index.vector_stores.qdrant import QdrantVectorStore
    from llama_index.embeddings.openai import OpenAIEmbedding
    from qdrant_client import QdrantClient
except ImportError as e:
    print(f"Errore: libreria mancante. Installa con: pip install -r requirements.txt")
    print(f"Dettaglio: {e}")
    sys.exit(1)

# Configurazione logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Configurazione
# IMPORTANTE: Configura queste variabili nel file .env.local o come variabili d'ambiente
# Non committare mai valori hardcoded nel repository!
QDRANT_URL = os.getenv('QDRANT_URL')
QDRANT_API_KEY = os.getenv('QDRANT_API_KEY')
OPENAI_API_KEY = os.getenv('OPENAI_API_KEY')
COLLECTION_NAME = os.getenv('QDRANT_COLLECTION_NAME', 'dataclinic_docs')

# Validazione: verifica che le variabili essenziali siano configurate
if not QDRANT_URL or not QDRANT_API_KEY:
    logger.warning(
        "QDRANT_URL o QDRANT_API_KEY non configurate. "
        "Configura queste variabili nel file .env.local o come variabili d'ambiente."
    )

# Configurazione chunking (stesse dimensioni del codice originale)
CHUNK_SIZE = 1000  # Caratteri per chunk
CHUNK_OVERLAP = 200  # Overlap tra chunk

def setup_vector_store():
    """Setup del vector store Qdrant con LlamaIndex."""
    qdrant_client = QdrantClient(
        url=QDRANT_URL,
        api_key=QDRANT_API_KEY,
    )
    
    vector_store = QdrantVectorStore(
        client=qdrant_client,
        collection_name=COLLECTION_NAME
    )
    
    return vector_store, qdrant_client

def process_pdf(pdf_path: Path):
    """Processa un PDF e lo carica su Qdrant usando LlamaIndex."""
    pdf_name = pdf_path.name
    
    logger.info(f"\n{'='*60}")
    logger.info(f"Processando: {pdf_name}")
    logger.info(f"{'='*60}")
    
    # Setup vector store
    vector_store, qdrant_client = setup_vector_store()
    
    # Setup embedding model
    embed_model = OpenAIEmbedding(
        model="text-embedding-3-small",
        api_key=OPENAI_API_KEY
    )
    
    # Configura text splitter con le stesse dimensioni del codice originale
    text_splitter = SentenceSplitter(
        chunk_size=CHUNK_SIZE,
        chunk_overlap=CHUNK_OVERLAP
    )
    
    # Carica PDF (LlamaIndex gestisce automaticamente estrazione e chunking)
    logger.info(f"Caricando PDF: {pdf_path}")
    documents = SimpleDirectoryReader(
        input_files=[str(pdf_path)]
    ).load_data()
    
    logger.info(f"Caricati {len(documents)} documenti dal PDF")
    
    # Aggiungi metadata source a tutti i documenti
    for doc in documents:
        if not doc.metadata.get('source'):
            doc.metadata['source'] = pdf_name
    
    # Crea storage context
    storage_context = StorageContext.from_defaults(vector_store=vector_store)
    
    # Crea index e carica su Qdrant (tutto automatico!)
    # LlamaIndex gestisce:
    # - Chunking con SentenceSplitter
    # - Generazione embeddings in batch
    # - Upload su Qdrant con metadata
    logger.info("Creando index e caricando su Qdrant...")
    index = VectorStoreIndex.from_documents(
        documents,
        storage_context=storage_context,
        embed_model=embed_model,
        transformations=[text_splitter],  # Usa il nostro text splitter configurato
        show_progress=True  # Mostra progresso
    )
    
    # Conta i nodi caricati
    num_nodes = len(index.docstore.docs)
    logger.info(f"✅ {pdf_name} caricato su Qdrant con successo!")
    logger.info(f"   Totale chunk caricati: {num_nodes}\n")

def main():
    """Funzione principale."""
    # Verifica configurazione
    if not OPENAI_API_KEY:
        logger.error("OPENAI_API_KEY non trovata nelle variabili d'ambiente!")
        sys.exit(1)
    
    if not QDRANT_API_KEY:
        logger.error("QDRANT_API_KEY non trovata nelle variabili d'ambiente!")
        sys.exit(1)
    
    # Processa PDF
    if len(sys.argv) < 2:
        logger.error("Uso: python upload_pdf.py <path_to_pdf> [altri_pdf...]")
        logger.info("Esempio: python upload_pdf.py documenti/dataclinic.pdf documenti/info.pdf")
        sys.exit(1)
    
    pdf_paths = [Path(p) for p in sys.argv[1:]]
    
    for pdf_path in pdf_paths:
        if not pdf_path.exists():
            logger.error(f"File non trovato: {pdf_path}")
            continue
        
        if pdf_path.suffix.lower() != '.pdf':
            logger.warning(f"Ignorando file non-PDF: {pdf_path}")
            continue
        
        try:
            process_pdf(pdf_path)
        except Exception as e:
            logger.error(f"Errore durante il processing di {pdf_path}: {e}")
            import traceback
            traceback.print_exc()
            continue
    
    logger.info("\n✅ Processo completato!")

if __name__ == "__main__":
    main()
