# 📚 Guida Completa: Architettura e Struttura del Chatbot RAG

Questa guida completa spiega come è stato costruito il chatbot, come funziona ogni componente e come estenderlo.

---

## 🏗️ Architettura del Sistema

### Panoramica Generale

Il chatbot è un sistema **RAG (Retrieval Augmented Generation)** che combina:
- **Vector Database (Qdrant)** per la ricerca semantica
- **LlamaIndex** per la gestione di documenti e retrieval
- **OpenAI Assistant API** per la generazione di risposte
- **FastAPI** come framework web

```
┌─────────────┐
│   Utente    │
└──────┬──────┘
       │
       ▼
┌─────────────────────────────────────────────────────────┐
│                    FastAPI Server                        │
│                  (main.py)                               │
│  ┌──────────┐  ┌──────────────┐  ┌──────────────────┐  │
│  │  /start  │  │    /chat     │  │  /health, /debug │  │
│  └──────────┘  └──────┬───────┘  └──────────────────┘  │
└───────────────────────┼──────────────────────────────────┘
                        │
                        ▼
            ┌───────────────────────┐
            │  retrieve_context.py  │
            │   (LlamaIndex RAG)    │
            └───────────┬───────────┘
                        │
        ┌───────────────┼───────────────┐
        │               │               │
        ▼               ▼               ▼
┌─────────────┐ ┌─────────────┐ ┌──────────────┐
│   Qdrant    │ │   OpenAI    │ │ OpenAI       │
│  Vector DB  │ │ Embeddings  │ │ Assistant    │
└─────────────┘ └─────────────┘ └──────────────┘
```

---

## 📁 Struttura del Progetto

```
Chatbot_dataclinic/
├── main.py                 # API FastAPI principale (327 righe)
├── retrieve_context.py     # Modulo RAG con LlamaIndex (163 righe)
├── upload_pdf.py          # Script caricamento PDF con LlamaIndex (158 righe)
├── test_chatbot.py        # Test funzionali
├── requirements.txt        # Dipendenze Python
├── railway.json           # Configurazione deploy Railway
├── dataclinic.pdf         # Documento di esempio
│
├── README.md              # Documentazione principale
├── GUIDA_ARCHITETTURA.md  # Questa guida
├── QDRANT_SETUP.md        # Setup Qdrant dettagliato
├── QUICK_START_QDRANT.md  # Quick start Qdrant
└── RAILWAY_DEPLOY.md      # Guida deploy Railway
```

---

## 🔄 Flusso Completo del Sistema

### Fase 1: Setup Iniziale (Caricamento Documenti)

```
PDF File
  │
  ▼
upload_pdf.py
  │
  ├─► SimpleDirectoryReader (LlamaIndex)
  │   └─► Estrae testo dal PDF
  │
  ├─► SentenceSplitter (LlamaIndex)
  │   └─► Divide in chunk di 1000 caratteri (overlap 200)
  │
  ├─► OpenAIEmbedding (LlamaIndex)
  │   └─► Genera embeddings per ogni chunk (1536 dimensioni)
  │
  └─► QdrantVectorStore (LlamaIndex)
      └─► Carica chunk + embeddings + metadata su Qdrant
```

**Cosa succede:**
1. Lo script `upload_pdf.py` legge il PDF
2. LlamaIndex estrae automaticamente il testo
3. Il testo viene diviso in chunk intelligenti (rispetta i confini delle frasi)
4. Per ogni chunk viene generato un embedding usando OpenAI
5. Chunk, embeddings e metadata vengono caricati su Qdrant

### Fase 2: Query Utente (Conversazione)

```
Utente → POST /chat
  │
  ├─► FastAPI riceve richiesta
  │
  ├─► retrieve_context.py
  │   │
  │   ├─► get_index() - Carica index LlamaIndex da Qdrant
  │   │
  │   ├─► retriever.retrieve(query)
  │   │   │
  │   │   ├─► Genera embedding della query (automatico)
  │   │   │
  │   │   ├─► Cerca in Qdrant i top_k chunk più simili
  │   │   │
  │   │   └─► Restituisce NodeWithScore (nodo + score)
  │   │
  │   └─► format_context_for_prompt()
  │       └─► Formatta contesti per il prompt
  │
  ├─► Prepara messaggio con contesto
  │   └─► "[Contesto dal PDF]\nDomanda: {user_input}"
  │
  ├─► OpenAI Assistant API
  │   │
  │   ├─► Crea/aggiorna thread
  │   │
  │   ├─► Aggiunge messaggio utente con contesto
  │   │
  │   ├─► Crea run per l'assistente
  │   │
  │   └─► Polling fino a completamento
  │
  └─► Restituisce risposta all'utente
```

