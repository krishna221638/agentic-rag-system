import sqlite3
import json

DB_PATH = "f:/agentic-rag-system/data/financials.db"

def query_data(query):
    """
    Execute a SQL query on the financials database and return the result as JSON.
    """
    try:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        cursor.execute(query)
        rows = cursor.fetchall()
        columns = [description[0] for description in cursor.description]
        conn.close()
        
        result = [dict(zip(columns, row)) for row in rows]
        return json.dumps(result, indent=2)
    except sqlite3.Error as e:
        return json.dumps({"error": str(e)})

if __name__ == '__main__':
    # Example usage
    print(query_data("SELECT * FROM financials WHERE company = 'TCS' AND year = 2024"))
