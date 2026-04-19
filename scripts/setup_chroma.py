import os
from PyPDF2 import PdfReader
import chromadb
from chromadb.utils import embedding_functions
from dotenv import load_dotenv

load_dotenv()

DOCS_DIR = "f:/agentic-rag-system/data/docs/"
CHROMA_PATH = "f:/agentic-rag-system/data/chroma"

def setup_chroma():
    """
    Read PDFs, chunk them, and store them in ChromaDB.
    """
    print("Setting up vector database...")
    if not os.path.exists(CHROMA_PATH):
        os.makedirs(CHROMA_PATH)
    
    client = chromadb.PersistentClient(path=CHROMA_PATH)
    
    try:
        client.delete_collection(name="financial_docs")
    except Exception:
        pass
        
    collection = client.get_or_create_collection(
        name="financial_docs", 
        embedding_function=embedding_functions.DefaultEmbeddingFunction()
    )
    
    # Reset collection if running multiple times during development
    # collection.delete()
    
    documents = []
    metadatas = []
    ids = []
    chunk_id = 0
    
    for filename in os.listdir(DOCS_DIR):
        if filename.endswith(".pdf"):
            filepath = os.path.join(DOCS_DIR, filename)
            reader = PdfReader(filepath)
            for page_num, page in enumerate(reader.pages):
                text = page.extract_text()
                if text:
                    # Simple chunking by page
                    documents.append(text)
                    metadatas.append({"source": f"{filename}", "page": page_num + 1})
                    ids.append(str(chunk_id))
                    chunk_id += 1
    
    if documents:
        collection.add(
            documents=documents,
            metadatas=metadatas,
            ids=ids
        )
    print(f"Vector database setup complete. Indexed {len(documents)} chunks from PDFs.")

if __name__ == "__main__":
    setup_chroma()