**Passo per passo:**
1. Utente invia domanda → `POST /chat` con `thread_id` e `message`
2. FastAPI valida input e chiama `retrieve_relevant_context()`
3. LlamaIndex genera embedding della query automaticamente
4. Qdrant cerca i 3 chunk più simili (cosine similarity)
5. I contesti vengono formattati e aggiunti al messaggio utente
6. Il messaggio completo viene inviato a OpenAI Assistant API
7. OpenAI genera risposta usando contesto + conoscenza pre-addestrata
8. La risposta viene restituita all'utente

---

## 📝 Analisi Dettagliata dei File

### `main.py` - Il Cuore dell'API (327 righe)

**Responsabilità:**
- Gestisce tutte le richieste HTTP
- Coordina il flusso tra retrieval e generazione
- Gestisce thread OpenAI e polling

**Struttura:**

```python
# 1. CONFIGURAZIONE (righe 1-91)
- Carica variabili ambiente (.env.local → .env)
- Configura logging
- Valida versione OpenAI
- Crea app FastAPI
- Configura CORS
- Inizializza client OpenAI

# 2. MODELLI PYDANTIC (righe 92-105)
- ChatRequest: thread_id + message
- ChatResponse: response + thread_id
- StartResponse: thread_id + message

# 3. ENDPOINTS (righe 107-325)
- GET /start: Crea nuovo thread OpenAI
- POST /chat: Gestisce messaggio con RAG
- GET /health: Health check
- GET /debug/env: Debug variabili ambiente
- GET /: Info API
```

**Flusso Endpoint `/chat`:**

```python
@app.post('/chat')
async def chat(chat_request: ChatRequest):
    # 1. Validazione input
    # 2. Recupera contesto da Qdrant
    relevant_contexts = retrieve_relevant_context(user_input, top_k=3)
    
    # 3. Formatta contesto
    context_text = format_context_for_prompt(relevant_contexts)
    
    # 4. Prepara messaggio con contesto
    enhanced_message = f"{context_text}Domanda dell'utente: {user_input}"
    
    # 5. Aggiungi messaggio al thread OpenAI
    client.beta.threads.messages.create(
        thread_id=thread_id,
        role="user",
        content=enhanced_message
    )
    
    # 6. Crea run per l'assistente
    run = client.beta.threads.runs.create(
        thread_id=thread_id,
        assistant_id=ASSISTANT_ID
    )
    
    # 7. Polling fino a completamento (max 60 secondi)
    while run_status.status != 'completed':
        await asyncio.sleep(1)
        run_status = client.beta.threads.runs.retrieve(...)
    
    # 8. Recupera e restituisce risposta
    messages = client.beta.threads.messages.list(thread_id)
    return ChatResponse(response=messages.data[0].content[0].text.value)
```

**Punti chiave:**
- **Thread Management**: Ogni conversazione ha un `thread_id` univoco che mantiene il contesto
- **Polling**: Aspetta che OpenAI completi la risposta (timeout 60 secondi)
- **Error Handling**: Gestisce gracefully errori di rete, timeout, API errors
- **Logging**: Log dettagliato di ogni operazione per debugging

---

### `retrieve_context.py` - Modulo RAG con LlamaIndex (163 righe)

**Responsabilità:**
- Gestisce la connessione a Qdrant
- Esegue retrieval semantico usando LlamaIndex
- Formatta contesti per il prompt

**Struttura:**

