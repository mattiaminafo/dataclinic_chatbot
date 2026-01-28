# 🚀 Deploy Rapido su Railway

Guida passo-passo per pubblicare il chatbot su Railway in 5 minuti.

---

## ✅ Prerequisiti Completati

- ✅ Codice pubblicato su GitHub: `mattiaminafo/dataclinic_chatbot`
- ✅ Protezioni di sicurezza implementate
- ✅ File `railway.json` configurato
- ✅ Tutte le dipendenze in `requirements.txt`

---

## 🚀 Deploy su Railway (5 minuti)

### Passo 1: Crea Progetto Railway

1. Vai su **[railway.app](https://railway.app)** e accedi (puoi usare GitHub)
2. Clicca **"New Project"**
3. Seleziona **"Deploy from GitHub repo"**
4. Autorizza Railway ad accedere ai tuoi repository GitHub
5. Seleziona il repository **`dataclinic_chatbot`**
6. Railway inizierà automaticamente il deploy

### Passo 2: Configura Variabili d'Ambiente

⚠️ **CRUCIALE**: Devi configurare queste variabili prima che il chatbot funzioni!

Nel dashboard Railway del tuo progetto:

1. Vai alla scheda **"Variables"** (o **"Settings"** → **"Variables"**)
2. Clicca **"New Variable"** e aggiungi una per una:

#### Variabili Obbligatorie:

```
OPENAI_API_KEY=sk-proj-tua-api-key-qui
ASSISTANT_ID=asst-tuo-assistant-id-qui
QDRANT_URL=https://3295f9b4-ebee-474a-957d-da07a46a4a80.europe-west3-0.gcp.cloud.qdrant.io
QDRANT_API_KEY=eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJhY2Nlc3MiOiJtIn0.6hMeqzzUolOcOG5baapb2lH2trSuLoRvPbQaCiLtHkk
```

#### Variabile Opzionale:

```
QDRANT_COLLECTION_NAME=dataclinic_docs
```

3. Dopo ogni variabile aggiunta, Railway riavvierà automaticamente il servizio

### Passo 3: Verifica Deploy

1. Vai alla scheda **"Deployments"**
2. Attendi che lo status diventi **"SUCCESS"** (verde)
3. Se ci sono errori, clicca sul deployment → **"View Logs"** per vedere i dettagli

### Passo 4: Ottieni URL Pubblico

1. Vai su **"Settings"** → **"Networking"**
2. Railway assegnerà automaticamente un URL tipo:
   ```
   https://tuo-progetto.up.railway.app
   ```
3. Puoi anche generare un dominio personalizzato cliccando **"Generate Domain"**

### Passo 5: Testa il Chatbot

```bash
# Health check
curl https://tuo-progetto.up.railway.app/health

# Avvia conversazione
curl https://tuo-progetto.up.railway.app/start

# Invia messaggio (sostituisci THREAD_ID)
curl -X POST https://tuo-progetto.up.railway.app/chat \
  -H "Content-Type: application/json" \
  -d '{"thread_id": "THREAD_ID", "message": "Cos'\''è DataClinic?"}'
```

Oppure usa l'interfaccia Swagger:
```
https://tuo-progetto.up.railway.app/docs
```

---

## 🔍 Troubleshooting

### Deploy Fallisce

**Controlla i log:**
1. Vai su **Deployments** → clicca sul deployment fallito → **View Logs**
2. Cerca errori comuni:
   - `ModuleNotFoundError` → Verifica `requirements.txt`
   - `OPENAI_API_KEY not set` → Aggiungi variabile d'ambiente
   - `Port already in use` → Railway gestisce automaticamente, non dovrebbe succedere

### Il Servizio Si Avvia Ma Restituisce Errori 500

1. **Controlla i log** per vedere l'errore specifico
2. **Verifica variabili d'ambiente:**
   - Tutte le variabili obbligatorie sono configurate?
   - I valori sono corretti (no spazi extra)?
3. **Testa health endpoint:**
   ```bash
   curl https://tuo-progetto.up.railway.app/health
   ```

### Rate Limiting Troppo Restrittivo

Se ricevi errori 429 (Too Many Requests), modifica in `security.py`:
```python
MAX_REQUESTS_PER_MINUTE = 20  # Aumenta da 10
MAX_REQUESTS_PER_HOUR = 200   # Aumenta da 100
```

Poi fai commit e push:
```bash
git add security.py
git commit -m "Increase rate limits"
git push origin main
```

Railway farà automaticamente un nuovo deploy.

---

## 📊 Monitoraggio

### Logs in Tempo Reale

1. Vai su **Deployments** → clicca sul deployment attivo
2. Clicca **"View Logs"**
3. Vedi tutti i log in tempo reale

### Eventi di Sicurezza

Cerca nei log eventi di sicurezza:
```
SECURITY EVENT [INPUT_REJECTED] | ...
SECURITY EVENT [RATE_LIMIT_EXCEEDED] | ...
```

### Metriche

Railway mostra automaticamente:
- CPU usage
- Memory usage
- Network traffic
- Request count

---

## 🔄 Aggiornamenti Futuri

Ogni volta che fai `git push` su GitHub, Railway:
1. Rileva automaticamente le modifiche
2. Fa un nuovo build
3. Deploy automatico
4. Riavvia il servizio

**Nessuna azione manuale necessaria!**

---

## ✅ Checklist Deploy

- [ ] Account Railway creato
- [ ] Progetto Railway creato e connesso a GitHub
- [ ] Deploy completato con successo
- [ ] Variabili d'ambiente configurate:
  - [ ] OPENAI_API_KEY
  - [ ] ASSISTANT_ID
  - [ ] QDRANT_URL
  - [ ] QDRANT_API_KEY
- [ ] Health check passa (`/health`)
- [ ] Chatbot funziona (`/start` e `/chat`)
- [ ] URL pubblico funzionante

---

## 🎉 Fatto!

Il tuo chatbot è ora live su Railway! 🚀

**URL pubblico:** `https://tuo-progetto.up.railway.app`

Per domande o problemi, consulta:
- `RAILWAY_DEPLOY.md` - Guida dettagliata
- `GUIDA_SICUREZZA.md` - Protezioni implementate
- Logs Railway per debugging

