from agent.agent import run_agent
from scripts.setup_db import setup_database
from scripts.setup_chroma import setup_chroma

def main():
    """
    Main function to run the agentic RAG system.
    """
    # Setup the database on first run
    print("Setting up the database...")
    setup_database()
    setup_chroma()
    print("Databases setup complete.")

    while True:
        question = input("\nAsk a question (or type 'exit' to quit): ")
        if question.lower() == 'exit':
            break
            
        print("\nRunning Agent...\n")
        response = run_agent(question)
        
        # Exact Trace Logging Format
        print("-" * 80)
        print(f"Question:    {question}")
        for i, step in enumerate(response.get("trace", [])):
            print(f"Step {i+1}:      tool={step['tool']}   input='{step['input']}'")
            print(f"             result={step['result'][:150]}...")
        
        print(f"Final Answer: {response.get('answer')}")
        citations_str = ", ".join(response.get("citations", [])) if response.get("citations") else "None"
        print(f"Citations:   {citations_str}")
        print(f"Steps used:  {response.get('steps')} / 8 max")
        print("-" * 80 + "\n")

if __name__ == "__main__":
    main()