```python
# 1. CONFIGURAZIONE (righe 1-33)
- Carica variabili ambiente
- Importa LlamaIndex e Qdrant
- Configurazione Qdrant e OpenAI

# 2. SINGLETON PATTERN (righe 35-82)
_index = None  # Cache globale dell'index

def get_index():
    """Crea/carica index LlamaIndex da Qdrant (singleton)"""
    global _index
    if _index is None:
        # Setup Qdrant client
        # Setup vector store
        # Setup embedding model
        # Carica index esistente
        _index = VectorStoreIndex.from_vector_store(...)
    return _index

# 3. RETRIEVAL (righe 84-140)
def retrieve_relevant_context(query, top_k=3):
    """Recupera chunk rilevanti usando LlamaIndex"""
    index = get_index()
    retriever = index.as_retriever(similarity_top_k=top_k)
    nodes = retriever.retrieve(query)
    # Formatta risultati
    return results

# 4. FORMATTAZIONE (righe 142-162)
def format_context_for_prompt(contexts):
    """Formatta contesti per includerli nel prompt"""
    # Crea stringa formattata con source e testo
    return formatted_string
```

**Come funziona LlamaIndex:**

1. **Index Creation**: 
   - LlamaIndex crea un `VectorStoreIndex` che si connette a Qdrant
   - L'index viene cachato (singleton) per evitare reinizializzazioni

2. **Retrieval**:
   - `retriever.retrieve(query)` gestisce automaticamente:
     - Generazione embedding della query
     - Ricerca in Qdrant (cosine similarity)
     - Ranking dei risultati per score
   - Restituisce `NodeWithScore` objects con:
     - `node.text`: Testo del chunk
     - `node.metadata`: Metadata (source, etc.)
     - `score`: Score di similarità (0-1)

3. **Vantaggi LlamaIndex**:
   - ✅ Meno codice (gestisce tutto automaticamente)
   - ✅ Caching intelligente (index singleton)
   - ✅ Gestione errori robusta
   - ✅ Supporto per filtri avanzati (metadata filtering)

**Ricerca Vettoriale - Come Funziona:**

```
Query: "Cos'è DataClinic?"
  │
  ▼
Embedding: [0.123, -0.456, 0.789, ..., 0.234] (1536 dimensioni)
  │
  ▼
Qdrant Vector Search
  │
  ├─► Confronta con tutti i chunk nel database
  │
  ├─► Calcola cosine similarity per ogni chunk
  │
  ├─► Ordina per score (più alto = più rilevante)
  │
  └─► Restituisce top_k risultati
```

**Esempio di risultati:**

```python
[
    {
        'text': 'DataClinic è una piattaforma...',
        'source': 'dataclinic.pdf',
        'score': 0.89  # Molto rilevante!
    },
    {
        'text': 'La piattaforma offre servizi...',
        'source': 'dataclinic.pdf',
        'score': 0.76
    },
    {
        'text': 'Per maggiori informazioni...',
        'source': 'dataclinic.pdf',
        'score': 0.65
    }
]
```

---

### `upload_pdf.py` - Script Caricamento PDF con LlamaIndex (158 righe)

**Responsabilità:**
- Estrae testo da PDF
- Divide in chunk intelligenti
- Genera embeddings
- Carica tutto su Qdrant

**Struttura:**

```python
# 1. CONFIGURAZIONE (righe 1-44)
- Importa LlamaIndex
- Configurazione Qdrant e OpenAI
- CHUNK_SIZE = 1000, CHUNK_OVERLAP = 200

# 2. SETUP (righe 46-58)
def setup_vector_store():
    """Crea vector store Qdrant"""
    qdrant_client = QdrantClient(...)
    vector_store = QdrantVectorStore(...)
    return vector_store, qdrant_client

# 3. PROCESSING (righe 60-116)
def process_pdf(pdf_path):
    """Processa PDF e carica su Qdrant"""
    # Setup
    vector_store, qdrant_client = setup_vector_store()
    embed_model = OpenAIEmbedding(...)
    text_splitter = SentenceSplitter(...)
    
    # Carica PDF
    documents = SimpleDirectoryReader(input_files=[pdf_path]).load_data()
    
    # Aggiungi metadata
    for doc in documents:
        doc.metadata['source'] = pdf_name
    
    # Crea index e carica su Qdrant (automatico!)
    index = VectorStoreIndex.from_documents(
        documents,
        storage_context=StorageContext.from_defaults(vector_store=vector_store),
        embed_model=embed_model,
        transformations=[text_splitter],
        show_progress=True
    )
```

