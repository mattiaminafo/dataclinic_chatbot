# 🧪 Guida Completa: Come Testare il Chatbot

Questa guida ti mostra come testare ogni componente del chatbot per verificare che tutto funzioni correttamente.

---

## 📋 Checklist Pre-Test

Prima di iniziare, verifica che:

- [ ] Python 3.8+ installato
- [ ] Dipendenze installate: `pip install -r requirements.txt`
- [ ] File `.env.local` configurato con:
  - [ ] `OPENAI_API_KEY`
  - [ ] `ASSISTANT_ID`
  - [ ] `QDRANT_URL`
  - [ ] `QDRANT_API_KEY`
  - [ ] `QDRANT_COLLECTION_NAME` (opzionale, default: `dataclinic_docs`)

---

## 🧪 Test 1: Verifica Configurazione

### Test delle Variabili d'Ambiente

```bash
# Verifica che le variabili siano caricate
python -c "from dotenv import load_dotenv; import os; load_dotenv('.env.local'); print('OPENAI_API_KEY:', 'SET' if os.getenv('OPENAI_API_KEY') else 'NOT SET'); print('ASSISTANT_ID:', 'SET' if os.getenv('ASSISTANT_ID') else 'NOT SET'); print('QDRANT_URL:', 'SET' if os.getenv('QDRANT_URL') else 'NOT SET')"
```

**Risultato atteso:**
```
OPENAI_API_KEY: SET
ASSISTANT_ID: SET
QDRANT_URL: SET
```

---

## 🧪 Test 2: Caricamento PDF su Qdrant

### Test Base

```bash
# Carica il PDF di esempio
python upload_pdf.py dataclinic.pdf
```

**Risultato atteso:**
```
============================================================
Processando: dataclinic.pdf
============================================================
Caricando PDF: dataclinic.pdf
Caricati 1 documenti dal PDF
Creando index e caricando su Qdrant...
✅ dataclinic.pdf caricato su Qdrant con successo!
   Totale chunk caricati: XX
```

### Test con Più PDF

```bash
# Carica più PDF contemporaneamente
python upload_pdf.py documento1.pdf documento2.pdf documento3.pdf
```

### Verifica su Qdrant

Puoi verificare che i dati siano stati caricati usando il client Qdrant:

```python
from qdrant_client import QdrantClient
import os
from dotenv import load_dotenv

load_dotenv('.env.local')

client = QdrantClient(
    url=os.getenv('QDRANT_URL'),
    api_key=os.getenv('QDRANT_API_KEY')
)

# Conta i punti nella collection
collection_info = client.get_collection('dataclinic_docs')
print(f"Totale punti nella collection: {collection_info.points_count}")

# Recupera alcuni punti di esempio
from qdrant_client.models import ScrollRequest
points, _ = client.scroll(
    collection_name='dataclinic_docs',
    limit=3
)
for point in points:
    print(f"ID: {point.id}, Source: {point.payload.get('source')}")
```

---

## 🧪 Test 3: Test del Retrieval RAG

### Test del Modulo retrieve_context.py

Crea un file `test_retrieve.py`:

```python
#!/usr/bin/env python3
"""Test del modulo retrieve_context"""

from retrieve_context import retrieve_relevant_context, format_context_for_prompt

def test_retrieval():
    print("🔍 Test Retrieval RAG\n")
    print("=" * 50)
    
    # Test query
    query = "Cos'è DataClinic?"
    print(f"\nQuery: {query}\n")
    
    # Recupera contesto
    print("Recuperando contesto da Qdrant...")
    contexts = retrieve_relevant_context(query, top_k=3)
    
    if not contexts:
        print("❌ Nessun contesto trovato!")
        print("   Assicurati di aver caricato PDF con: python upload_pdf.py dataclinic.pdf")
        return
    
    print(f"✅ Trovati {len(contexts)} contesti rilevanti\n")
    
    # Mostra risultati
    for i, ctx in enumerate(contexts, 1):
        print(f"{i}. Score: {ctx['score']:.3f}")
        print(f"   Source: {ctx['source']}")
        print(f"   Text: {ctx['text'][:100]}...\n")
    
    # Test formattazione
    print("Formattazione contesto:")
    print("-" * 50)
    formatted = format_context_for_prompt(contexts)
    print(formatted[:500] + "..." if len(formatted) > 500 else formatted)

if __name__ == "__main__":
    test_retrieval()
```

Esegui:

```bash
python test_retrieve.py
```

**Risultato atteso:**
```
🔍 Test Retrieval RAG

==================================================
Query: Cos'è DataClinic?

Recuperando contesto da Qdrant...
✅ Trovati 3 contesti rilevanti

1. Score: 0.892
   Source: dataclinic.pdf
   Text: DataClinic è una piattaforma innovativa per l'analisi dei dati...

2. Score: 0.765
   Source: dataclinic.pdf
   Text: La piattaforma offre servizi di consulenza...

3. Score: 0.654
   Source: dataclinic.pdf
   Text: Per maggiori informazioni...
```

---

## 🧪 Test 4: Test dell'API FastAPI

### Avvia il Server

