import os
from PyPDF2 import PdfReader

DOCS_DIR = "f:/agentic-rag-system/data/docs/"

def search_docs(keyword):
    """
    Search for a keyword in PDF documents and return relevant text snippets.
    """
    results = []
    for filename in os.listdir(DOCS_DIR):
        if filename.endswith(".pdf"):
            filepath = os.path.join(DOCS_DIR, filename)
            reader = PdfReader(filepath)
            for page_num, page in enumerate(reader.pages):
                text = page.extract_text()
                if keyword.lower() in text.lower():
                    # Simple implementation: return first 200 chars of the page
                    snippet = text[:200]
                    results.append({
                        "source": f"{filename}, page {page_num + 1}",
                        "snippet": snippet.strip()
                    })
    return results

if __name__ == '__main__':
    # Example usage
    print(search_docs("strategy"))