**Cosa fa LlamaIndex automaticamente:**

1. **Estrazione PDF**: `SimpleDirectoryReader` estrae testo automaticamente
2. **Chunking**: `SentenceSplitter` divide testo rispettando i confini delle frasi
3. **Embeddings**: `OpenAIEmbedding` genera embeddings in batch automaticamente
4. **Upload**: `VectorStoreIndex.from_documents()` carica tutto su Qdrant

**Prima (codice manuale):**
- ~290 righe di codice
- Gestione manuale di batch
- Chunking manuale con ricerca punteggiatura
- Upload manuale punto per punto

**Dopo (con LlamaIndex):**
- ~158 righe di codice (45% riduzione!)
- Gestione automatica di batch
- Chunking semantico intelligente
- Upload automatico ottimizzato

---

## 🧠 Concetti Chiave

### 1. RAG (Retrieval Augmented Generation)

**Il Problema:**
- LLM hanno conoscenza limitata ai dati di training
- Non conoscono informazioni specifiche della tua azienda
- Possono "allucinare" informazioni non veritiere

**La Soluzione RAG:**
1. **Retrieval**: Recupera informazioni rilevanti dal database
2. **Augmentation**: Aggiungi queste informazioni al prompt
3. **Generation**: LLM genera risposta usando contesto + conoscenza

**Esempio:**

```
Senza RAG:
Q: "Quali sono i servizi di DataClinic?"
A: "Non ho informazioni specifiche su DataClinic..." ❌

Con RAG:
Q: "Quali sono i servizi di DataClinic?"
→ Recupera: "DataClinic offre analisi dati, consulenza, formazione..."
→ Prompt: "[Contesto recuperato]\nQ: Quali sono i servizi?"
A: "DataClinic offre analisi dati, consulenza e formazione..." ✅
```

### 2. Embeddings

**Cosa sono:**
- Rappresentazioni numeriche di testo come vettori
- Testi simili semanticamente hanno vettori simili
- Permettono ricerca semantica (non solo keyword matching)

**Esempio:**

```
"Cos'è DataClinic?" 
→ [0.123, -0.456, 0.789, ..., 0.234] (1536 numeri)

"Che cosa fa DataClinic?" 
→ [0.125, -0.454, 0.791, ..., 0.236] (simile!)

"Come cucinare la pasta?"
→ [0.987, 0.123, -0.456, ..., -0.789] (diverso!)
```

**Modello usato:** `text-embedding-3-small`
- 1536 dimensioni
- Economico e veloce
- Buona qualità per ricerca semantica

### 3. Vector Database (Qdrant)

**Perché serve:**
- Cercare tra milioni di chunk velocemente
- Trovare contenuti simili semanticamente
- Non solo keyword matching ma comprensione semantica

**Come funziona:**
- Ogni chunk è un punto nello spazio 1536-dimensionale
- La ricerca trova i punti più vicini alla query
- Cosine similarity misura la "vicinanza" (0-1, più alto = più simile)

**Struttura su Qdrant:**

```json
{
  "id": 12345,
  "vector": [0.123, -0.456, ..., 0.234],  // 1536 dimensioni
  "payload": {
    "text": "DataClinic è una piattaforma...",
    "source": "dataclinic.pdf",
    "chunk_index": 5
  }
}
```

### 4. Chunking

**Perché dividere in chunk:**
- LLM hanno limiti di token (max ~8000-32000)
- Chunk piccoli = ricerca più precisa
- Chunk grandi = più contesto ma meno preciso

**Strategia usata:**
- **CHUNK_SIZE**: 1000 caratteri
- **CHUNK_OVERLAP**: 200 caratteri
- **Metodo**: `SentenceSplitter` di LlamaIndex (rispetta confini frasi)

**Esempio:**

```
Testo originale (3000 caratteri):
"DataClinic è una piattaforma innovativa per l'analisi dei dati. 
Offre servizi di consulenza e formazione. La piattaforma è..."

Chunk 1 (0-1000):
"DataClinic è una piattaforma innovativa per l'analisi dei dati. 
Offre servizi di consulenza..."

Chunk 2 (800-1800):  ← Overlap di 200 caratteri
"Offre servizi di consulenza e formazione. La piattaforma è..."

Chunk 3 (1600-2600):
"La piattaforma è progettata per..."
```

