"""
Script per caricare PDF su Qdrant Vector Database.
Estrae il testo dai PDF, lo divide in chunks, genera embeddings con OpenAI e li carica su Qdrant.
"""

import os
import sys
from pathlib import Path
from typing import List
import logging
from dotenv import load_dotenv

# Carica variabili d'ambiente
load_dotenv('.env.local')
load_dotenv()

# Importa librerie
try:
    from qdrant_client import QdrantClient
    from qdrant_client.models import Distance, VectorParams, PointStruct
    from openai import OpenAI
    import pypdf
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
QDRANT_URL = os.getenv('QDRANT_URL', 'https://3295f9b4-ebee-474a-957d-da07a46a4a80.europe-west3-0.gcp.cloud.qdrant.io')
QDRANT_API_KEY = os.getenv('QDRANT_API_KEY', 'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJhY2Nlc3MiOiJtIn0.6hMeqzzUolOcOG5baapb2lH2trSuLoRvPbQaCiLtHkk')
OPENAI_API_KEY = os.getenv('OPENAI_API_KEY')
COLLECTION_NAME = os.getenv('QDRANT_COLLECTION_NAME', 'dataclinic_docs')

# Configurazione chunking
CHUNK_SIZE = 1000  # Caratteri per chunk
CHUNK_OVERLAP = 200  # Overlap tra chunk

def extract_text_from_pdf(pdf_path: Path) -> List[str]:
    """Estrae il testo da un PDF pagina per pagina."""
    logger.info(f"Estraendo testo da {pdf_path}...")
    pages_text = []
    
    try:
        with open(pdf_path, 'rb') as file:
            pdf_reader = pypdf.PdfReader(file)
            for page_num, page in enumerate(pdf_reader.pages):
                page_text = page.extract_text()
                if page_text.strip():
                    pages_text.append(page_text.strip())
            logger.info(f"Estratte {len(pdf_reader.pages)} pagine")
    except Exception as e:
        logger.error(f"Errore durante l'estrazione del testo: {e}")
        raise
    
    return pages_text

def split_text_into_chunks(text: str, chunk_size: int = CHUNK_SIZE, overlap: int = CHUNK_OVERLAP) -> List[str]:
    """Divide il testo in chunk con overlap."""
    if len(text) <= chunk_size:
        return [text]
    
    chunks = []
    start = 0
    
    while start < len(text):
        end = start + chunk_size
        
        # Cerca un punto di interruzione naturale (fine frase o paragrafo)
        if end < len(text):
            # Cerca l'ultimo punto, punto esclamativo o punto interrogativo
            for punct in ['. ', '.\n', '! ', '!\n', '? ', '?\n', '\n\n']:
                last_punct = text.rfind(punct, start, end)
                if last_punct != -1:
                    end = last_punct + len(punct)
                    break
        
        chunk = text[start:end].strip()
        if chunk:
            chunks.append(chunk)
        
        # Avanza considerando l'overlap
        start = end - overlap if end < len(text) else end
    
    logger.info(f"Testo diviso in {len(chunks)} chunk")
    return chunks

def generate_embeddings(texts: List[str], client: OpenAI, model: str = "text-embedding-3-small", batch_size: int = 50) -> List[List[float]]:
    """Genera embeddings per una lista di testi usando OpenAI, processando in batch."""
    logger.info(f"Generando embeddings per {len(texts)} chunk (batch size: {batch_size})...")
    
    all_embeddings = []
    
    try:
        # Processa in batch per evitare problemi di memoria
        for i in range(0, len(texts), batch_size):
            batch = texts[i:i + batch_size]
            logger.info(f"Processando batch {i//batch_size + 1}/{(len(texts) + batch_size - 1)//batch_size} ({len(batch)} chunk)...")
            
            response = client.embeddings.create(
                model=model,
                input=batch
            )
            batch_embeddings = [item.embedding for item in response.data]
            all_embeddings.extend(batch_embeddings)
        
        logger.info(f"✅ Embeddings generati con successo per tutti i {len(texts)} chunk")
        return all_embeddings
    except Exception as e:
        logger.error(f"Errore durante la generazione degli embeddings: {e}")
        raise

def create_collection_if_not_exists(client: QdrantClient, collection_name: str, vector_size: int = 1536):
    """Crea la collection su Qdrant se non esiste."""
    try:
        collections = client.get_collections()
        collection_names = [col.name for col in collections.collections]
        
        if collection_name not in collection_names:
            logger.info(f"Creando collection '{collection_name}'...")
            client.create_collection(
                collection_name=collection_name,
                vectors_config=VectorParams(
                    size=vector_size,
                    distance=Distance.COSINE
                )
            )
            logger.info(f"Collection '{collection_name}' creata con successo")
        else:
            logger.info(f"Collection '{collection_name}' già esistente")
    except Exception as e:
        logger.error(f"Errore durante la creazione della collection: {e}")
        raise

