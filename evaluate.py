import json
import time
from agent import run_agent  # Ensure this points to the file containing your run_agent function

def run_evaluation_suite():
    """
    Comprehensive verification suite for the Agentic RAG System.
    Validates Agentic ReAct capabilities across structured SQL execution, 
    semantic document retrieval, real-time web extraction, and out-of-domain handling.
    """
    print("=" * 70)
    print("🚀 STARTING AGENTIC RAG SYSTEM EVALUATION (20 TEST CASES)")
    print("=" * 70)

    test_cases = [
        # --- Core Financial Data Retrieval ---
        {
            "id": "TC-01",
            "type": "Structured Data (SQL)",
            "query": "What was Infosys' operating margin in FY24?",
            "expected_tools": ["query_data"]
        },
        {
            "id": "TC-02",
            "type": "Unstructured Retrieval (RAG)",
            "query": "What reason did TCS give for its margin improvement in FY24?",
            "expected_tools": ["search_docs"]
        },
        {
            "id": "TC-03",
            "type": "Hybrid Reasoning (SQL + RAG)",
            "query": "How did Infosys' and TCS' operating margins compare in FY24, and what drove each?",
            "expected_tools": ["query_data", "search_docs"]
        },
        {
            "id": "TC-04",
            "type": "Real-time Extraction (Web)",
            "query": "What is the current stock price of Infosys?",
            "expected_tools": ["web_search"]
        },
        {
            "id": "TC-05",
            "type": "Entity Resolution (Web/RAG)",
            "query": "Who is the current CFO of TCS?",
            "expected_tools": ["web_search"]
        },
        {
            "id": "TC-06",
            "type": "Trend Analysis (SQL)",
            "query": "What was Wipro's revenue growth over the last 4 years?",
            "expected_tools": ["query_data"]
        },
        {
            "id": "TC-07",
            "type": "Strategic Extraction (RAG)",
            "query": "What strategic priorities did Infosys highlight in their FY24 MD&A?",
            "expected_tools": ["search_docs"]
        },
        {
            "id": "TC-08",
            "type": "Aggregated Comparison (SQL)",
            "query": "Compare headcount growth at all 3 companies over 4 years.",
            "expected_tools": ["query_data"]
        },
        {
            "id": "TC-09",
            "type": "Market Intelligence (Web)",
            "query": "What happened to IT sector stocks last week?",
            "expected_tools": ["web_search"]
        },
        {
            "id": "TC-10",
            "type": "Domain Boundary Check",
            "query": "What is the airspeed velocity of an unladen swallow?",
            "expected_tools": [] # Expecting direct refusal or general knowledge response
        },

        # --- Rigorous Edge Cases & Analytical Queries ---
        {
            "id": "TC-11",
            "type": "Computational SQL (MAX)",
            "query": "Which company had the highest net profit in 2024?",
            "expected_tools": ["query_data"]
        },
        {
            "id": "TC-12",
            "type": "Contextual Retrieval (RAG)",
            "query": "Did Wipro face any attrition challenges recently according to their annual report?",
            "expected_tools": ["search_docs"]
        },
        {
            "id": "TC-13",
            "type": "Regex Anchoring Check (Web)",
            "query": "Give me the exact live share price of TCS right now.",
            "expected_tools": ["web_search"]
        },
        {
            "id": "TC-14",
            "type": "Multi-Entity Lookup (SQL)",
            "query": "Give me the EPS for Infosys, TCS, and Wipro in 2023.",
            "expected_tools": ["query_data"]
        },
        {
            "id": "TC-15",
            "type": "Risk Assessment (RAG)",
            "query": "What are the key financial risks mentioned by TCS in their FY24 report?",
            "expected_tools": ["search_docs"]
        },
        {
            "id": "TC-16",
            "type": "Out-of-Domain Rejection",
            "query": "Who won the cricket world cup in 2011?",
            "expected_tools": []
        },
        {
            "id": "TC-17",
            "type": "Parallel Reasoning (SQL + Web)",
            "query": "Compare the revenue of Infosys and Wipro in 2024 and find their latest news.",
            "expected_tools": ["query_data", "web_search"]
        },
        {
            "id": "TC-18",
            "type": "Precise Numeric Lookup (SQL)",
            "query": "Exactly how many employees did Infosys have in 2022?",
            "expected_tools": ["query_data"]
        },
        {
            "id": "TC-19",
            "type": "Executive Leadership Check (Web)",
            "query": "Who is the CEO of Wipro?",
            "expected_tools": ["web_search"]
        },
        {
            "id": "TC-20",
            "type": "Time-Series Summary (SQL)",
            "query": "Summarize the financial performance of TCS over the last 3 years based on data.",
            "expected_tools": ["query_data"]
        }
    ]

    passed = 0

    for i, tc in enumerate(test_cases):
        print(f"\n[{tc['id']}] {tc['type']}")
        print(f"QUERY: '{tc['query']}'")
        
        try:
            # Respecting API rate limits for consistent evaluation
            time.sleep(1.5) 
            
            result = run_agent(tc['query'])
            trace = result.get('trace', [])
            
            # Filter tools to ensure routing logic is valid
            tools_used = set([step.get('tool') for step in trace if step.get('tool') != 'system_correction'])
            steps_taken = result.get('steps', 0)
            
            # Validation logic
            if not tc['expected_tools']:
                # Pass if the agent handles out-of-domain queries without redundant tool calls
                success = len(tools_used) == 0
            else:
                # Pass if the agent successfully identified at least one necessary tool
                success = any(tool in tools_used for tool in tc['expected_tools'])
            
            if success:
                print(f"✅ PASS: Steps: {steps_taken}. Tools: {list(tools_used) if tools_used else 'None'}")
                passed += 1
            else:
                print(f"❌ FAIL:")
                print(f"     Expected: {tc['expected_tools']} | Observed: {list(tools_used)}")
                print(f"     Response: {result.get('answer', 'N/A')[:150]}...")
                
        except Exception as e:
            print(f"❌ SYSTEM ERROR: {str(e)}")

    print("\n" + "=" * 70)
    print(f"📊 SUMMARY: {passed} / {len(test_cases)} TEST CASES PASSED")
    print("=" * 70)

if __name__ == '__main__':
    run_evaluation_suite()