### 5. OpenAI Assistant API

**Perché usare Assistant API invece di chiamate dirette:**

✅ **Vantaggi:**
- Gestisce thread automaticamente (mantiene contesto conversazione)
- Più semplice da usare
- Supporta file attachments (futuro)
- Gestione automatica dello stato

❌ **Svantaggi:**
- Richiede polling per completamento
- Meno controllo rispetto a chiamate dirette
- Potrebbe essere più lento

**Flusso:**

```
1. Crea thread → thread_id
2. Aggiungi messaggio utente → message_id
3. Crea run → run_id
4. Polling: while status != 'completed'
5. Recupera messaggi → risposta
```

---

## 🔧 Come Modificare/Estendere

### Cambiare numero di risultati recuperati

In `main.py`, riga 180:

```python
# Prima
relevant_contexts = retrieve_relevant_context(user_input, top_k=3)

# Dopo (più contesto)
relevant_contexts = retrieve_relevant_context(user_input, top_k=5)
```

### Cambiare dimensione chunk

In `upload_pdf.py`, righe 42-44:

```python
# Prima
CHUNK_SIZE = 1000
CHUNK_OVERLAP = 200

# Dopo (chunk più grandi)
CHUNK_SIZE = 1500
CHUNK_OVERLAP = 300
```

### Usare modello embedding diverso

In `retrieve_context.py` e `upload_pdf.py`:

```python
# Prima
embed_model = OpenAIEmbedding(
    model="text-embedding-3-small",
    api_key=OPENAI_API_KEY
)

# Dopo (più costoso ma migliore qualità)
embed_model = OpenAIEmbedding(
    model="text-embedding-3-large",  # o "text-embedding-ada-002"
    api_key=OPENAI_API_KEY
)
```

### Aggiungere filtri per source

In `retrieve_context.py`, modifica `retrieve_relevant_context()`:

```python
from llama_index.core.vector_stores import MetadataFilters, ExactMatchFilter

def retrieve_relevant_context(query: str, top_k: int = 3, source: str = None):
    index = get_index()
    
    # Crea filtro se source specificato
    filters = None
    if source:
        filters = MetadataFilters(
            filters=[ExactMatchFilter(key="source", value=source)]
        )
    
    retriever = index.as_retriever(
        similarity_top_k=top_k,
        filters=filters  # Applica filtro
    )
    
    nodes = retriever.retrieve(query)
    # ... resto del codice
```

### Aggiungere più PDF

```bash
python upload_pdf.py documento1.pdf documento2.pdf documento3.pdf
```

Ogni PDF viene caricato nella stessa collection con metadata `source` diverso.

### Supportare altri formati (DOCX, TXT, MD)

Modifica `upload_pdf.py`:

```python
from llama_index.readers.file import FlatReader  # Per TXT
from llama_index.readers.docx import DocxReader  # Per DOCX

# Per TXT
documents = FlatReader().load_data(input_files=[str(txt_path)])

# Per DOCX
documents = DocxReader().load_data(input_files=[str(docx_path)])
```

---

## 📊 Flusso Dati Dettagliato

### Caricamento PDF

```
PDF File (dataclinic.pdf)
  │
  ▼
SimpleDirectoryReader (LlamaIndex)
  │
  ▼
Document objects (1 documento)
  │
  ├─► metadata: {file_path: "dataclinic.pdf"}
  │
  └─► text: "DataClinic è una piattaforma..."
  │
  ▼
SentenceSplitter (LlamaIndex)
  │
  ├─► Chunk 1: "DataClinic è una piattaforma..." (1000 char)
  ├─► Chunk 2: "...servizi di consulenza..." (1000 char, overlap 200)
  └─► Chunk 3: "...formazione e supporto..." (1000 char, overlap 200)
  │
  ▼
OpenAIEmbedding (LlamaIndex)
  │
  ├─► Chunk 1 → [0.123, -0.456, ..., 0.234] (1536 dim)
  ├─► Chunk 2 → [0.125, -0.454, ..., 0.236] (1536 dim)
  └─► Chunk 3 → [0.127, -0.452, ..., 0.238] (1536 dim)
  │
  ▼
QdrantVectorStore (LlamaIndex)
  │
  ├─► Point 1: {id: 1, vector: [...], payload: {text: "...", source: "dataclinic.pdf"}}
  ├─► Point 2: {id: 2, vector: [...], payload: {text: "...", source: "dataclinic.pdf"}}
  └─► Point 3: {id: 3, vector: [...], payload: {text: "...", source: "dataclinic.pdf"}}
  │
  ▼
Qdrant Database (Collection: dataclinic_docs)
```

