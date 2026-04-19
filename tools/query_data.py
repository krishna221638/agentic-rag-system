import sqlite3
import json

DB_PATH = "f:/agentic-rag-system/data/financials.db"

def query_data(sql_query: str) -> str:
    """
    Execute a SQL query on the financials database. Database has table 'financials' 
    with columns: company, year, revenue, operating_margin, net_profit, eps, headcount.
    Args:
        sql_query: A valid SQL query string.
    Returns:
        JSON string of results with column names and row count, or error message.
    """
    try:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        cursor.execute(sql_query)
        rows = cursor.fetchall()
        columns = [description[0] for description in cursor.description]
        conn.close()
        
        result = [dict(zip(columns, row)) for row in rows]
        output = {
            "columns": columns,
            "row_count": len(result),
            "data": result[:10]  # Limiting output to first 10 rows
        }
        return json.dumps(output, indent=2)
    except sqlite3.Error as e:
        return f"SQL Error: {str(e)}"

if __name__ == '__main__':
    # Example usage
    print(query_data("SELECT company, revenue FROM financials WHERE year = 2024 ORDER BY revenue DESC LIMIT 3"))
