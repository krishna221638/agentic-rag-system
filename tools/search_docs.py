import os
import chromadb
from chromadb.utils import embedding_functions
from dotenv import load_dotenv

load_dotenv()

CHROMA_PATH = "./data/chroma"

def search_docs(query_string: str, top_k: int = 3, raw: bool = False):
    """
    Search for semantically relevant information in unstructured documents.     
    Args:
        query_string: Natural language query string.
        top_k: Number of results to return.
        raw: If True, returns a list of raw text chunks.
    Returns:
        Top-k relevant text chunks with source filename and page number, or raw list.
    """
    try:
        client = chromadb.PersistentClient(path=CHROMA_PATH)

        collection = client.get_collection(
            name="financial_docs"
        )
        
        # We need to explicitly initialize the embedding function to use the same default as creation
        from chromadb.utils import embedding_functions
        default_ef = embedding_functions.DefaultEmbeddingFunction()

        results = collection.query(
            query_texts=[query_string],
            n_results=top_k
        )
        
        if raw:
            docs = []
            for doc in results['documents'][0]:
                docs.append(doc)
            return docs

        output = ""
        for i, (doc, meta) in enumerate(zip(results['documents'][0], results['metadatas'][0])):
            snippet = doc[:300].replace('\n', ' ')
            source = f"{meta['source']} p. {meta['page']}"
            output += f"[Chunk {i+1} from {source}]: {snippet}...\n"

        return output if output else "No relevant documents found."
    except Exception as e:
        return [] if raw else f"Error searching documents: {str(e)}"

if __name__ == '__main__':
    # Example usage
    print(search_docs("What is the strategy of Infosys for FY24?"))