import os
import logging
from time import sleep
from packaging import version
import openai
from openai import OpenAI
from fastapi import FastAPI, HTTPException, Request
from fastapi import Request as FastAPIRequest
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
import asyncio
from dotenv import load_dotenv
from retrieve_context import retrieve_relevant_context, format_context_for_prompt
from security import validate_and_sanitize_input, create_safe_prompt, log_security_event, detect_injection, check_rate_limit

# Carica le variabili d'ambiente dal file .env o .env.local
# .env.local ha priorità se esiste (utile per override locali)
# Nota: Su Railway, le variabili devono essere configurate nel dashboard
load_dotenv('.env.local')  # Prova prima .env.local
load_dotenv()  # Poi carica .env come fallback

# Configurazione del logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Debug: mostra tutte le variabili d'ambiente che iniziano con OPENAI o ASSISTANT
all_env_vars = {k: v for k, v in os.environ.items() if 'OPENAI' in k.upper() or 'ASSISTANT' in k.upper()}
logger.info(f"Found environment variables matching OPENAI/ASSISTANT: {list(all_env_vars.keys())}")

# Debug: mostra TUTTE le chiavi delle variabili d'ambiente (per diagnosticare problemi Railway)
all_env_keys = sorted(os.environ.keys())
logger.info(f"Total environment variables found: {len(all_env_keys)}")
logger.info(f"Sample environment variable keys (first 20): {all_env_keys[:20]}")

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

# Debug: mostra quali variabili sono presenti (senza valori sensibili)
logger.info(f"Environment variables check:")
logger.info(f"  OPENAI_API_KEY: {'SET' if OPENAI_API_KEY else 'NOT SET'}")
logger.info(f"  ASSISTANT_ID: {'SET' if ASSISTANT_ID else 'NOT SET'}")

# Validazione delle variabili d'ambiente (non blocchiamo l'avvio, ma loggiamo un warning)
missing_vars = []
if not OPENAI_API_KEY:
    missing_vars.append("OPENAI_API_KEY")
if not ASSISTANT_ID:
    missing_vars.append("ASSISTANT_ID")

if missing_vars:
    error_msg = (
        f"WARNING: Missing required environment variables: {', '.join(missing_vars)}. "
        f"Please configure them in Railway dashboard under 'Variables' tab. "
        f"The application will start but endpoints will fail until variables are set."
    )
    logger.warning(error_msg)
    # Non blocchiamo l'avvio - permettiamo all'app di partire per permettere il debug

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

