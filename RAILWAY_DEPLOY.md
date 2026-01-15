# Guida al Deployment su Railway.com

Questa guida ti aiuterà a pubblicare il chatbot su Railway.com.

## Prerequisiti

1. Account su [Railway.com](https://railway.app) (puoi registrarti con GitHub)
2. Repository Git (GitHub, GitLab, o Bitbucket) con il codice del chatbot

## Passo 1: Prepara il Repository Git

Assicurati che il tuo codice sia su GitHub/GitLab/Bitbucket:

```bash
# Se non hai ancora inizializzato git
git init
git add .
git commit -m "Initial commit - Chatbot DataClinic"

# Aggiungi il tuo repository remoto
git remote add origin <URL_DEL_TUO_REPOSITORY>
git push -u origin main
```

⚠️ **IMPORTANTE**: Assicurati che `.env.local` sia nel `.gitignore` (già incluso) e NON committare mai le tue credenziali!

## Passo 2: Crea un Nuovo Progetto su Railway

1. Vai su [railway.app](https://railway.app) e accedi
2. Clicca su **"New Project"**
3. Seleziona **"Deploy from GitHub repo"** (o GitLab/Bitbucket)
4. Autorizza Railway ad accedere al tuo repository
5. Seleziona il repository `Chatbot_dataclinic`
6. Railway inizierà automaticamente il deployment

## Passo 3: Configura le Variabili d'Ambiente

⚠️ **CRUCIALE**: Devi configurare le variabili d'ambiente su Railway!

1. Nel dashboard del tuo progetto Railway, vai alla scheda **"Variables"**
2. Aggiungi le seguenti variabili d'ambiente:

   ```
   OPENAI_API_KEY=sk-proj-your-api-key-here
   ASSISTANT_ID=asst_your-assistant-id-here
   ```
   
   ⚠️ **Sostituisci con le tue credenziali reali!**

3. Railway riavvierà automaticamente il servizio dopo aver aggiunto le variabili

## Passo 4: Verifica il Deployment

1. Railway assegnerà automaticamente un URL pubblico al tuo servizio
2. Puoi trovarlo nella scheda **"Settings"** → **"Networking"**
3. Testa il tuo chatbot visitando:
   - `https://tuo-progetto.up.railway.app/` - Root endpoint
   - `https://tuo-progetto.up.railway.app/health` - Health check
   - `https://tuo-progetto.up.railway.app/docs` - Documentazione Swagger

## Passo 5: Testa il Chatbot

```bash
# Avvia una conversazione
curl https://tuo-progetto.up.railway.app/start

# Invia un messaggio (sostituisci THREAD_ID)
curl -X POST https://tuo-progetto.up.railway.app/chat \
  -H "Content-Type: application/json" \
  -d '{"thread_id": "THREAD_ID", "message": "Ciao!"}'
```

## Configurazione Avanzata

### Dominio Personalizzato (Opzionale)

1. Vai su **Settings** → **Networking**
2. Clicca su **"Generate Domain"** per un dominio Railway gratuito
3. Oppure aggiungi il tuo dominio personalizzato

### Monitoraggio e Logs

- I log sono disponibili nella scheda **"Deployments"** → clicca su un deployment → **"View Logs"**
- Railway mostra automaticamente metriche di CPU, memoria e traffico

### Restart Manuale

Se necessario, puoi riavviare il servizio dalla scheda **"Deployments"**

## Troubleshooting

### Il deployment fallisce

1. **Controlla i log**: Vai su Deployments → View Logs
2. **Verifica le variabili d'ambiente**: Assicurati che `OPENAI_API_KEY` e `ASSISTANT_ID` siano impostate
3. **Verifica requirements.txt**: Assicurati che tutte le dipendenze siano specificate

### Errore: "OPENAI_API_KEY environment variable is not set"

- Vai su Variables e aggiungi `OPENAI_API_KEY`
- Assicurati che il nome sia esatto (case-sensitive)
- Riavvia il servizio dopo aver aggiunto le variabili

### Il servizio si avvia ma restituisce errori 500

- Controlla i log per vedere l'errore specifico
- Verifica che l'Assistant ID sia corretto
- Assicurati che la tua API key di OpenAI sia valida

### Porta non disponibile

- Railway imposta automaticamente la variabile `$PORT`
- Il comando nel `railway.json` usa già `$PORT`, quindi dovrebbe funzionare automaticamente

## Costi

Railway offre:
- **$5 di credito gratuito** al mese
- Pay-as-you-go dopo il credito gratuito
- Il chatbot FastAPI dovrebbe consumare poco, quindi probabilmente rientrerà nel tier gratuito

## Aggiornamenti Futuri

Ogni volta che fai `git push` al tuo repository, Railway rileverà automaticamente le modifiche e farà un nuovo deployment.

---

**Nota**: Il file `railway.json` è già configurato correttamente e Railway lo userà automaticamente per il deployment.