```bash
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

**Risultato atteso:**
```
INFO:     Uvicorn running on http://0.0.0.0:8000 (Press CTRL+C to quit)
INFO:     Started reloader process
INFO:     Started server process
INFO:     Waiting for application startup.
INFO:     Application startup complete.
```

### Test Health Check

```bash
curl http://localhost:8000/health
```

**Risultato atteso:**
```json
{
  "status": "healthy",
  "openai_version": "1.x.x",
  "assistant_id_set": true,
  "openai_api_key_set": true
}
```

### Test Debug Environment

```bash
curl http://localhost:8000/debug/env
```

Verifica che tutte le variabili siano configurate.

### Test Root Endpoint

```bash
curl http://localhost:8000/
```

**Risultato atteso:**
```json
{
  "message": "Chatbot DataClinic API",
  "version": "1.0.0",
  "endpoints": {
    "start": "/start",
    "chat": "/chat",
    "health": "/health"
  }
}
```

---

## 🧪 Test 5: Test Completo End-to-End

### Metodo 1: Usando lo Script di Test

```bash
# Assicurati che il server sia avviato in un altro terminale
# uvicorn main:app --reload

# Esegui il test
python test_chatbot.py
```

**Risultato atteso:**
```
🤖 Test Chatbot DataClinic

==================================================

1️⃣ Avvio nuova conversazione...
✅ Thread ID: thread_abc123...

1️⃣ Domanda: Cos'è DataClinic?
--------------------------------------------------
✅ Risposta:
DataClinic è una piattaforma innovativa per l'analisi dei dati...

