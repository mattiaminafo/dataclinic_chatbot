# 📚 Guida Completa: Architettura e Logica del Chatbot RAG

Questa guida ti spiega come funziona il chatbot e come replicarlo in autonomia.

## 🏗️ Struttura del Progetto

```
Chatbot_dataclinic/
├── main.py                 # API FastAPI principale
├── retrieve_context.py     # Modulo per ricerca in Qdrant
├── upload_pdf.py          # Script per caricare PDF su Qdrant
├── requirements.txt        # Dipendenze Python
├── railway.json           # Configurazione deploy Railway
└── .env.local             # Variabili ambiente (non committato)
```

## 🔄 Flusso Completo del Sistema

### 1. Setup Iniziale

```
PDF → upload_pdf.py → Qdrant Vector Database
```

**Cosa succede:**
1. Carichi un PDF con `upload_pdf.py`
2. Lo script estrae il testo pagina per pagina
3. Divide il testo in "chunk" (pezzi) di ~1000 caratteri
4. Genera embeddings per ogni chunk usando OpenAI
5. Carica tutto su Qdrant con metadata (nome file, indice chunk)

### 2. Quando un Utente Fa una Domanda

```
Utente → FastAPI → retrieve_context.py → Qdrant → OpenAI Assistant → Risposta
```

**Passo per passo:**

1. **Utente invia domanda** → `POST /chat`
2. **FastAPI riceve** → `main.py` endpoint `/chat`
3. **Recupera contesto** → `retrieve_context.py`:
   - Genera embedding della domanda
   - Cerca in Qdrant i 3 chunk più simili
   - Restituisce i chunk rilevanti
4. **Prepara messaggio** → Aggiunge contesto alla domanda:
   ```
   [Informazioni dal PDF]
   Domanda: "Cos'è DataClinic?"
   ```
5. **Invia a OpenAI** → L'assistente genera risposta usando contesto + conoscenza
6. **Restituisce risposta** → All'utente

## 📝 Analisi Dettagliata dei File

### `main.py` - Il Cuore dell'API

```python
# 1. CONFIGURAZIONE
- Carica variabili ambiente (.env.local)
- Inizializza logging
- Crea app FastAPI
- Configura CORS

# 2. ENDPOINTS

GET /start
- Crea un nuovo thread OpenAI
- Restituisce thread_id

POST /chat
- Riceve thread_id + message
- Recupera contesto da Qdrant (retrieve_context.py)
- Aggiunge contesto al messaggio
- Invia a OpenAI Assistant
- Polling per completamento
- Restituisce risposta

GET /health
- Verifica stato API

GET /debug/env
- Debug variabili ambiente
```

**Punti chiave:**
- **Thread**: Ogni conversazione ha un thread_id univoco
- **Polling**: Aspetta che OpenAI completi la risposta (max 60 secondi)
- **Error handling**: Gestisce errori gracefully

### `retrieve_context.py` - Ricerca Vettoriale

```python
# FUNZIONI PRINCIPALI

get_qdrant_client()
- Crea/restituisce client Qdrant (singleton pattern)
- Usa variabili ambiente per configurazione

get_openai_client()
- Crea/restituisce client OpenAI (singleton pattern)

retrieve_relevant_context(query, top_k=3)
- Genera embedding della query
- Cerca in Qdrant usando query_points()
- Restituisce top_k risultati più rilevanti

format_context_for_prompt(contexts)
- Formatta i chunk per includerli nel prompt
```

**Come funziona la ricerca vettoriale:**
1. La domanda viene convertita in un vettore (embedding)
2. Qdrant confronta questo vettore con tutti i chunk nel database
3. Restituisce i più simili usando cosine similarity
4. Più alto lo score, più rilevante il chunk

### `upload_pdf.py` - Caricamento Documenti

