from agent.agent import run_agent
from scripts.setup_db import setup_database

def main():
    """
    Main function to run the agentic RAG system.
    """
    # Setup the database on first run
    print("Setting up the database...")
    setup_database()
    print("Database setup complete.")

    while True:
        question = input("\nAsk a question (or type 'exit' to quit): ")
        if question.lower() == 'exit':
            break
        
        response = run_agent(question)
        
        print("\n---")
        print(f"Answer: {response['answer']}")
        print(f"Source: {response['source']}")
        print("---\n")

if __name__ == "__main__":
    main()