### Query Utente

```
Query: "Cos'è DataClinic?"
  │
  ▼
retrieve_relevant_context(query, top_k=3)
  │
  ├─► get_index() → Carica VectorStoreIndex da Qdrant
  │
  ├─► retriever = index.as_retriever(similarity_top_k=3)
  │
  └─► nodes = retriever.retrieve(query)
      │
      ├─► Genera embedding query: [0.123, -0.456, ..., 0.234]
      │
      ├─► Qdrant similarity search
      │   │
      │   ├─► Confronta con tutti i chunk
      │   │
      │   ├─► Calcola cosine similarity
      │   │   ├─► Chunk 1: score = 0.89 ✅
      │   │   ├─► Chunk 2: score = 0.76 ✅
      │   │   ├─► Chunk 3: score = 0.65 ✅
      │   │   └─► Chunk 4: score = 0.45 ❌
      │   │
      │   └─► Restituisce top 3
      │
      └─► Formatta risultati
          │
          ├─► Result 1: {text: "...", source: "dataclinic.pdf", score: 0.89}
          ├─► Result 2: {text: "...", source: "dataclinic.pdf", score: 0.76}
          └─► Result 3: {text: "...", source: "dataclinic.pdf", score: 0.65}
  │
  ▼
format_context_for_prompt(contexts)
  │
  ▼
Stringa formattata:
"""
--- Informazioni rilevanti da DataClinic ---

[Fonte: dataclinic.pdf]
DataClinic è una piattaforma innovativa...

[Fonte: dataclinic.pdf]
Offre servizi di consulenza...

[Fonte: dataclinic.pdf]
La piattaforma è progettata per...

--- Fine informazioni ---
"""
  │
  ▼
Messaggio completo:
"""
--- Informazioni rilevanti da DataClinic ---
...
--- Fine informazioni ---

Domanda dell'utente: Cos'è DataClinic?
"""
  │
  ▼
OpenAI Assistant API
  │
  ├─► Aggiunge messaggio al thread
  │
  ├─► Crea run
  │
  ├─► Polling (status: queued → in_progress → completed)
  │
  └─► Recupera risposta
      │
      ▼
Risposta: "DataClinic è una piattaforma innovativa per l'analisi dei dati..."
```

---

## 🎯 Decisioni Architetturali

### Perché FastAPI?

✅ **Vantaggi:**
- Async/await per performance migliori
- Documentazione automatica (Swagger UI su `/docs`)
- Validazione automatica con Pydantic
- Facile da testare
- Type hints support

### Perché LlamaIndex?

✅ **Vantaggi:**
- Specializzato per RAG
- Meno codice da scrivere (65% riduzione)
- Gestione automatica di batch e errori
- Chunking semantico intelligente
- Caching automatico dell'index
- API semplice e intuitiva

### Perché Qdrant?

✅ **Vantaggi:**
- Cloud managed (no server da gestire)
- API Python semplice
- Performance ottime per ricerca vettoriale
- Free tier generoso
- Supporto per filtri avanzati (metadata filtering)

### Perché OpenAI Assistant API?

✅ **Vantaggi:**
- Gestisce thread automaticamente
- Mantiene contesto conversazione
- Più semplice di chiamate dirette a GPT
- Supporta file attachments (futuro)
- Gestione automatica dello stato

❌ **Svantaggi:**
- Richiede polling per completamento
- Meno controllo rispetto a chiamate dirette
- Potrebbe essere più lento

---

## 🚀 Come Replicare da Zero