```python
# FUNZIONI PRINCIPALI

extract_text_from_pdf()
- Legge PDF pagina per pagina
- Estrae testo usando pypdf
- Restituisce lista di pagine

split_text_into_chunks()
- Divide testo in chunk di ~1000 caratteri
- Overlap di 200 caratteri tra chunk
- Cerca punti di interruzione naturali (frasi)

generate_embeddings()
- Genera embeddings in batch (50 alla volta)
- Usa OpenAI text-embedding-3-small
- Evita problemi di memoria

upload_to_qdrant()
- Carica chunk in batch (100 alla volta)
- Crea PointStruct con ID, vector, payload
- Usa ID positivi (abs(hash()))

process_pdf()
- Orchestra tutto il processo
- Processa pagina per pagina
- Logging dettagliato
```

**Perché pagina per pagina?**
- Evita problemi di memoria con PDF grandi
- Permette di vedere progresso
- Più robusto

## 🧠 Concetti Chiave da Capire

### 1. Embeddings

**Cosa sono:**
- Rappresentazioni numeriche di testo come vettori
- Testi simili hanno vettori simili
- Permettono ricerca semantica (non solo keyword)

**Esempio:**
```
"Cos'è DataClinic?" → [0.123, -0.456, 0.789, ...] (1536 numeri)
"Che cosa fa DataClinic?" → [0.125, -0.454, 0.791, ...] (simile!)
```

### 2. Vector Database (Qdrant)

**Perché serve:**
- Cercare tra milioni di chunk velocemente
- Trovare contenuti simili semanticamente
- Non solo keyword matching

**Come funziona:**
- Ogni chunk è un punto nello spazio 1536-dimensionale
- La ricerca trova i punti più vicini alla query
- Cosine similarity misura la "vicinanza"

### 3. RAG (Retrieval Augmented Generation)

**Il problema che risolve:**
- LLM hanno conoscenza limitata a training data
- Non sanno informazioni specifiche della tua azienda
- Possono "allucinare" informazioni

**La soluzione:**
- Recupera informazioni rilevanti dal database
- Fornisci queste informazioni al LLM come contesto
- LLM genera risposta basata su contesto + conoscenza

### 4. Chunking

**Perché dividere in chunk:**
- LLM hanno limiti di token (max ~8000-32000)
- Chunk piccoli = ricerca più precisa
- Chunk grandi = più contesto ma meno preciso

**Strategia usata:**
- 1000 caratteri per chunk
- 200 caratteri di overlap
- Cerca punti di interruzione naturali

## 🔧 Come Modificare/Estendere

### Aggiungere più PDF

```bash
python upload_pdf.py documento1.pdf documento2.pdf documento3.pdf
```

Ogni PDF viene caricato nella stessa collection con metadata diverso.

### Cambiare numero di risultati

In `main.py`, modifica:
```python
relevant_contexts = retrieve_relevant_context(user_input, top_k=5)  # invece di 3
```

### Cambiare dimensione chunk

In `upload_pdf.py`, modifica:
```python
CHUNK_SIZE = 1500  # invece di 1000
CHUNK_OVERLAP = 300  # invece di 200
```

### Usare modello embedding diverso

In `retrieve_context.py` e `upload_pdf.py`, modifica:
```python
model="text-embedding-ada-002"  # invece di text-embedding-3-small
```

### Aggiungere filtri

In `retrieve_context.py`, puoi filtrare per source:
```python
from qdrant_client.models import Filter, FieldCondition, MatchValue

search_results = qdrant_client.query_points(
    collection_name=COLLECTION_NAME,
    query=Query(
        vector=QueryVector(vector=query_embedding),
        limit=top_k,
        filter=Filter(
            must=[
                FieldCondition(
                    key="source",
                    match=MatchValue(value="dataclinic.pdf")
                )
            ]
        )
    )
)
```

## 📊 Flusso Dati Dettagliato

### Caricamento PDF

```
PDF File
  ↓
extract_text_from_pdf()
  ↓
Lista di pagine (testo)
  ↓
split_text_into_chunks()
  ↓
Lista di chunk (8 chunk per esempio)
  ↓
generate_embeddings()
  ↓
Lista di vettori (1536 dimensioni ciascuno)
  ↓
upload_to_qdrant()
  ↓
Qdrant Database (8 punti con metadata)
```

### Query Utente

