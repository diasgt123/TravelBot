import httpx
from app.core.config import get_settings
from typing import Dict, Any
import json

settings = get_settings()

class WhatsAppService:
    def __init__(self):
        self.base_url = "https://graph.facebook.com/v17.0"  # Using latest stable version
        self.access_token = "EAA1g6kz1BSkBOZBthEZCVTvdstBqaqHnGQtiWkXuE95XFYEylZAlE4s4eenW4XF6hHtlD3N4nHMcgFyXG4ZBij1steJOPxCZCOSf58ayC9rwS23kqpFowxQdJRZCQEHhC0OdPFGqHM7Pg3PKOgWSt6jPmVMZB6gvrTijiPB2TtSAQgZB9ss6i38j4P8sSUCZBMrTNOsKM5MbbZCREAZAdAOrp5IefyUZC61rzmVOGZBamh3LEp0zVpKYZD"
        self.phone_number_id = "264902300050961"
        self.headers = {
            "Authorization": f"Bearer {self.access_token}",
            "Content-Type": "application/json"
        }
    
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
            
            return {
                "message": messages.get("text", {}).get("body", ""),
                "from_number": messages.get("from", ""),
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