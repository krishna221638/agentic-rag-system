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
        
        # Exact Trace Logging Format with Chain of Thought
        print("-" * 80)
        print(f"Question:    {question}")
        for i, step in enumerate(response.get("trace", [])):
            print(f"Step {i+1}:      tool={step.get('tool', 'Unknown')}")
            
            # Print the agent's internal reasoning if it exists
            if 'thought' in step:
                print(f"             thought='{step['thought']}'")
                
            print(f"             input='{step.get('input', '')}'")
            print(f"             result={str(step.get('result', ''))[:150]}...")
        
        print(f"\nFinal Answer: {response.get('answer')}")
        
        print("\nCitations:")
        citations = response.get("citations", [])
        if citations:
            for c in citations:
                print(f"- {c}")
        else:
            print("- None")
            
        print(f"\nSteps used: {response.get('steps')} / 8 max")
        print("-" * 80 + "\n")

if __name__ == "__main__":
    main()