```
"Cos'è DataClinic?"
  ↓
retrieve_relevant_context()
  ↓
generate_embedding(query)
  ↓
Vettore query [0.123, -0.456, ...]
  ↓
query_points() su Qdrant
  ↓
3 chunk più rilevanti + score
  ↓
format_context_for_prompt()
  ↓
Stringa formattata con contesto
  ↓
Aggiunta al messaggio utente
  ↓
OpenAI Assistant API
  ↓
Risposta generata
```

## 🎯 Decisioni Architetturali

### Perché FastAPI?
- Async/await per performance
- Documentazione automatica (Swagger)
- Validazione automatica con Pydantic
- Facile da testare

### Perché Qdrant?
- Cloud managed (no server da gestire)
- API Python semplice
- Performance ottime per ricerca vettoriale
- Free tier generoso

### Perché OpenAI Assistant API?
- Gestisce thread automaticamente
- Mantiene contesto conversazione
- Più semplice di chiamate dirette a GPT
- Supporta file attachments (futuro)

### Perché pagina per pagina?
- Evita problemi memoria
- Più robusto
- Permette retry su singole pagine
- Logging più dettagliato

## 🚀 Come Replicare da Zero

### 1. Setup Base

```bash
# Crea progetto
mkdir my-chatbot
cd my-chatbot

# Virtual environment
python -m venv venv
source venv/bin/activate  # o venv\Scripts\activate su Windows

# Installa dipendenze base
pip install fastapi uvicorn python-dotenv openai qdrant-client pypdf
```

### 2. Crea struttura file

```bash
touch main.py retrieve_context.py upload_pdf.py requirements.txt .env.local
```

### 3. Configura variabili

Crea `.env.local`:
```env
OPENAI_API_KEY=sk-...
ASSISTANT_ID=asst_...
QDRANT_URL=https://...
QDRANT_API_KEY=...
```

### 4. Implementa in ordine

1. `main.py` - Endpoint base senza Qdrant
2. `upload_pdf.py` - Carica PDF
3. `retrieve_context.py` - Recupera contesto
4. Integra in `main.py`

### 5. Test locale

```bash
uvicorn main:app --reload
# Testa su http://localhost:8000/docs
```

### 6. Deploy

- Push su GitHub
- Connetti Railway
- Aggiungi variabili ambiente
- Deploy automatico!

## 💡 Tips e Best Practices

### Performance
- Usa batch per embeddings (50-100 alla volta)
- Processa PDF in chunk per evitare memory issues
- Cache client Qdrant/OpenAI (singleton pattern)

### Costi
- Usa `text-embedding-3-small` invece di `ada-002` (più economico)
- Limita numero di chunk recuperati (top_k=3 è spesso sufficiente)
- Monitora usage su OpenAI dashboard

### Sicurezza
- Mai committare `.env.local`
- Usa variabili ambiente su Railway
- Valida input utente (Pydantic)

### Debugging
- Logging dettagliato in ogni step
- Endpoint `/debug/env` per verificare configurazione
- Testa ogni componente separatamente

## 🔍 Domande Frequenti

**Q: Perché non uso direttamente GPT con i PDF?**
A: GPT ha limiti di token. Con RAG, puoi avere migliaia di pagine e cercare solo quelle rilevanti.

**Q: Posso usare altri vector database?**
A: Sì! Pinecone, Weaviate, ChromaDB. Cambia solo il client in `retrieve_context.py`.

**Q: Come miglioro la qualità delle risposte?**
A: 
- Migliora chunking (dimensioni, overlap)
- Aumenta top_k
- Migliora prompt engineering
- Aggiungi metadata per filtri

**Q: Posso caricare altri formati?**
A: Sì! Modifica `upload_pdf.py` per supportare DOCX, TXT, MD, ecc.

## 📚 Risorse per Approfondire

- [OpenAI Embeddings Guide](https://platform.openai.com/docs/guides/embeddings)
- [Qdrant Documentation](https://qdrant.tech/documentation/)
- [FastAPI Tutorial](https://fastapi.tiangolo.com/tutorial/)
- [RAG Paper](https://arxiv.org/abs/2005.11401)

---

Con questa guida hai tutto per replicare e modificare il progetto! 🚀

