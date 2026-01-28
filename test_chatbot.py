#!/usr/bin/env python3
"""
Script semplice per testare il chatbot.
Assicurati che il server sia avviato con: uvicorn main:app --reload
"""

import requests
import json

BASE_URL = "http://localhost:8000"

def test_chatbot():
    print("🤖 Test Chatbot DataClinic\n")
    print("=" * 50)
    
    # 1. Avvia una nuova conversazione
    print("\n1️⃣ Avvio nuova conversazione...")
    try:
        response = requests.get(f"{BASE_URL}/start")
        response.raise_for_status()
        data = response.json()
        thread_id = data["thread_id"]
        print(f"✅ Thread ID: {thread_id}\n")
    except requests.exceptions.ConnectionError:
        print("❌ Errore: Il server non è avviato!")
        print("   Avvia con: uvicorn main:app --reload")
        return
    except Exception as e:
        print(f"❌ Errore: {e}")
        return
    
    # 2. Fai alcune domande
    questions = [
        "Cos'è DataClinic?",
        "Cosa fa DataClinic?",
        "Quali servizi offre DataClinic?"
    ]
    
    for i, question in enumerate(questions, 1):
        print(f"\n{i}️⃣ Domanda: {question}")
        print("-" * 50)
        
        try:
            response = requests.post(
                f"{BASE_URL}/chat",
                json={
                    "thread_id": thread_id,
                    "message": question
                },
                timeout=60  # Timeout di 60 secondi
            )
            response.raise_for_status()
            data = response.json()
            answer = data["response"]
            
            print(f"✅ Risposta:\n{answer}\n")
            
        except requests.exceptions.Timeout:
            print("⏱️ Timeout: La risposta ha impiegato troppo tempo")
        except Exception as e:
            print(f"❌ Errore: {e}")
            if hasattr(e, 'response') and e.response is not None:
                print(f"   Dettagli: {e.response.text}")
    
    print("\n" + "=" * 50)
    print("✅ Test completato!")

if __name__ == "__main__":
    test_chatbot()

