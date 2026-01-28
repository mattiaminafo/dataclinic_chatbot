#!/usr/bin/env python3
"""
Script completo per testare tutti i componenti del chatbot.
Esegue test automatici di configurazione, retrieval e API.
"""

import os
import sys
import time
from pathlib import Path
from dotenv import load_dotenv

# Carica variabili d'ambiente
load_dotenv('.env.local')
load_dotenv()

def print_header(text):
    """Stampa un header formattato"""
    print("\n" + "=" * 60)
    print(f"  {text}")
    print("=" * 60)

def print_success(text):
    """Stampa un messaggio di successo"""
    print(f"✅ {text}")

def print_error(text):
    """Stampa un messaggio di errore"""
    print(f"❌ {text}")

def print_info(text):
    """Stampa un messaggio informativo"""
    print(f"ℹ️  {text}")

def test_configuration():
    """Test 1: Verifica configurazione"""
    print_header("TEST 1: Configurazione")
    
    required_vars = {
        'OPENAI_API_KEY': os.getenv('OPENAI_API_KEY'),
        'ASSISTANT_ID': os.getenv('ASSISTANT_ID'),
        'QDRANT_URL': os.getenv('QDRANT_URL'),
        'QDRANT_API_KEY': os.getenv('QDRANT_API_KEY'),
    }
    
    all_ok = True
    for var_name, var_value in required_vars.items():
        if var_value:
            print_success(f"{var_name}: Configurato")
        else:
            print_error(f"{var_name}: NON configurato")
            all_ok = False
    
    if not all_ok:
        print_error("\nConfigura le variabili mancanti in .env.local")
        return False
    
    print_success("Tutte le variabili d'ambiente sono configurate!")
    return True

def test_imports():
    """Test 2: Verifica importazioni"""
    print_header("TEST 2: Importazioni Librerie")
    
    try:
        import fastapi
        print_success(f"FastAPI: {fastapi.__version__}")
    except ImportError:
        print_error("FastAPI non installato")
        return False
    
    try:
        import openai
        print_success(f"OpenAI: {openai.__version__}")
    except ImportError:
        print_error("OpenAI non installato")
        return False
    
    try:
        from llama_index.core import VectorStoreIndex
        print_success("LlamaIndex: Installato")
    except ImportError:
        print_error("LlamaIndex non installato")
        return False
    
    try:
        from qdrant_client import QdrantClient
        print_success("Qdrant Client: Installato")
    except ImportError:
        print_error("Qdrant Client non installato")
        return False
    
    print_success("Tutte le librerie sono installate!")
    return True

def test_qdrant_connection():
    """Test 3: Verifica connessione Qdrant"""
    print_header("TEST 3: Connessione Qdrant")
    
    try:
        from qdrant_client import QdrantClient
        
        qdrant_url = os.getenv('QDRANT_URL')
        qdrant_key = os.getenv('QDRANT_API_KEY')
        
        if not qdrant_url or not qdrant_key:
            print_error("QDRANT_URL o QDRANT_API_KEY non configurati")
            return False
        
        client = QdrantClient(url=qdrant_url, api_key=qdrant_key)
        
        # Prova a ottenere le collections
        collections = client.get_collections()
        print_success(f"Connesso a Qdrant: {len(collections.collections)} collections trovate")
        
        # Verifica collection dataclinic_docs
        collection_name = os.getenv('QDRANT_COLLECTION_NAME', 'dataclinic_docs')
        collection_names = [col.name for col in collections.collections]
        
        if collection_name in collection_names:
            collection_info = client.get_collection(collection_name)
            points_count = collection_info.points_count
            print_success(f"Collection '{collection_name}': {points_count} punti")
            
            if points_count == 0:
                print_info("⚠️  Collection vuota! Carica PDF con: python upload_pdf.py dataclinic.pdf")
                return False
        else:
            print_error(f"Collection '{collection_name}' non trovata!")
            print_info("Carica PDF con: python upload_pdf.py dataclinic.pdf")
            return False
        
        return True
        
    except Exception as e:
        print_error(f"Errore connessione Qdrant: {e}")
        return False

