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
            # Create new vector store with initial document
            return FAISS.from_texts(
                ["Welcome to the travel assistant. How can I help you today?"],
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
    
    def get_response(self, query: str, session_id: str):
        """Get response using RAG"""
        try:
            # Get or create memory for this session
            memory = self.get_memory(session_id)
            
            # Create custom prompt template
            template = """You are a helpful travel assistant. Use the following pieces of context to answer the user's question.
            If you don't know the answer, just say that you don't know, don't try to make up an answer.
            
            Context: {context}
            Chat History: {chat_history}
            Question: {question}
            Answer:"""
            
            prompt = PromptTemplate(
                input_variables=["context", "chat_history", "question"],
                template=template
            )
            
            # Create chain with custom prompt
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
            
            # Get response
            logger.info(f"Processing query: {query}")
            response = chain({"question": query})
            
            # Extract just the answer from the response
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