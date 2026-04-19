import os
import chromadb
from chromadb.utils import embedding_functions
from dotenv import load_dotenv

load_dotenv()

CHROMA_PATH = "f:/agentic-rag-system/data/chroma"

def search_docs(query_string: str) -> str:
    """
    Search for semantically relevant information in unstructured documents.
    Args:
        query_string: Natural language query string.
    Returns:
        Top-3 relevant text chunks with source filename and page number.
    """
    try:
        client = chromadb.PersistentClient(path=CHROMA_PATH)
        
        collection = client.get_collection(
            name="financial_docs", 
            embedding_function=embedding_functions.DefaultEmbeddingFunction()
        )
        
        results = collection.query(
            query_texts=[query_string],
            n_results=3
        )
        
        output = ""
        for i, (doc, meta) in enumerate(zip(results['documents'][0], results['metadatas'][0])):
            snippet = doc[:300].replace('\n', ' ')
            source = f"{meta['source']} p. {meta['page']}"
            output += f"[Chunk {i+1} from {source}]: {snippet}...\n"
            
        return output if output else "No relevant documents found."
    except Exception as e:
        return f"Error searching documents: {str(e)}"

if __name__ == '__main__':
    # Example usage
    print(search_docs("What is the strategy of Infosys for FY24?"))
