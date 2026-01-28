"""
Modulo per recuperare contesto rilevante da Qdrant usando LlamaIndex.
Riscritto con LlamaIndex per semplificare il codice e migliorare le performance.
"""

import os
import logging
from typing import List, Dict
from dotenv import load_dotenv

# Configurazione logging
logger = logging.getLogger(__name__)

# Carica variabili d'ambiente
load_dotenv('.env.local')
load_dotenv()

# Importa LlamaIndex
try:
    from llama_index.core import VectorStoreIndex, StorageContext
    from llama_index.vector_stores.qdrant import QdrantVectorStore
    from llama_index.embeddings.openai import OpenAIEmbedding
    from qdrant_client import QdrantClient
except ImportError as e:
    logger.error(f"Errore: libreria LlamaIndex mancante. Installa con: pip install -r requirements.txt")
    logger.error(f"Dettaglio: {e}")
    raise

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

# Singleton per evitare reinizializzazioni
_index = None

def get_index():
    """Ottiene o crea l'index LlamaIndex (singleton pattern)."""
    global _index
    
    if _index is None:
        if not QDRANT_API_KEY or not OPENAI_API_KEY:
            logger.warning("QDRANT_API_KEY o OPENAI_API_KEY non configurate")
            return None
        
        try:
            # Setup client Qdrant
            qdrant_client = QdrantClient(
                url=QDRANT_URL,
                api_key=QDRANT_API_KEY,
            )
            
            # Setup vector store
            vector_store = QdrantVectorStore(
                client=qdrant_client,
                collection_name=COLLECTION_NAME
            )
            
            # Setup embedding model
            embed_model = OpenAIEmbedding(
                model="text-embedding-3-small",
                api_key=OPENAI_API_KEY
            )
            
            # Crea storage context
            storage_context = StorageContext.from_defaults(vector_store=vector_store)
            
            # Carica index esistente da Qdrant
            _index = VectorStoreIndex.from_vector_store(
                vector_store=vector_store,
                embed_model=embed_model
            )
            
            logger.info("Index LlamaIndex inizializzato con successo")
        except Exception as e:
            logger.error(f"Errore durante l'inizializzazione dell'index: {e}")
            import traceback
            traceback.print_exc()
            return None
    
    return _index

def retrieve_relevant_context(query: str, top_k: int = 3) -> List[Dict]:
    """
    Recupera i chunk più rilevanti da Qdrant usando LlamaIndex.
    
    Args:
        query: La query dell'utente
        top_k: Numero di risultati da recuperare
    
    Returns:
        Lista di dizionari con 'text', 'source', 'score'
    """
    index = get_index()
    
    if index is None:
        logger.warning("Index non disponibile, restituendo lista vuota")
        return []
    
    try:
        # Crea retriever con top_k dinamico
        retriever = index.as_retriever(similarity_top_k=top_k)
        
        # LlamaIndex gestisce automaticamente:
        # 1. Generazione embedding della query
        # 2. Ricerca in Qdrant
        # 3. Recupero dei risultati più rilevanti
        
        # Usa retrieve() per ottenere i nodi (restituisce NodeWithScore)
        nodes = retriever.retrieve(query)
        
        # Formatta risultati nel formato originale per compatibilità
        results = []
        for node_with_score in nodes:
            # LlamaIndex restituisce NodeWithScore che ha:
            # - node: il nodo con testo e metadata
            # - score: lo score di similarità
            node = node_with_score.node if hasattr(node_with_score, 'node') else node_with_score
            score = getattr(node_with_score, 'score', 0.0)
            
            # Estrai testo e metadata dal nodo
            text = getattr(node, 'text', '') if hasattr(node, 'text') else str(node)
            metadata = getattr(node, 'metadata', {}) if hasattr(node, 'metadata') else {}
            source = metadata.get('source', 'unknown')
            
            results.append({
                'text': text,
                'source': source,
                'score': float(score) if score else 0.0
            })
        
        logger.info(f"Recuperati {len(results)} contesti rilevanti per la query")
        return results
    
    except Exception as e:
        logger.error(f"Errore durante il retrieval: {e}")
        import traceback
        traceback.print_exc()
        return []

def format_context_for_prompt(contexts: List[Dict]) -> str:
    """
    Formatta i contesti recuperati per includerli nel prompt.
    
    Args:
        contexts: Lista di contesti recuperati
    
    Returns:
        Stringa formattata con il contesto
    """
    if not contexts:
        return ""
    
    formatted = "\n\n--- Informazioni rilevanti da DataClinic ---\n\n"
    
    for idx, ctx in enumerate(contexts, 1):
        formatted += f"[Fonte: {ctx['source']}]\n{ctx['text']}\n\n"
    
    formatted += "--- Fine informazioni ---\n\n"
    
    return formatted
