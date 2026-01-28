"""
Modulo per recuperare contesto rilevante da Qdrant basato su una query.
"""

import os
import logging
from typing import List, Dict
from dotenv import load_dotenv
from qdrant_client import QdrantClient
from openai import OpenAI

# Configurazione logging
logger = logging.getLogger(__name__)

# Carica variabili d'ambiente
load_dotenv('.env.local')
load_dotenv()

# Configurazione
QDRANT_URL = os.getenv('QDRANT_URL', 'https://3295f9b4-ebee-474a-957d-da07a46a4a80.europe-west3-0.gcp.cloud.qdrant.io')
QDRANT_API_KEY = os.getenv('QDRANT_API_KEY', 'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJhY2Nlc3MiOiJtIn0.6hMeqzzUolOcOG5baapb2lH2trSuLoRvPbQaCiLtHkk')
OPENAI_API_KEY = os.getenv('OPENAI_API_KEY')
COLLECTION_NAME = os.getenv('QDRANT_COLLECTION_NAME', 'dataclinic_docs')

# Inizializza client (saranno None se le chiavi non sono impostate)
_qdrant_client = None
_openai_client = None

def get_qdrant_client() -> QdrantClient:
    """Ottiene o crea il client Qdrant."""
    global _qdrant_client
    if _qdrant_client is None and QDRANT_API_KEY:
        _qdrant_client = QdrantClient(
            url=QDRANT_URL,
            api_key=QDRANT_API_KEY,
        )
    return _qdrant_client

def get_openai_client() -> OpenAI:
    """Ottiene o crea il client OpenAI."""
    global _openai_client
    if _openai_client is None and OPENAI_API_KEY:
        _openai_client = OpenAI(api_key=OPENAI_API_KEY)
    return _openai_client

def retrieve_relevant_context(query: str, top_k: int = 3) -> List[Dict]:
    """
    Recupera i chunk più rilevanti da Qdrant per una query.
    
    Args:
        query: La query dell'utente
        top_k: Numero di risultati da recuperare
    
    Returns:
        Lista di dizionari con 'text', 'source', 'score'
    """
    qdrant_client = get_qdrant_client()
    openai_client = get_openai_client()
    
    if not qdrant_client or not openai_client:
        return []
    
    try:
        # Genera embedding per la query
        response = openai_client.embeddings.create(
            model="text-embedding-3-small",
            input=[query]
        )
        query_embedding = response.data[0].embedding
        
        # Cerca in Qdrant usando query_points
        from qdrant_client.models import Query, QueryVector
        
        search_results = qdrant_client.query_points(
            collection_name=COLLECTION_NAME,
            query=Query(
                vector=QueryVector(
                    vector=query_embedding,
                    using=None  # Usa il vettore di default
                ),
                limit=top_k
            )
        )
        
        # Formatta risultati
        results = []
        for point in search_results.points:
            results.append({
                'text': point.payload.get('text', ''),
                'source': point.payload.get('source', 'unknown'),
                'score': point.score if hasattr(point, 'score') else 0.0
            })
        
        return results
    
    except Exception as e:
        logger.error(f"Errore durante il retrieval: {e}")
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

