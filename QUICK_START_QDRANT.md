# 🚀 Quick Start: Qdrant + PDF

## Setup Rapido (3 minuti)

### 1. Installa dipendenze
```bash
pip install -r requirements.txt
```

### 2. Configura `.env.local`
```env
QDRANT_URL=https://your-qdrant-cluster-url.qdrant.io
QDRANT_API_KEY=your-qdrant-api-key-here
QDRANT_COLLECTION_NAME=dataclinic_docs
OPENAI_API_KEY=sk-proj-your-api-key-here
ASSISTANT_ID=asst_your-assistant-id-here
```

### 3. Carica un PDF
```bash
python upload_pdf.py tuo_file.pdf
```

### 4. Testa il chatbot
Il chatbot ora userà automaticamente le informazioni dai PDF quando risponde!

## ✅ Verifica Funzionamento

Dopo aver caricato un PDF, fai una domanda al chatbot che riguarda il contenuto del PDF. Il chatbot dovrebbe rispondere usando le informazioni dal PDF.

## 📝 Per Railway

Aggiungi queste variabili su Railway:
- `QDRANT_URL`
- `QDRANT_API_KEY`
- `QDRANT_COLLECTION_NAME` (opzionale)

Poi fai redeploy!

