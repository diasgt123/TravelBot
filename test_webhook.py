import requests
import json
from dotenv import load_dotenv
import os
import logging

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Load environment variables
load_dotenv()

def test_webhook():
    """Test the WhatsApp webhook endpoint"""
    # Your local server URL
    webhook_url = "http://localhost:8000/api/webhook/whatsapp"
    
    # Sample webhook payload from WhatsApp Business API
    payload = {
        "object": "whatsapp_business_account",
        "entry": [{
            "id": "123456789",
            "changes": [{
                "value": {
                    "messaging_product": "whatsapp",
                    "metadata": {
                        "display_phone_number": "1234567890",
                        "phone_number_id": os.getenv("WHATSAPP_PHONE_NUMBER_ID")
                    },
                    "messages": [{
                        "from": "1234567890",
                        "id": "wamid.123456789",
                        "timestamp": "1234567890",
                        "text": {
                            "body": "What are the visa requirements for Japan?"
                        },
                        "type": "text"
                    }]
                },
                "field": "messages"
            }]
        }]
    }
    
    headers = {
        "Content-Type": "application/json",
        "X-Hub-Signature-256": "test_signature"  # In production, this would be a real signature
    }
    
    try:
        logger.info("Sending test webhook request...")
        logger.info(f"Payload: {json.dumps(payload, indent=2)}")
        
        response = requests.post(webhook_url, json=payload, headers=headers)
        
        logger.info(f"Response status code: {response.status_code}")
        logger.info(f"Response body: {response.text}")
        
        response.raise_for_status()
        print("✅ Webhook test successful!")
        return True
    except requests.exceptions.RequestException as e:
        print(f"❌ Webhook test failed: {str(e)}")
        if hasattr(e.response, 'text'):
            print(f"Error details: {e.response.text}")
        return False
    except Exception as e:
        print(f"❌ Unexpected error: {str(e)}")
        return False

if __name__ == "__main__":
    print("🔍 Testing WhatsApp Webhook...\n")
    test_webhook() 