from fastapi import APIRouter, Request, UploadFile, File, HTTPException
from app.services.whatsapp_service import WhatsAppService
from app.services.rag_service import RAGService
from app.services.function_service import FunctionService
from app.core.config import get_settings
from typing import Dict, Any, Optional
import uuid
import json
import logging
import os
from fastapi.responses import PlainTextResponse

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

router = APIRouter()
settings = get_settings()

# WhatsApp webhook verify token
VERIFY_TOKEN = "123123123"

# Initialize services
whatsapp_service = WhatsAppService()
rag_service = RAGService(None)  # We'll update this when Redis is configured
function_service = FunctionService()

@router.get("/webhook/whatsapp")
async def verify_webhook(request: Request):
    params = dict(request.query_params)
    if (
        params.get("hub.mode") == "subscribe"
        and params.get("hub.verify_token") == VERIFY_TOKEN
    ):
        return PlainTextResponse(params.get("hub.challenge"))
    return PlainTextResponse("Verification token mismatch", status_code=403)

@router.post("/webhook/whatsapp")
async def whatsapp_webhook(request: Request):
    """Handle incoming WhatsApp messages"""
    try:
        # Parse incoming data
        data = await request.json()
        logger.info(f"Received webhook data: {json.dumps(data, indent=2)}")
        
        # Extract message
        message = data["entry"][0]["changes"][0]["value"]["messages"][0]
        from_number = message["from"]
        message_text = message["text"]["body"]
        
        # Generate session ID using just the phone number for consistent conversation
        session_id = from_number
        logger.info(f"Processing message with session ID: {session_id}")
        
        # Check if it's a simple greeting
        greetings = ["hi", "hello", "hey", "greetings"]
        if message_text.lower().strip() in greetings:
            response = "Hello! How can I assist you with your travel plans today?"
        else:
            # Process with RAG
            rag_response = rag_service.get_response(message_text, session_id)
            if not rag_response:
                rag_response = "I apologize, but I'm having trouble processing your request at the moment."
            
            # Only use RAG response for general queries
            response = rag_response
            
            # Only use function service for specific actions like booking
            if any(keyword in message_text.lower() for keyword in ["book", "reserve", "schedule"]):
                function_response = await function_service.process_message(message_text, session_id)
                if isinstance(function_response, dict):
                    function_response = str(function_response.get("output", ""))
                if function_response and function_response.strip():
                    response = function_response
        
        # Send response back to WhatsApp
        result = await whatsapp_service.send_message(from_number, response)
        if result["status"] == "error":
            logger.error(f"Failed to send WhatsApp message: {result['error']}")
            raise HTTPException(status_code=500, detail=f"Failed to send response: {result['error']}")
        
        logger.info(f"Response sent successfully to {from_number}")
        return {"status": "success"}
        
    except json.JSONDecodeError:
        logger.error("Invalid JSON in webhook data")
        raise HTTPException(status_code=400, detail="Invalid JSON data")
    except Exception as e:
        logger.error(f"Error processing webhook: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/upload/pdf")
async def upload_pdf(file: UploadFile = File(...)):
    """Upload a PDF file for processing"""
    try:
        # Create uploads directory if it doesn't exist
        os.makedirs("data/uploads", exist_ok=True)
        
        # Save the uploaded file
        file_path = f"data/uploads/{file.filename}"
        with open(file_path, "wb") as buffer:
            content = await file.read()
            buffer.write(content)
        
        # Process the PDF
        success = rag_service.add_document(file_path)
        if not success:
            raise HTTPException(status_code=500, detail="Failed to process PDF")
        
        return {"message": "PDF processed successfully"}
    except Exception as e:
        logger.error(f"Error processing PDF: {e}")
        raise HTTPException(status_code=500, detail=str(e)) 