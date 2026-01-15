# Chatbot DataClinic

Un chatbot basato su OpenAI Assistant API costruito con FastAPI.

## Caratteristiche

- API RESTful per gestire conversazioni con OpenAI Assistant
- Gestione asincrona delle richieste
- Logging completo delle operazioni
- Gestione errori robusta
- Supporto per CORS
- Health check endpoint
- Timeout configurabile per le richieste

## Setup

### Prerequisiti

- Python 3.8 o superiore
- Account OpenAI con API key
- Assistant ID configurato su OpenAI

### Installazione

1. Clona il repository o scarica i file

2. Installa le dipendenze:
```bash
pip install -r requirements.txt
```

3. Configura le variabili d'ambiente:
   - Copia `.env.example` in `.env`
   - Inserisci la tua API key di OpenAI e l'Assistant ID

```bash
cp .env.example .env
# Modifica .env con le tue credenziali
```

### Variabili d'Ambiente

- `OPENAI_API_KEY`: La tua API key di OpenAI
- `ASSISTANT_ID`: L'ID dell'assistente OpenAI che vuoi utilizzare

## Utilizzo

### Avvio del server locale

```bash
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

Il server sarà disponibile su `http://localhost:8000`

### API Endpoints

#### 1. Avvia una nuova conversazione
```bash
GET /start
```

Risposta:
```json
{
  "thread_id": "thread_abc123",
  "message": "Conversazione avviata con successo"
}
```

#### 2. Invia un messaggio
```bash
POST /chat
Content-Type: application/json

{
  "thread_id": "thread_abc123",
  "message": "Ciao, come stai?"
}
```

Risposta:
```json
{
  "response": "Ciao! Sto bene, grazie per aver chiesto...",
  "thread_id": "thread_abc123"
}
```

#### 3. Health Check
```bash
GET /health
```

#### 4. Root
```bash
GET /
```

### Esempio di utilizzo con curl

```bash
# Avvia una conversazione
THREAD_ID=$(curl -s http://localhost:8000/start | jq -r '.thread_id')

# Invia un messaggio
curl -X POST http://localhost:8000/chat \
  -H "Content-Type: application/json" \
  -d "{\"thread_id\": \"$THREAD_ID\", \"message\": \"Ciao!\"}"
```

### Esempio con Python

```python
import requests

BASE_URL = "http://localhost:8000"

# Avvia una conversazione
response = requests.get(f"{BASE_URL}/start")
thread_id = response.json()["thread_id"]

# Invia un messaggio
response = requests.post(
    f"{BASE_URL}/chat",
    json={
        "thread_id": thread_id,
        "message": "Ciao, come posso aiutarti?"
    }
)

print(response.json()["response"])
```

## Deployment su Railway

1. Assicurati che il file `railway.json` sia presente
2. Configura le variabili d'ambiente su Railway:
   - `OPENAI_API_KEY`
   - `ASSISTANT_ID`
3. Railway utilizzerà automaticamente il comando di start definito in `railway.json`

## Struttura del Progetto

```
Chatbot_dataclinic/
├── main.py              # File principale dell'API
├── requirements.txt     # Dipendenze Python
├── railway.json        # Configurazione Railway
├── .env                # Variabili d'ambiente (non committare!)
├── .env.example        # Template per variabili d'ambiente
└── README.md           # Questo file
```

## Note di Sicurezza

⚠️ **IMPORTANTE**: 
- Non committare mai il file `.env` nel repository
- Il file `.env` è già incluso nel progetto con le tue credenziali per comodità, ma in produzione dovresti usare variabili d'ambiente del sistema o un gestore di segreti
- In produzione, configura `allow_origins` in CORS con i domini specifici invece di `["*"]`

## Troubleshooting

### Errore: "OpenAI version is less than required"
- Assicurati di avere `openai>=1.3.3` installato: `pip install --upgrade openai`

### Errore: "Missing thread_id"
- Assicurati di chiamare `/start` prima di `/chat` per ottenere un `thread_id`

### Timeout delle richieste
- Il timeout è impostato a 60 secondi. Se necessario, modifica `max_attempts` in `main.py`

## Licenza

Questo progetto è fornito così com'è per uso interno.