### 1. Setup Base

```bash
# Crea progetto
mkdir my-chatbot
cd my-chatbot

# Virtual environment
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate

# Installa dipendenze
pip install fastapi uvicorn python-dotenv openai llama-index llama-index-vector-stores-qdrant llama-index-embeddings-openai qdrant-client
```

### 2. Crea struttura file

```bash
touch main.py retrieve_context.py upload_pdf.py requirements.txt .env.local
```

### 3. Configura variabili

Crea `.env.local`:

```env
OPENAI_API_KEY=sk-proj-...
ASSISTANT_ID=asst_...
QDRANT_URL=https://...
QDRANT_API_KEY=...
QDRANT_COLLECTION_NAME=dataclinic_docs
```

### 4. Implementa in ordine

1. **`upload_pdf.py`** - Carica PDF su Qdrant
2. **`retrieve_context.py`** - Recupera contesto da Qdrant
3. **`main.py`** - API FastAPI con integrazione RAG

### 5. Test locale

```bash
# Carica un PDF
python upload_pdf.py dataclinic.pdf

# Avvia server
uvicorn main:app --reload

# Testa su http://localhost:8000/docs
```

### 6. Deploy

- Push su GitHub
- Connetti Railway
- Aggiungi variabili ambiente
- Deploy automatico!

---

## 💡 Tips e Best Practices

### Performance

- ✅ **Batch processing**: LlamaIndex gestisce automaticamente batch per embeddings
- ✅ **Caching**: Index LlamaIndex viene cachato (singleton pattern)
- ✅ **Chunking intelligente**: SentenceSplitter rispetta confini frasi
- ✅ **Async/await**: FastAPI usa async per performance migliori

### Costi

- ✅ Usa `text-embedding-3-small` (più economico)
- ✅ Limita `top_k` a 3-5 (spesso sufficiente)
- ✅ Monitora usage su OpenAI dashboard
- ✅ Usa chunking appropriato (evita chunk troppo piccoli/grandi)

### Sicurezza

- ✅ Mai committare `.env.local` nel repository
- ✅ Usa variabili ambiente su Railway
- ✅ Valida input utente (Pydantic)
- ✅ Configura CORS per produzione (non `["*"]`)

### Debugging

- ✅ Logging dettagliato in ogni step
- ✅ Endpoint `/debug/env` per verificare configurazione
- ✅ Endpoint `/health` per monitoraggio
- ✅ Testa ogni componente separatamente

---

## 🔍 Domande Frequenti

**Q: Perché non uso direttamente GPT con i PDF?**
A: GPT ha limiti di token (~8000-32000). Con RAG, puoi avere migliaia di pagine e cercare solo quelle rilevanti.

**Q: Posso usare altri vector database?**
A: Sì! Pinecone, Weaviate, ChromaDB. LlamaIndex supporta molti vector store. Cambia solo `QdrantVectorStore` con quello che preferisci.

**Q: Come miglioro la qualità delle risposte?**
A: 
- Migliora chunking (dimensioni, overlap)
- Aumenta top_k (più contesto)
- Migliora prompt engineering
- Aggiungi metadata per filtri
- Usa modello embedding migliore

**Q: Posso caricare altri formati?**
A: Sì! LlamaIndex supporta DOCX, TXT, MD, HTML, etc. Usa i reader appropriati.

**Q: Come gestisco conversazioni multi-turn?**
A: OpenAI Assistant API gestisce automaticamente i thread. Ogni thread mantiene il contesto della conversazione.

---

## 📚 Risorse per Approfondire

- [LlamaIndex Documentation](https://docs.llamaindex.ai/)
- [LlamaIndex Qdrant Integration](https://docs.llamaindex.ai/en/stable/module_guides/storing/vector_stores/qdrant/)
- [OpenAI Assistant API](https://platform.openai.com/docs/assistants/overview)
- [FastAPI Tutorial](https://fastapi.tiangolo.com/tutorial/)
- [Qdrant Documentation](https://qdrant.tech/documentation/)
- [RAG Paper](https://arxiv.org/abs/2005.11401)

---

**Con questa guida hai tutto per capire, modificare e estendere il chatbot! 🚀**
