from langchain_openai import OpenAIEmbeddings
from langchain_community.vectorstores import FAISS
from langchain_community.document_loaders import PyPDFLoader
from langchain_community.chat_message_histories import RedisChatMessageHistory
from langchain_openai import ChatOpenAI
from langchain.memory import ConversationBufferMemory
from langchain.chains import ConversationalRetrievalChain
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain.prompts import PromptTemplate
import os
import logging
from typing import Dict
import re
import json

logger = logging.getLogger(__name__)

class RAGService:
    def __init__(self, redis_client):
        self.embeddings = OpenAIEmbeddings(
            model="text-embedding-3-small",
            openai_api_key=os.getenv("OPENAI_API_KEY")
        )
        self.redis_client = redis_client
        self.vector_store = self.initialize_vector_store()
        # Dictionary to store conversation memories
        self.conversation_memories: Dict[str, ConversationBufferMemory] = {}
        
        # Base URL for Reindeer Holidays
        self.base_url = "https://www.reindeerholidays.com/destination"
        
        # Welcome messages
        self.welcome_message = """Hi! 👋 Welcome to Reindeer Holidays 🦌

Thanks for reaching out!
We create personalized travel packages to make your trips unforgettable 🌍✈️
Let us know your destination, travel dates, and interests — and we'll get started with the perfect plan for you!

Looking forward to planning your next adventure! 😊"""

        self.welcome_back_message = """Welcome back! 👋 

How can I help you with your travel plans today? 🌍"""
        
    def initialize_vector_store(self):
        """Initialize or load the FAISS vector store"""
        vector_store_path = "data/vector_store"
        os.makedirs(vector_store_path, exist_ok=True)
        
        try:
            # Try to load existing vector store
            return FAISS.load_local(
                vector_store_path,
                self.embeddings,
                allow_dangerous_deserialization=True
            )
        except Exception as e:
            logger.info(f"No existing vector store found or error loading: {e}")
            # Create new vector store with welcome message
            return FAISS.from_texts(
                [self.welcome_message],
                self.embeddings
            )
    
    def add_document(self, file_path: str):
        """Add a new document to the vector store"""
        try:
            loader = PyPDFLoader(file_path)
            documents = loader.load()
            
            # Split documents into chunks
            text_splitter = RecursiveCharacterTextSplitter(
                chunk_size=1000,
                chunk_overlap=200
            )
            chunks = text_splitter.split_documents(documents)
            
            # Add to vector store
            self.vector_store.add_documents(chunks)
            
            # Save vector store
            self.vector_store.save_local("data/vector_store")
            return True
        except Exception as e:
            logger.error(f"Error adding document: {e}")
            return False
    
    def get_memory(self, session_id: str) -> ConversationBufferMemory:
        """Get or create memory for a session"""
        if session_id not in self.conversation_memories:
            self.conversation_memories[session_id] = ConversationBufferMemory(
                memory_key="chat_history",
                return_messages=True
            )
        return self.conversation_memories[session_id]
    
    def _is_booking_request(self, query: str) -> tuple[bool, str]:
        """Check if the query is a booking request and extract destination"""
        # Common booking-related phrases
        booking_phrases = [
            r"book.*trip.*to\s+(\w+)",
            r"book.*holiday.*to\s+(\w+)",
            r"book.*vacation.*to\s+(\w+)",
            r"book.*package.*to\s+(\w+)",
            r"want.*to.*book.*to\s+(\w+)",
            r"need.*to.*book.*to\s+(\w+)",
            r"looking.*to.*book.*to\s+(\w+)"
        ]
        
        query = query.lower()
        for pattern in booking_phrases:
            match = re.search(pattern, query)
            if match:
                destination = match.group(1).strip()
                return True, destination
        return False, ""
    
    def _get_booking_url(self, destination: str) -> str:
        """Generate the booking URL for a destination"""
        # Convert destination to URL format
        destination = destination.lower().replace(" ", "-")
        return f"{self.base_url}/{destination}"
    
    def _is_first_message(self, session_id: str) -> bool:
        """Check if this is the user's first message using Redis"""
        if not self.redis_client:
            return True  # If no Redis, treat as first message
            
        try:
            # Check if session exists in Redis
            session_key = f"session:{session_id}"
            session_data = self.redis_client.get(session_key)
            
            if not session_data:
                # First time user, create session
                self.redis_client.set(session_key, json.dumps({"message_count": 1}))
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
    
    def get_response(self, query: str, session_id: str):
        """Get response using RAG or handle booking request"""
        try:
            # Check if it's a greeting
            if query.lower() in ["hi", "hello", "hey", "greetings", "start"]:
                if self._is_first_message(session_id):
                    return self.welcome_message
                else:
                    return self.welcome_back_message
            
            # Check if it's a booking request
            is_booking, destination = self._is_booking_request(query)
            if is_booking:
                booking_url = self._get_booking_url(destination)
                return f"I'll help you book your trip to {destination.title()}. You can view and book packages here: {booking_url}"
            
            # If not a booking request, use RAG
            memory = self.get_memory(session_id)
            
            template = """You are a helpful travel assistant for Reindeer Holidays. Use the following pieces of context to answer the user's question.
            If you don't know the answer, just say that you don't know, don't try to make up an answer.
            Always maintain a friendly and professional tone, and include relevant emojis where appropriate.
            
            Context: {context}
            Chat History: {chat_history}
            Question: {question}
            Answer:"""
            
            prompt = PromptTemplate(
                input_variables=["context", "chat_history", "question"],
                template=template
            )
            
            chain = ConversationalRetrievalChain.from_llm(
                llm=ChatOpenAI(
                    model="gpt-4",
                    temperature=0.7,
                    openai_api_key=os.getenv("OPENAI_API_KEY")
                ),
                retriever=self.vector_store.as_retriever(),
                memory=memory,
                combine_docs_chain_kwargs={"prompt": prompt},
                verbose=True
            )
            
            logger.info(f"Processing query: {query}")
            response = chain({"question": query})
            
            if isinstance(response, dict) and "answer" in response:
                return response["answer"]
            elif isinstance(response, str):
                return response
            else:
                logger.error(f"Unexpected response format: {response}")
                return "I apologize, but I'm having trouble processing your request at the moment."
            
        except Exception as e:
            logger.error(f"RAG processing error: {str(e)}")
            return "I apologize, but I'm having trouble processing your request at the moment."
    
    def clear_memory(self, session_id: str):
        """Clear conversation memory for a session"""
        if session_id in self.conversation_memories:
            del self.conversation_memories[session_id] 