2️⃣ Domanda: Cosa fa DataClinic?
--------------------------------------------------
✅ Risposta:
DataClinic offre servizi di consulenza e formazione...
```

### Metodo 2: Usando Swagger UI (Interfaccia Web)

1. Avvia il server:
   ```bash
   uvicorn main:app --reload
   ```

2. Apri il browser su:
   ```
   http://localhost:8000/docs
   ```

3. Testa gli endpoint:
   - Clicca su `GET /start` → "Try it out" → "Execute"
   - Copia il `thread_id` dalla risposta
   - Clicca su `POST /chat` → "Try it out"
   - Incolla il `thread_id` e inserisci un messaggio
   - Clicca "Execute"

### Metodo 3: Usando curl

```bash
# 1. Avvia conversazione
THREAD_ID=$(curl -s http://localhost:8000/start | python -c "import sys, json; print(json.load(sys.stdin)['thread_id'])")

echo "Thread ID: $THREAD_ID"

# 2. Invia messaggio
curl -X POST http://localhost:8000/chat \
  -H "Content-Type: application/json" \
  -d "{\"thread_id\": \"$THREAD_ID\", \"message\": \"Cos'è DataClinic?\"}"
```

### Metodo 4: Usando Python Requests

Crea un file `test_api.py`:

```python
#!/usr/bin/env python3
"""Test completo dell'API"""

import requests
import json

BASE_URL = "http://localhost:8000"

def test_complete_flow():
    print("🚀 Test Completo Chatbot\n")
    print("=" * 50)
    
    # 1. Health check
    print("\n1️⃣ Health Check...")
    response = requests.get(f"{BASE_URL}/health")
    print(f"Status: {response.json()['status']}")
    
    # 2. Avvia conversazione
    print("\n2️⃣ Avvio conversazione...")
    response = requests.get(f"{BASE_URL}/start")
    thread_id = response.json()["thread_id"]
    print(f"✅ Thread ID: {thread_id}")
    
    # 3. Test domande
    questions = [
        "Cos'è DataClinic?",
        "Quali servizi offre?",
        "Come posso contattarvi?"
    ]
    
    for i, question in enumerate(questions, 1):
        print(f"\n{i+2}️⃣ Domanda: {question}")
        print("-" * 50)
        
        response = requests.post(
            f"{BASE_URL}/chat",
            json={
                "thread_id": thread_id,
                "message": question
            },
            timeout=60
        )
        
        if response.status_code == 200:
            answer = response.json()["response"]
            print(f"✅ Risposta:\n{answer[:200]}...")
        else:
            print(f"❌ Errore: {response.status_code}")
            print(response.text)
    
    print("\n" + "=" * 50)
    print("✅ Test completato!")

if __name__ == "__main__":
    test_complete_flow()
```

Esegui:

```bash
python test_api.py
```

---

## 🧪 Test 6: Test di Performance

### Test Tempo di Risposta

```python
import time
import requests

BASE_URL = "http://localhost:8000"

# Avvia conversazione
response = requests.get(f"{BASE_URL}/start")
thread_id = response.json()["thread_id"]

# Test con timing
start = time.time()
response = requests.post(
    f"{BASE_URL}/chat",
    json={"thread_id": thread_id, "message": "Cos'è DataClinic?"},
    timeout=60
)
end = time.time()

print(f"Tempo di risposta: {end - start:.2f} secondi")
print(f"Status: {response.status_code}")
```

### Test Retrieval Performance

```python
import time
from retrieve_context import retrieve_relevant_context

# Test velocità retrieval
start = time.time()
contexts = retrieve_relevant_context("Cos'è DataClinic?", top_k=3)
end = time.time()

print(f"Retrieval completato in {end - start:.3f} secondi")
print(f"Trovati {len(contexts)} contesti")
```

---

## 🐛 Troubleshooting

### Errore: "Index non disponibile"

**Causa:** Qdrant non configurato o collection vuota

**Soluzione:**
```bash
# Verifica configurazione
python -c "from dotenv import load_dotenv; import os; load_dotenv('.env.local'); print('QDRANT_URL:', os.getenv('QDRANT_URL'))"

# Carica PDF
python upload_pdf.py dataclinic.pdf
```

### Errore: "OpenAI API key not found"

**Causa:** Variabile d'ambiente non configurata

**Soluzione:**
```bash
# Verifica .env.local
cat .env.local | grep OPENAI_API_KEY

# Se mancante, aggiungi:
echo "OPENAI_API_KEY=sk-proj-..." >> .env.local
```

### Errore: "Assistant run failed"

**Causa:** Assistant ID non valido o non configurato

**Soluzione:**
1. Verifica ASSISTANT_ID su OpenAI Dashboard
2. Assicurati che sia configurato in `.env.local`
3. Verifica che l'assistant abbia le giuste configurazioni

### Errore: "Connection refused"

**Causa:** Server non avviato

**Soluzione:**
```bash
uvicorn main:app --reload
```

### Errore: "Timeout"

**Causa:** OpenAI impiega troppo tempo

**Soluzione:**
- Aumenta timeout in `main.py` (riga 207): `max_attempts = 120`
- Verifica connessione internet
- Controlla status OpenAI API

### Nessun contesto recuperato

**Causa:** PDF non caricato o query non rilevante

**Soluzione:**
```bash
# Verifica che PDF sia caricato
python upload_pdf.py dataclinic.pdf

# Testa retrieval direttamente
python test_retrieve.py
```

---

## ✅ Checklist Test Completo

Usa questa checklist per verificare che tutto funzioni:

- [ ] **Configurazione**
  - [ ] Variabili d'ambiente configurate
  - [ ] Health check passa

- [ ] **Caricamento PDF**
  - [ ] PDF caricato su Qdrant
  - [ ] Chunk visibili su Qdrant

- [ ] **Retrieval RAG**
  - [ ] Retrieval restituisce risultati
  - [ ] Score di similarità ragionevoli (>0.5)
  - [ ] Formattazione contesto corretta

- [ ] **API FastAPI**
  - [ ] Server avviato senza errori
  - [ ] Endpoint `/start` funziona
  - [ ] Endpoint `/chat` funziona
  - [ ] Endpoint `/health` funziona

- [ ] **Test End-to-End**
  - [ ] Conversazione completa funziona
  - [ ] Risposte contengono informazioni dal PDF
  - [ ] Thread mantiene contesto conversazione

- [ ] **Performance**
  - [ ] Tempo di risposta < 10 secondi
  - [ ] Retrieval < 1 secondo

---

## 📊 Test Avanzati

### Test con Query Multiple

```python
queries = [
    "Cos'è DataClinic?",
    "Quali servizi offre?",
    "Come funziona?",
    "Chi può usarlo?",
    "Quanto costa?"
]

for query in queries:
    contexts = retrieve_relevant_context(query, top_k=3)
    print(f"Query: {query}")
    print(f"Risultati: {len(contexts)}")
    if contexts:
        print(f"Best score: {contexts[0]['score']:.3f}\n")
```

### Test Conversazione Multi-Turn

```python
import requests

BASE_URL = "http://localhost:8000"

# Avvia conversazione
thread_id = requests.get(f"{BASE_URL}/start").json()["thread_id"]

# Domande correlate
questions = [
    "Cos'è DataClinic?",
    "Puoi darmi più dettagli?",
    "E quali sono i vantaggi?"
]

for q in questions:
    response = requests.post(
        f"{BASE_URL}/chat",
        json={"thread_id": thread_id, "message": q}
    )
    print(f"Q: {q}")
    print(f"A: {response.json()['response'][:100]}...\n")
```

---

## 🎯 Test di Validazione

### Verifica Qualità Risposte

1. **Rilevanza:** La risposta è pertinente alla domanda?
2. **Accuratezza:** Le informazioni sono corrette?
3. **Completezza:** La risposta è completa?
4. **Contesto:** Usa informazioni dal PDF?

### Test con Domande Fuori Contesto

```python
# Domande che NON dovrebbero trovare contesto
out_of_context = [
    "Come cucinare la pasta?",
    "Qual è la capitale della Francia?",
    "Come funziona Python?"
]

for query in out_of_context:
    contexts = retrieve_relevant_context(query, top_k=3)
    if contexts:
        # Se trova risultati, verifica che siano rilevanti
        best_score = contexts[0]['score']
        print(f"Query: {query}, Best score: {best_score:.3f}")
        if best_score < 0.3:
            print("✅ Corretto: nessun contesto rilevante")
```

---

**Con questa guida puoi testare completamente il chatbot! 🚀**

Per domande o problemi, consulta la sezione Troubleshooting o la `GUIDA_ARCHITETTURA.md`.

