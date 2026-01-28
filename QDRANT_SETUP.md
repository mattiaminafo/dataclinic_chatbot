# Guida Setup Qdrant + PDF per Chatbot

Questa guida spiega come caricare PDF su Qdrant e far sì che il chatbot risponda usando le informazioni contenute nei PDF.

## 📋 Prerequisiti

1. Cluster Qdrant creato (hai già le credenziali)
2. OpenAI API Key configurata
3. Python 3.8+ installato

## 🔧 Setup

### 1. Installa le dipendenze

```bash
pip install -r requirements.txt
```

### 2. Configura le variabili d'ambiente

Aggiungi al file `.env.local`:

```env
# Qdrant Configuration
QDRANT_URL=https://3295f9b4-ebee-474a-957d-da07a46a4a80.europe-west3-0.gcp.cloud.qdrant.io
QDRANT_API_KEY=eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJhY2Nlc3MiOiJtIn0.6hMeqzzUolOcOG5baapb2lH2trSuLoRvPbQaCiLtHkk
QDRANT_COLLECTION_NAME=dataclinic_docs

# OpenAI (già configurato)
OPENAI_API_KEY=sk-proj-...
ASSISTANT_ID=asst_...
```

**⚠️ IMPORTANTE per Railway:**

Aggiungi anche queste variabili nel dashboard Railway:
- `QDRANT_URL`
- `QDRANT_API_KEY`
- `QDRANT_COLLECTION_NAME` (opzionale, default: `dataclinic_docs`)

## 📄 Caricare PDF su Qdrant

### Metodo 1: Singolo PDF

```bash
python upload_pdf.py documenti/dataclinic.pdf
```

### Metodo 2: Più PDF

```bash
python upload_pdf.py documenti/dataclinic.pdf documenti/info.pdf documenti/altro.pdf
```

### Cosa fa lo script:

1. ✅ Estrae il testo da ogni PDF
2. ✅ Divide il testo in chunk (pezzi) di ~1000 caratteri
3. ✅ Genera embeddings usando OpenAI
4. ✅ Carica tutto su Qdrant

## 🤖 Come Funziona il Chatbot

Quando un utente fa una domanda:

1. **Recupero Contesto**: Il chatbot cerca in Qdrant i 3 chunk più rilevanti
2. **Aggiunta Contesto**: Aggiunge questi chunk al messaggio dell'utente
3. **Risposta**: L'assistente OpenAI risponde usando sia il contesto che la sua conoscenza

### Esempio:

**Utente chiede:** "Cos'è DataClinic?"

**Il chatbot:**
1. Cerca in Qdrant chunk che parlano di "DataClinic"
2. Trova informazioni rilevanti dai PDF caricati
3. Invia all'assistente: `[Contesto dai PDF] Domanda: Cos'è DataClinic?`
4. L'assistente risponde usando le informazioni dai PDF

## 🔍 Verificare i Dati Caricati

Puoi verificare che i PDF siano stati caricati correttamente:

```python
from qdrant_client import QdrantClient

client = QdrantClient(
    url="https://3295f9b4-ebee-474a-957d-da07a46a4a80.europe-west3-0.gcp.cloud.qdrant.io",
    api_key="eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJhY2Nlc3MiOiJtIn0.6hMeqzzUolOcOG5baapb2lH2trSuLoRvPbQaCiLtHkk",
)

# Conta i punti nella collection
info = client.get_collection("dataclinic_docs")
print(f"Punti caricati: {info.points_count}")
```

## 🚀 Deploy su Railway

1. **Push su GitHub** (se non già fatto)
2. **Aggiungi variabili su Railway:**
   - Vai su Railway → Il tuo progetto → Variables
   - Aggiungi:
     - `QDRANT_URL`
     - `QDRANT_API_KEY`
     - `QDRANT_COLLECTION_NAME` (opzionale)
3. **Redeploy** - Railway installerà automaticamente le nuove dipendenze

## 📝 Note Importanti

- **Costi OpenAI**: Ogni caricamento PDF genera embeddings (costo minimo)
- **Costi Qdrant**: Dipende dal piano del tuo cluster
- **Chunk Size**: Modificabile in `upload_pdf.py` (default: 1000 caratteri)
- **Top K**: Numero di chunk recuperati per query (default: 3, modificabile in `main.py`)

## 🐛 Troubleshooting

### Errore: "Collection not found"
- Lo script crea automaticamente la collection se non esiste
- Verifica che `QDRANT_COLLECTION_NAME` sia corretto

### Errore: "No relevant context found"
- Verifica che i PDF siano stati caricati correttamente
- Controlla i log durante il caricamento

### Il chatbot non usa le informazioni dai PDF
- Verifica che le variabili Qdrant siano configurate su Railway
- Controlla i log del chatbot per vedere se recupera contesto

## 📚 File Utili

- `upload_pdf.py` - Script per caricare PDF
- `retrieve_context.py` - Modulo per recuperare contesto
- `main.py` - API principale (modificata per usare Qdrant)

