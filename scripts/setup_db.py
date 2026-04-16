import sqlite3
import pandas as pd

DB_PATH = "f:/agentic-rag-system/data/financials.db"
CSV_PATH = "f:/agentic-rag-system/data/financials.csv"

def setup_database():
    """
    Load data from a CSV file into a SQLite database.
    """
    conn = sqlite3.connect(DB_PATH)
    df = pd.read_csv(CSV_PATH)
    df.to_sql("financials", conn, if_exists="replace", index=False)
    conn.close()
    print("Database setup complete.")

if __name__ == "__main__":
    setup_database()