# Inizializziamo il client di OpenAI (sarà None se la chiave non è impostata)
client = OpenAI(api_key=OPENAI_API_KEY) if OPENAI_API_KEY else None

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
    # Verifica che le variabili siano configurate
    if not OPENAI_API_KEY or not ASSISTANT_ID:
        missing = []
        if not OPENAI_API_KEY:
            missing.append("OPENAI_API_KEY")
        if not ASSISTANT_ID:
            missing.append("ASSISTANT_ID")
        raise HTTPException(
            status_code=500,
            detail=f"Missing required environment variables: {', '.join(missing)}. Please configure them in Railway dashboard."
        )
    
    if not client:
        raise HTTPException(
            status_code=500,
            detail="OpenAI client not initialized. Missing OPENAI_API_KEY."
        )
    
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
async def chat(chat_request: ChatRequest, request: FastAPIRequest = None):
    """Gestisce un messaggio dell'utente e restituisce la risposta dell'assistente."""
    # Verifica che le variabili siano configurate
    if not OPENAI_API_KEY or not ASSISTANT_ID:
        missing = []
        if not OPENAI_API_KEY:
            missing.append("OPENAI_API_KEY")
        if not ASSISTANT_ID:
            missing.append("ASSISTANT_ID")
        raise HTTPException(
            status_code=500,
            detail=f"Missing required environment variables: {', '.join(missing)}. Please configure them in Railway dashboard."
        )
    
    thread_id = chat_request.thread_id
    user_input = chat_request.message

    # Validazione input base
    if not thread_id:
        logger.error("Error: Missing thread_id")
        raise HTTPException(status_code=400, detail="Missing thread_id")
    
    if not user_input or not user_input.strip():
        logger.error("Error: Empty message")
        raise HTTPException(status_code=400, detail="Message cannot be empty")

    # 🔒 SICUREZZA: Rate limiting basato su IP (se disponibile)
    if request:
        client_ip = request.client.host if request.client else None
        if client_ip:
            allowed, rate_error = check_rate_limit(f"ip_{client_ip}")
            if not allowed:
                log_security_event("RATE_LIMIT_EXCEEDED", f"IP: {client_ip}", thread_id)
                raise HTTPException(
                    status_code=429,
                    detail="Troppe richieste. Riprova più tardi."
                )
    
    # 🔒 SICUREZZA: Validazione e sanitizzazione input
    sanitized_input, security_error = validate_and_sanitize_input(user_input, thread_id)
    
    if security_error:
        log_security_event("INPUT_REJECTED", security_error, thread_id)
        raise HTTPException(
            status_code=400,
            detail="Input non valido. Per favore, riformula la tua domanda."
        )
    
    logger.info(f"Received message (sanitized): {sanitized_input[:100]}... for thread ID: {thread_id}")

    if not client:
        raise HTTPException(
            status_code=500,
            detail="OpenAI client not initialized. Missing OPENAI_API_KEY."
        )

    try:
        # Recupera contesto rilevante da Qdrant (usa input sanitizzato)
        logger.info("Recuperando contesto rilevante da Qdrant...")
        relevant_contexts = retrieve_relevant_context(sanitized_input, top_k=3)
        
        # 🔒 SICUREZZA: Crea prompt sicuro per prevenire injection
        if relevant_contexts:
            context_text = format_context_for_prompt(relevant_contexts)
            enhanced_message = create_safe_prompt(context_text, sanitized_input)
            logger.info(f"Contesto recuperato: {len(relevant_contexts)} chunk rilevanti")
        else:
            # Anche senza contesto, usa formato sicuro
            enhanced_message = create_safe_prompt("", sanitized_input)
            logger.info("Nessun contesto rilevante trovato in Qdrant")
        
        # Inseriamo il messaggio dell'utente (con contesto) nella conversazione
        client.beta.threads.messages.create(
            thread_id=thread_id,
            role="user",
            content=enhanced_message
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
        
        # 🔒 SICUREZZA: Verifica che la risposta non contenga tentativi di injection
        # (doppio controllo per sicurezza)
        if response:
            is_injection, reason = detect_injection(response)
            if is_injection:
                log_security_event("RESPONSE_INJECTION_DETECTED", reason, thread_id)
                # Non restituiamo la risposta sospetta
                response = "Mi dispiace, non posso elaborare questa richiesta. Per favore, riformula la tua domanda."

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
        "status": "healthy" if (OPENAI_API_KEY and ASSISTANT_ID) else "degraded",
        "openai_version": openai.__version__,
        "assistant_id_set": bool(ASSISTANT_ID),
        "openai_api_key_set": bool(OPENAI_API_KEY)
    }

# Endpoint di debug per diagnosticare problemi con le variabili d'ambiente
@app.get('/debug/env')
async def debug_env():
    """Endpoint di debug per verificare le variabili d'ambiente (NON ESPONE VALORI SENSIBILI)."""
    # Mostra tutte le chiavi delle variabili d'ambiente
    all_keys = sorted(os.environ.keys())
    
    # Cerca variabili che potrebbero essere correlate
    openai_related = [k for k in all_keys if 'OPENAI' in k.upper() or 'ASSISTANT' in k.upper()]
    
    # Mostra alcune variabili comuni di Railway
    railway_vars = [k for k in all_keys if 'RAILWAY' in k.upper() or 'PORT' in k.upper()]
    
    return {
        "total_env_vars": len(all_keys),
        "openai_related_vars": openai_related,
        "railway_vars": railway_vars,
        "openai_api_key_set": bool(OPENAI_API_KEY),
        "assistant_id_set": bool(ASSISTANT_ID),
        "all_env_keys": all_keys[:50],  # Prime 50 chiavi
        "note": "This endpoint shows environment variable names only, not values"
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

