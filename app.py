# app.py
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from typing import Optional, Dict, Any
import importlib
from logger_config import logger

# Initialize FastAPI
app = FastAPI(title="Voice Bot API", version="1.0")

#Input Schema
class BotRequest(BaseModel):
    transcript: str
    metadata: Optional[Dict[str, Any]] = None


try:
    main_bot = importlib.import_module("main_bot")
except Exception as e:
    main_bot = None
    logger.info(f"[error] Could not import main_bot: {e}")

def format_error(error_type: str, details: str, status_code: int = 500):
    return {
        "intent": "UNKNOWN",
        "error": {
            "type": error_type,
            "details": details
        }
    }, status_code


@app.post("/bot/handle")
def handle_bot(req: BotRequest):
    """
    POST endpoint to handle user transcript and return model output.
    """

    logger.info(f"[API] /bot/handle called by user_id={(req.metadata or {}).get('user_id', 'unknown')}")  
    
    if not req.transcript or not isinstance(req.transcript, str):
        error, code = format_error(
            "VALIDATION_ERROR",
            "Invalid input format. Expected {'transcript': <string>, 'metadata': {'user_id': 'optional'}}.",
            400
        )
        raise HTTPException(status_code=code, detail=error)

    if main_bot is None or not hasattr(main_bot, "process_request"):
        error, code = format_error(
            "PARSING_ERROR",
            "main_bot.process_request() missing or not importable. Verify main_bot.py exists.",
            500
        )
        raise HTTPException(status_code=code, detail=error)


    #Prepare payload
    payload = {"transcript": req.transcript, "metadata": req.metadata or {}}
    try:
        result = main_bot.process_request(payload)
    except Exception as e:
        error, code = format_error("CRM_ERROR", f"Error running model pipeline: {str(e)}", 500)
        raise HTTPException(status_code=code, detail=error)


    #Run model pipeline
    try:
        result = main_bot.process_request(payload)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error running model: {e}")

    #Return model output
    if not isinstance(result, dict):
        error, code = format_error("PARSING_ERROR", "Model returned invalid output format (expected dict).", 500)
        raise HTTPException(status_code=code, detail=error)
    
    return result