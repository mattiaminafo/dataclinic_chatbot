# 🧪 Come Testare il Chatbot

## Metodo 1: Documentazione Interattiva (Più Semplice) ⭐

1. **Avvia il server:**
   ```bash
   uvicorn main:app --reload
   ```

2. **Apri il browser e vai su:**
   ```
   http://localhost:8000/docs
   ```

3. **Nella pagina che si apre:**
   - Clicca su `GET /start` → "Try it out" → "Execute"
   - Copia il `thread_id` dalla risposta
   - Clicca su `POST /chat` → "Try it out"
   - Incolla il `thread_id` nel campo `thread_id`
   - Scrivi la tua domanda nel campo `message` (es: "Cos'è DataClinic?")
   - Clicca "Execute"
   - Leggi la risposta! 🎉

## Metodo 2: Usando curl (Terminale)

1. **Avvia il server** (in un terminale):
   ```bash
   uvicorn main:app --reload
   ```

2. **In un altro terminale, avvia una conversazione:**
   ```bash
   curl http://localhost:8000/start
   ```
   
   Copia il `thread_id` dalla risposta (es: `thread_abc123`)

3. **Fai una domanda:**
   ```bash
   curl -X POST http://localhost:8000/chat \
     -H "Content-Type: application/json" \
     -d '{
       "thread_id": "thread_abc123",
       "message": "Cos'\''è DataClinic?"
     }'
   ```

## Metodo 3: Usando il Frontend React

1. **Avvia il backend** (terminale 1):
   ```bash
   uvicorn main:app --reload
   ```

2. **Avvia il frontend** (terminale 2):
   ```bash
   cd frontend
   npm run dev
   ```

3. **Apri il browser su:**
   ```
   http://localhost:3000
   ```

   Avrai un'interfaccia grafica completa per chattare!

## Metodo 4: Usando Python (Script di test)

Crea un file `test_chatbot.py`:

```python
import requests

# 1. Avvia conversazione
response = requests.get("http://localhost:8000/start")
thread_id = response.json()["thread_id"]
print(f"Thread ID: {thread_id}")

# 2. Fai una domanda
response = requests.post(
    "http://localhost:8000/chat",
    json={
        "thread_id": thread_id,
        "message": "Cos'è DataClinic?"
    }
)

print(f"Risposta: {response.json()['response']}")
```

Esegui:
```bash
python test_chatbot.py
```

## ✅ Verifica che Qdrant Funzioni

Se vuoi verificare che il chatbot stia usando le informazioni dal PDF:

1. Fai una domanda specifica che sai essere nel PDF
2. Controlla la risposta - dovrebbe contenere informazioni dal PDF
3. Se non funziona, controlla i log del server per vedere se recupera contesto da Qdrant

## 🔍 Log del Server

Quando fai una domanda, nel terminale dove gira `uvicorn` vedrai:
```
INFO - Recuperando contesto rilevante da Qdrant...
INFO - Contesto recuperato: 3 chunk rilevanti
```

Questo conferma che sta usando Qdrant!

