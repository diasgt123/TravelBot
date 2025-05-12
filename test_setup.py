import os
import requests
from dotenv import load_dotenv
import json

# Load environment variables
load_dotenv()

def test_environment():
    """Test if all required environment variables are set"""
    required_vars = [
        "OPENAI_API_KEY",
        "WHATSAPP_ACCESS_TOKEN",
        "WHATSAPP_PHONE_NUMBER_ID",
        "REDIS_URL"
    ]
    
    missing_vars = [var for var in required_vars if not os.getenv(var)]
    if missing_vars:
        print("❌ Missing environment variables:", missing_vars)
        return False
    
    print("✅ All environment variables are set")
    return True

def test_whatsapp_api():
    """Test WhatsApp API connection"""
    access_token = os.getenv("WHATSAPP_ACCESS_TOKEN")
    phone_number_id = os.getenv("WHATSAPP_PHONE_NUMBER_ID")
    
    url = f"https://graph.facebook.com/v17.0/{phone_number_id}"
    headers = {
        "Authorization": f"Bearer {access_token}"
    }
    
    try:
        response = requests.get(url, headers=headers)
        response.raise_for_status()
        print("✅ WhatsApp API connection successful")
        return True
    except Exception as e:
        print(f"❌ WhatsApp API connection failed: {str(e)}")
        return False

def test_openai_api():
    """Test OpenAI API connection"""
    api_key = os.getenv("OPENAI_API_KEY")
    
    url = "https://api.openai.com/v1/chat/completions"
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json"
    }
    data = {
        "model": "gpt-3.5-turbo",
        "messages": [{"role": "user", "content": "Hello"}],
        "max_tokens": 5
    }
    
    try:
        response = requests.post(url, headers=headers, json=data)
        response.raise_for_status()
        print("✅ OpenAI API connection successful")
        return True
    except Exception as e:
        print(f"❌ OpenAI API connection failed: {str(e)}")
        return False

def test_redis_connection():
    """Test Redis connection"""
    redis_url = os.getenv("REDIS_URL")
    
    try:
        import redis
        r = redis.from_url(redis_url)
        r.ping()
        print("✅ Redis connection successful")
        return True
    except Exception as e:
        print(f"❌ Redis connection failed: {str(e)}")
        return False

def main():
    print("🔍 Testing AI Travel Agent Setup...\n")
    
    tests = [
        ("Environment Variables", test_environment),
        ("WhatsApp API", test_whatsapp_api),
        ("OpenAI API", test_openai_api),
        ("Redis Connection", test_redis_connection)
    ]
    
    all_passed = True
    for test_name, test_func in tests:
        print(f"\nTesting {test_name}...")
        if not test_func():
            all_passed = False
    
    print("\n" + "="*50)
    if all_passed:
        print("✅ All tests passed! You're ready to run the application.")
    else:
        print("❌ Some tests failed. Please fix the issues before running the application.")
    print("="*50)

if __name__ == "__main__":
    main() 