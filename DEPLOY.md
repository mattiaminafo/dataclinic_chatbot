# 🚀 Guida Deploy su Railway

## Passo 1: Aggiungi Variabili su Railway

1. Vai su [Railway Dashboard](https://railway.app)
2. Seleziona il tuo progetto (Chatbot DataClinic)
3. Vai su **Variables** (o **Settings** → **Variables**)
4. Aggiungi queste variabili:

### Variabili Obbligatorie:

```
QDRANT_URL=https://3295f9b4-ebee-474a-957d-da07a46a4a80.europe-west3-0.gcp.cloud.qdrant.io
QDRANT_API_KEY=eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJhY2Nlc3MiOiJtIn0.6hMeqzzUolOcOG5baapb2lH2trSuLoRvPbQaCiLtHkk
```

### Variabili Opzionali:

```
QDRANT_COLLECTION_NAME=dataclinic_docs
```

### Variabili già presenti (verifica che ci siano):

```
OPENAI_API_KEY=sk-proj-...
ASSISTANT_ID=asst_...
```

## Passo 2: Push su GitHub

Dopo aver aggiunto le variabili su Railway, fai push del codice:

```bash
# Aggiungi i file modificati
git add main.py requirements.txt retrieve_context.py upload_pdf.py

# Aggiungi i file di documentazione (opzionale)
git add *.md test_chatbot.py

# Commit
git commit -m "Aggiunta integrazione Qdrant per retrieval da PDF"

# Push su GitHub
git push origin main
```

## Passo 3: Railway Deploy Automatico

Railway rileverà automaticamente il push e farà il deploy:
- ✅ Installerà le nuove dipendenze (`qdrant-client`, `pypdf`, `tiktoken`)
- ✅ Avvierà il server con il nuovo codice
- ✅ Userà le variabili ambiente che hai configurato

## Passo 4: Verifica Deploy

1. Vai su Railway → Il tuo progetto → **Deployments**
2. Aspetta che il deploy sia completato (status: "Active")
3. Clicca sul dominio pubblico per testare

## ✅ Checklist Pre-Deploy

- [ ] Variabili Qdrant aggiunte su Railway
- [ ] Variabili OpenAI già presenti su Railway
- [ ] Codice committato localmente
- [ ] Push fatto su GitHub
- [ ] Deploy completato su Railway

## 🐛 Troubleshooting

### Errore: "Missing QDRANT_API_KEY"
- Verifica che le variabili siano aggiunte come **Service Variables** (non Project Variables)
- Riavvia il servizio su Railway

### Errore: "Collection not found"
- Verifica che `QDRANT_COLLECTION_NAME` sia corretto
- La collection viene creata automaticamente al primo caricamento PDF

### Il chatbot non usa Qdrant
- Controlla i log su Railway per vedere se recupera contesto
- Verifica che le variabili siano configurate correttamente

## 📝 Note

- Il PDF `dataclinic.pdf` NON viene committato su GitHub (è nel .gitignore)
- Per caricare PDF su Qdrant in produzione, usa lo script `upload_pdf.py` localmente con le credenziali corrette
- Le variabili su Railway sono sicure e non vengono esposte pubblicamente

