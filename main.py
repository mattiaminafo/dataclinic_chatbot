import os
import logging
from time import sleep
from packaging import version
import openai
from openai import OpenAI
from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
import asyncio
from dotenv import load_dotenv

# Carica le variabili d'ambiente dal file .env o .env.local
# .env.local ha priorità se esiste (utile per override locali)
load_dotenv('.env.local')  # Prova prima .env.local
load_dotenv()  # Poi carica .env come fallback

# Configurazione del logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Controlliamo che la versione di OpenAI sia corretta
required_version = version.parse("1.1.1")
current_version = version.parse(openai.__version__)

if current_version < required_version:
    raise ValueError(
        f"Error: OpenAI version {openai.__version__} "
        f"is less than the required version 1.1.1"
    )
else:
    logger.info(f"OpenAI version {openai.__version__} is compatible.")

# Carica le variabili d'ambiente
OPENAI_API_KEY = os.getenv('OPENAI_API_KEY')
ASSISTANT_ID = os.getenv('ASSISTANT_ID')

# Validazione delle variabili d'ambiente
if not OPENAI_API_KEY:
    raise ValueError("OPENAI_API_KEY environment variable is not set")
if not ASSISTANT_ID:
    raise ValueError("ASSISTANT_ID environment variable is not set")

# Inizializziamo l'app FastAPI
app = FastAPI(
    title="Chatbot DataClinic",
    description="API per il chatbot basato su OpenAI Assistant",
    version="1.0.0"
)

# Configurazione CORS (modifica secondo le tue esigenze)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In produzione, specifica i domini consentiti
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Inizializziamo il client di OpenAI
client = OpenAI(api_key=OPENAI_API_KEY)

# Definiamo il modello di richiesta per la chat
class ChatRequest(BaseModel):
    thread_id: str = Field(..., description="ID del thread della conversazione")
    message: str = Field(..., min_length=1, description="Messaggio dell'utente")

# Modello per la risposta
class ChatResponse(BaseModel):
    response: str
    thread_id: str

# Modello per la risposta di start
class StartResponse(BaseModel):
    thread_id: str
    message: str = "Conversazione avviata con successo"

# Endpoint per inizializzare una nuova conversazione
@app.get('/start', response_model=StartResponse)
async def start_conversation():
    """Avvia una nuova conversazione creando un nuovo thread."""
    try:
        logger.info("Starting a new conversation...")
        thread = client.beta.threads.create()
        logger.info(f"New thread created with ID: {thread.id}")
        return StartResponse(
            thread_id=thread.id,
            message="Conversazione avviata con successo"
        )
    except Exception as e:
        logger.error(f"Error creating thread: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error creating thread: {str(e)}")

# Endpoint per gestire il messaggio di chat
@app.post('/chat', response_model=ChatResponse)
async def chat(chat_request: ChatRequest):
    """Gestisce un messaggio dell'utente e restituisce la risposta dell'assistente."""
    thread_id = chat_request.thread_id
    user_input = chat_request.message

    # Validazione input
    if not thread_id:
        logger.error("Error: Missing thread_id")
        raise HTTPException(status_code=400, detail="Missing thread_id")
    
    if not user_input or not user_input.strip():
        logger.error("Error: Empty message")
        raise HTTPException(status_code=400, detail="Message cannot be empty")

    logger.info(f"Received message: {user_input} for thread ID: {thread_id}")

    try:
        # Inseriamo il messaggio dell'utente nella conversazione
        client.beta.threads.messages.create(
            thread_id=thread_id,
            role="user",
            content=user_input
        )

        # Creiamo la run per l'assistente
        run = client.beta.threads.runs.create(
            thread_id=thread_id,
            assistant_id=ASSISTANT_ID
        )

        logger.info(f"Run created with ID: {run.id}")

        # Polling per controllare lo stato della run
        max_attempts = 60  # Timeout di 60 secondi
        attempt = 0
        end = False

        while not end and attempt < max_attempts:
            # Controlliamo lo stato della run
            run_status = client.beta.threads.runs.retrieve(
                thread_id=thread_id,
                run_id=run.id
            )
            
            logger.info(f"Run status: {run_status.status} (attempt {attempt + 1})")

            if run_status.status == 'completed':
                end = True
            elif run_status.status in ["cancelling", "requires_action", "cancelled", "expired", "failed"]:
                end = True
                if run_status.status == "failed":
                    error_msg = run_status.last_error.message if run_status.last_error else "Unknown error"
                    logger.error(f"Run failed: {error_msg}")
                    raise HTTPException(
                        status_code=500,
                        detail=f"Assistant run failed: {error_msg}"
                    )
                elif run_status.status == "requires_action":
                    logger.warning("Run requires action - this may need special handling")
                    raise HTTPException(
                        status_code=500,
                        detail="Assistant requires action - not implemented"
                    )

            if not end:
                await asyncio.sleep(1)
                attempt += 1

        if attempt >= max_attempts:
            logger.error("Run timeout - exceeded max attempts")
            raise HTTPException(
                status_code=504,
                detail="Request timeout - assistant took too long to respond"
            )

        # Recuperiamo i messaggi della conversazione
        messages = client.beta.threads.messages.list(thread_id=thread_id)

        # Verifichiamo che ci siano messaggi
        if not messages.data:
            logger.error("No messages found in thread")
            raise HTTPException(
                status_code=500,
                detail="No messages found in thread"
            )

        # Recuperiamo il testo della risposta
        response = messages.data[0].content[0].text.value

        logger.info(f"Assistant response generated successfully for thread {thread_id}")

        return ChatResponse(
            response=response,
            thread_id=thread_id
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error processing chat request: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Error processing request: {str(e)}"
        )

# Endpoint di health check
@app.get('/health')
async def health_check():
    """Endpoint per verificare lo stato dell'API."""
    return {
        "status": "healthy",
        "openai_version": openai.__version__,
        "assistant_id": ASSISTANT_ID
    }

# Endpoint root
@app.get('/')
async def root():
    """Endpoint root con informazioni sull'API."""
    return {
        "message": "Chatbot DataClinic API",
        "version": "1.0.0",
        "endpoints": {
            "start": "/start",
            "chat": "/chat",
            "health": "/health"
        }
    }