def test_retrieval():
    """Test 4: Test retrieval RAG"""
    print_header("TEST 4: Retrieval RAG")
    
    try:
        from retrieve_context import retrieve_relevant_context
        
        query = "Cos'è DataClinic?"
        print_info(f"Query di test: '{query}'")
        
        start = time.time()
        contexts = retrieve_relevant_context(query, top_k=3)
        elapsed = time.time() - start
        
        if not contexts:
            print_error("Nessun contesto recuperato!")
            print_info("Assicurati di aver caricato PDF con: python upload_pdf.py dataclinic.pdf")
            return False
        
        print_success(f"Recuperati {len(contexts)} contesti in {elapsed:.3f} secondi")
        
        # Mostra risultati
        for i, ctx in enumerate(contexts, 1):
            score = ctx.get('score', 0.0)
            source = ctx.get('source', 'unknown')
            text_preview = ctx.get('text', '')[:80] + '...' if len(ctx.get('text', '')) > 80 else ctx.get('text', '')
            
            print(f"  {i}. Score: {score:.3f} | Source: {source}")
            print(f"     Text: {text_preview}")
        
        # Verifica score minimo
        best_score = contexts[0].get('score', 0.0) if contexts else 0.0
        if best_score < 0.3:
            print_info("⚠️  Score basso - potrebbe indicare che il PDF non contiene informazioni rilevanti")
        
        return True
        
    except Exception as e:
        print_error(f"Errore durante retrieval: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_api_server():
    """Test 5: Verifica se il server API è avviato"""
    print_header("TEST 5: Server API")
    
    try:
        import requests
        
        # Prova health check
        response = requests.get("http://localhost:8000/health", timeout=5)
        
        if response.status_code == 200:
            data = response.json()
            print_success("Server API raggiungibile!")
            print(f"  Status: {data.get('status')}")
            print(f"  OpenAI Version: {data.get('openai_version')}")
            return True
        else:
            print_error(f"Server risponde con status {response.status_code}")
            return False
            
    except requests.exceptions.ConnectionError:
        print_error("Server non raggiungibile!")
        print_info("Avvia il server con: uvicorn main:app --reload")
        return False
    except Exception as e:
        print_error(f"Errore: {e}")
        return False

def test_api_endpoints():
    """Test 6: Test endpoint API"""
    print_header("TEST 6: Endpoint API")
    
    try:
        import requests
        
        # Test /start
        print_info("Test endpoint /start...")
        response = requests.get("http://localhost:8000/start", timeout=10)
        
        if response.status_code != 200:
            print_error(f"Endpoint /start fallito: {response.status_code}")
            return False
        
        thread_id = response.json().get('thread_id')
        if not thread_id:
            print_error("Thread ID non restituito")
            return False
        
        print_success(f"Endpoint /start: OK (Thread ID: {thread_id[:20]}...)")
        
        # Test /chat
        print_info("Test endpoint /chat...")
        response = requests.post(
            "http://localhost:8000/chat",
            json={
                "thread_id": thread_id,
                "message": "Test: Cos'è DataClinic?"
            },
            timeout=60
        )
        
        if response.status_code != 200:
            print_error(f"Endpoint /chat fallito: {response.status_code}")
            print_error(f"Dettagli: {response.text}")
            return False
        
        answer = response.json().get('response', '')
        if not answer:
            print_error("Risposta vuota")
            return False
        
        print_success(f"Endpoint /chat: OK")
        print(f"  Risposta: {answer[:100]}...")
        
        return True
        
    except requests.exceptions.Timeout:
        print_error("Timeout durante test endpoint")
        return False
    except Exception as e:
        print_error(f"Errore: {e}")
        return False

def main():
    """Esegue tutti i test"""
    print("\n" + "=" * 60)
    print("  🧪 TEST COMPLETO CHATBOT DATACLINIC")
    print("=" * 60)
    
    results = []
    
    # Test configurazione
    results.append(("Configurazione", test_configuration()))
    
    # Test importazioni
    results.append(("Importazioni", test_imports()))
    
    # Test Qdrant
    results.append(("Connessione Qdrant", test_qdrant_connection()))
    
    # Test retrieval
    results.append(("Retrieval RAG", test_retrieval()))
    
    # Test server API
    api_server_ok = test_api_server()
    results.append(("Server API", api_server_ok))
    
    # Test endpoint solo se server OK
    if api_server_ok:
        results.append(("Endpoint API", test_api_endpoints()))
    else:
        results.append(("Endpoint API", False))
        print_info("Skippato test endpoint - server non disponibile")
    
    # Riepilogo
    print_header("RIEPILOGO TEST")
    
    passed = sum(1 for _, result in results if result)
    total = len(results)
    
    for name, result in results:
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"  {status}: {name}")
    
    print(f"\nRisultato: {passed}/{total} test passati")
    
    if passed == total:
        print_success("\n🎉 Tutti i test sono passati! Il chatbot è pronto!")
        return 0
    else:
        print_error(f"\n⚠️  {total - passed} test falliti. Controlla i dettagli sopra.")
        return 1

if __name__ == "__main__":
    sys.exit(main())

