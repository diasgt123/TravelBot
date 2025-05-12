# AI Travel Agent

An intelligent travel assistant that combines RAG capabilities with function calling to provide comprehensive travel support via WhatsApp.

## Features

- 🤖 RAG-powered Q&A about travel policies and requirements
- 🎯 Function calling for booking and itinerary management
- 💬 WhatsApp integration for easy communication
- 📚 PDF document processing and understanding
- 🔄 Conversation memory for context-aware responses

## Setup

1. Clone the repository
2. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```
3. Set up environment variables in `.env`:
   ```
   OPENAI_API_KEY=your_openai_key
   TWILIO_ACCOUNT_SID=your_twilio_sid
   TWILIO_AUTH_TOKEN=your_twilio_token
   REDIS_URL=your_redis_url
   ```

## Project Structure

```
ai_travel_agent/
├── app/
│   ├── api/            # FastAPI routes
│   ├── core/           # Core functionality
│   ├── models/         # Data models
│   ├── services/       # Business logic
│   └── utils/          # Utility functions
├── data/               # PDF documents and data
├── tests/              # Test files
└── main.py            # Application entry point
```

## Running the Application

1. Start the FastAPI server:
   ```bash
   uvicorn main:app --reload
   ```

2. The WhatsApp webhook will be available at `/webhook/whatsapp`

## API Documentation

Once the server is running, visit `/docs` for the Swagger UI documentation.

## Contributing

1. Fork the repository
2. Create a feature branch
3. Commit your changes
4. Push to the branch
5. Create a Pull Request 