def upload_to_qdrant(
    client: QdrantClient,
    collection_name: str,
    chunks: List[str],
    embeddings: List[List[float]],
    pdf_name: str,
    batch_size: int = 100,
    start_id: int = 0
):
    """Carica i chunk e gli embeddings su Qdrant in batch."""
    logger.info(f"Caricando {len(chunks)} chunk su Qdrant (batch size: {batch_size})...")
    
    total_uploaded = 0
    
    try:
        # Carica in batch per evitare problemi di memoria
        for i in range(0, len(chunks), batch_size):
            batch_chunks = chunks[i:i + batch_size]
            batch_embeddings = embeddings[i:i + batch_size]
            
            points = []
            for idx, (chunk, embedding) in enumerate(zip(batch_chunks, batch_embeddings)):
                # Usa abs() per assicurarsi che l'ID sia positivo, oppure usa un contatore
                # Qdrant richiede ID unsigned integer o UUID
                point_id = abs(hash(f"{pdf_name}_{start_id + i + idx}")) % (2**63)  # Limita a 64-bit unsigned
                
                point = PointStruct(
                    id=point_id,
                    vector=embedding,
                    payload={
                        "text": chunk,
                        "source": pdf_name,
                        "chunk_index": start_id + i + idx
                    }
                )
                points.append(point)
            
            client.upsert(
                collection_name=collection_name,
                points=points
            )
            total_uploaded += len(points)
            logger.info(f"✅ Caricati {total_uploaded}/{len(chunks)} punti su Qdrant...")
        
        logger.info(f"✅ Caricati tutti i {len(chunks)} punti su Qdrant con successo")
    except Exception as e:
        logger.error(f"Errore durante il caricamento su Qdrant: {e}")
        raise

def process_pdf(pdf_path: Path, qdrant_client: QdrantClient, openai_client: OpenAI):
    """Processa un singolo PDF e lo carica su Qdrant, pagina per pagina."""
    pdf_name = pdf_path.name
    
    logger.info(f"\n{'='*60}")
    logger.info(f"Processando: {pdf_name}")
    logger.info(f"{'='*60}")
    
    # 1. Estrai testo pagina per pagina
    pages_text = extract_text_from_pdf(pdf_path)
    if not pages_text:
        logger.warning(f"Nessun testo estratto da {pdf_name}")
        return
    
    all_chunks = []
    all_embeddings = []
    chunk_counter = 0  # Contatore globale per ID univoci
    
    # Processa pagina per pagina per evitare problemi di memoria
    for page_num, page_text in enumerate(pages_text, 1):
        logger.info(f"Processando pagina {page_num}/{len(pages_text)}...")
        
        # 2. Dividi la pagina in chunk
        page_chunks = split_text_into_chunks(page_text)
        
        if not page_chunks:
            continue
        
        # 3. Genera embeddings per questa pagina (batch piccolo)
        page_embeddings = generate_embeddings(page_chunks, openai_client, batch_size=20)
        
        # 4. Carica immediatamente su Qdrant (batch piccolo)
        upload_to_qdrant(
            qdrant_client, 
            COLLECTION_NAME, 
            page_chunks, 
            page_embeddings, 
            pdf_name,  # Usa solo il nome del PDF, non la pagina
            batch_size=50,
            start_id=chunk_counter
        )
        
        chunk_counter += len(page_chunks)
        all_chunks.extend(page_chunks)
        logger.info(f"✅ Pagina {page_num} processata: {len(page_chunks)} chunk caricati")
    
    logger.info(f"✅ {pdf_name} processato e caricato con successo!")
    logger.info(f"   Totale: {len(all_chunks)} chunk da {len(pages_text)} pagine\n")

def main():
    """Funzione principale."""
    # Verifica configurazione
    if not OPENAI_API_KEY:
        logger.error("OPENAI_API_KEY non trovata nelle variabili d'ambiente!")
        sys.exit(1)
    
    if not QDRANT_API_KEY:
        logger.error("QDRANT_API_KEY non trovata nelle variabili d'ambiente!")
        sys.exit(1)
    
    # Inizializza client
    logger.info("Inizializzando client...")
    qdrant_client = QdrantClient(
        url=QDRANT_URL,
        api_key=QDRANT_API_KEY,
    )
    
    openai_client = OpenAI(api_key=OPENAI_API_KEY)
    
    # Crea collection se non esiste
    create_collection_if_not_exists(qdrant_client, COLLECTION_NAME)
    
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
            process_pdf(pdf_path, qdrant_client, openai_client)
        except Exception as e:
            logger.error(f"Errore durante il processing di {pdf_path}: {e}")
            continue
    
    logger.info("\n✅ Processo completato!")

if __name__ == "__main__":
    main()

