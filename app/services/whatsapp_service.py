import httpx
from app.core.config import get_settings
from typing import Dict, Any
import json
import logging
import redis

settings = get_settings()
logger = logging.getLogger(__name__)

class WhatsAppService:
    def __init__(self):
        self.base_url = "https://graph.facebook.com/v17.0"  # Using latest stable version
        self.access_token = settings.WHATSAPP_ACCESS_TOKEN
        self.phone_number_id = settings.WHATSAPP_PHONE_NUMBER_ID
        self.headers = {
            "Authorization": f"Bearer {self.access_token}",
            "Content-Type": "application/json"
        }
        
        # Initialize Redis client
        self.redis_client = redis.from_url(settings.REDIS_URL)
        
        # Welcome messages
        self.welcome_message = """Hi! 👋 Welcome to Reindeer Holidays 🦌

Thanks for reaching out!
We create personalized travel packages to make your trips unforgettable 🌍✈️
Let us know your destination, travel dates, and interests — and we'll get started with the perfect plan for you!

Looking forward to planning your next adventure! 😊"""

        self.welcome_back_message = """Welcome back! 👋 

How can I help you with your travel plans today? 🌍"""
    
    def _is_first_message(self, from_number: str) -> bool:
        """Check if this is the user's first message using Redis"""
        try:
            # Check if session exists in Redis
            session_key = f"whatsapp:session:{from_number}"
            session_data = self.redis_client.get(session_key)
            
            if not session_data:
                # First time user, create session
                self.redis_client.set(session_key, json.dumps({
                    "message_count": 1,
                    "last_message": None
                }))
                return True
            else:
                # Update message count
                data = json.loads(session_data)
                data["message_count"] += 1
                self.redis_client.set(session_key, json.dumps(data))
                return False
                
        except Exception as e:
            logger.error(f"Error checking session: {e}")
            return True  # On error, treat as first message
    
    def _get_welcome_message(self, from_number: str) -> str:
        """Get appropriate welcome message based on session"""
        if self._is_first_message(from_number):
            return self.welcome_message
        return self.welcome_back_message
    
    async def send_message(self, to_number: str, message: str) -> Dict[str, Any]:
        """Send a WhatsApp message using the WhatsApp Business API"""
        try:
            url = f"{self.base_url}/{self.phone_number_id}/messages"
            
            payload = {
                "messaging_product": "whatsapp",
                "to": to_number,
                "type": "text",
                "text": {
                    "body": message
                }
            }
            
            async with httpx.AsyncClient() as client:
                response = await client.post(url, headers=self.headers, json=payload)
                response.raise_for_status()
                
                return {
                    "status": "success",
                    "message_id": response.json().get("messages", [{}])[0].get("id")
                }
        except Exception as e:
            logger.error(f"Error sending WhatsApp message: {str(e)}")
            return {
                "status": "error",
                "error": str(e)
            }
    
    def parse_webhook(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Parse incoming webhook data from WhatsApp Business API"""
        try:
            # Extract the message details from the webhook
            entry = data.get("entry", [{}])[0]
            changes = entry.get("changes", [{}])[0]
            value = changes.get("value", {})
            messages = value.get("messages", [{}])[0]
            
            from_number = messages.get("from", "")
            message_text = messages.get("text", {}).get("body", "")
            
            # Check if it's a greeting
            if message_text.lower() in ["hi", "hello", "hey", "greetings", "start"]:
                message_text = self._get_welcome_message(from_number)
            
            return {
                "message": message_text,
                "from_number": from_number,
                "timestamp": messages.get("timestamp", ""),
                "message_id": messages.get("id", "")
            }
        except Exception as e:
            return {
                "error": str(e)
            }
    
    def verify_webhook(self, signature: str, url: str, params: Dict[str, Any]) -> bool:
        """Verify the webhook signature from WhatsApp Business API"""
        try:
            # Here you would implement WhatsApp's webhook signature verification
            # For now, we'll return True for development
            return True
        except Exception:
            return False