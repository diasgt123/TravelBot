from app.services.rag_service import RAGService
from app.core.config import get_settings
import os
import logging
import shutil
from langchain_community.vectorstores import FAISS
from langchain_openai import OpenAIEmbeddings

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def count_documents_in_store(vector_store):
    """Count the number of documents in the vector store"""
    try:
        return len(vector_store.index_to_docstore_id)
    except:
        return 0

def clear_vector_store(vector_store_path):
    """Delete the existing vector store directory"""
    if os.path.exists(vector_store_path):
        logger.info(f"Clearing existing vector store at {vector_store_path}")
        shutil.rmtree(vector_store_path)
        logger.info("✅ Vector store cleared")

def process_uploads(rag_service, uploads_dir):
    """Process all PDFs in the uploads directory"""
    if not os.path.exists(uploads_dir):
        logger.error(f"❌ Uploads directory not found at {uploads_dir}")
        return False
    
    pdf_files = [f for f in os.listdir(uploads_dir) if f.endswith('.pdf')]
    if not pdf_files:
        logger.error("❌ No PDF files found in uploads directory")
        return False
    
    success = True
    for pdf_file in pdf_files:
        pdf_path = os.path.join(uploads_dir, pdf_file)
        logger.info(f"Processing: {pdf_file}")
        if rag_service.add_document(pdf_path):
            logger.info(f"✅ Successfully added {pdf_file}")
        else:
            logger.error(f"❌ Failed to add {pdf_file}")
            success = False
    
    return success

def interactive_conversation(rag_service):
    """Start an interactive conversation with the RAG system"""
    session_id = "conversation_test"
    print("\n🤖 Starting conversation with the travel assistant...")
    print("Type 'exit' to end the conversation")
    print("Type 'clear' to clear the conversation history")
    print("-" * 50)
    
    while True:
        # Get user input
        user_input = input("\n👤 You: ").strip()
        
        # Check for exit command
        if user_input.lower() == 'exit':
            print("\n👋 Ending conversation...")
            break
            
        # Check for clear command
        if user_input.lower() == 'clear':
            rag_service.clear_memory(session_id)
            print("🧹 Conversation history cleared")
            continue
            
        # Get response from RAG system
        print("\n🤖 Assistant: ", end="")
        response = rag_service.get_response(user_input, session_id)
        print(response)

def test_rag():
    """Test RAG functionality and check embeddings storage"""
    settings = get_settings()
    
    # Clear existing vector store
    vector_store_path = "data/vector_store"
    clear_vector_store(vector_store_path)
    
    # Initialize RAG service
    rag_service = RAGService(None)  # No Redis for this test
    
    # Process all PDFs in uploads directory
    uploads_dir = "data/uploads"
    logger.info(f"\nProcessing documents from {uploads_dir}")
    if process_uploads(rag_service, uploads_dir):
        # Check document count
        try:
            embeddings = OpenAIEmbeddings(
                model="text-embedding-3-small",
                openai_api_key=settings.OPENAI_API_KEY
            )
            vector_store = FAISS.load_local(vector_store_path, embeddings)
            doc_count = count_documents_in_store(vector_store)
            logger.info(f"Total document chunks in vector store: {doc_count}")
        except Exception as e:
            logger.error(f"Error checking document count: {e}")
    
    # Start interactive conversation
    interactive_conversation(rag_service)
    
    # Check vector store files
    if os.path.exists(vector_store_path):
        logger.info("\nVector store files:")
        for file in os.listdir(vector_store_path):
            file_path = os.path.join(vector_store_path, file)
            size = os.path.getsize(file_path) / 1024  # Size in KB
            logger.info(f"- {file} ({size:.2f} KB)")
    else:
        logger.error("❌ Vector store directory not created")

if __name__ == "__main__":
    test_rag() 