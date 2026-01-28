# 🚀 Quick Start: Qdrant + PDF

## Setup Rapido (3 minuti)

### 1. Installa dipendenze
```bash
pip install -r requirements.txt
```

### 2. Configura `.env.local`
```env
QDRANT_URL=https://3295f9b4-ebee-474a-957d-da07a46a4a80.europe-west3-0.gcp.cloud.qdrant.io
QDRANT_API_KEY=eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJhY2Nlc3MiOiJtIn0.6hMeqzzUolOcOG5baapb2lH2trSuLoRvPbQaCiLtHkk
QDRANT_COLLECTION_NAME=dataclinic_docs
OPENAI_API_KEY=sk-proj-...
ASSISTANT_ID=asst_...
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

