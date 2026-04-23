import sqlite3
import pandas as pd
import os

# Changed from absolute paths to relative paths to ensure it runs on any machine
DB_DIR = "./data"
DB_PATH = os.path.join(DB_DIR, "financials.db")
CSV_PATH = os.path.join(DB_DIR, "financials.csv")

def setup_database():
    """
    Load data from a CSV file into a SQLite database.
    """
    # Ensure the data directory exists
    if not os.path.exists(DB_DIR):
        os.makedirs(DB_DIR)

    if os.path.exists(DB_PATH):
        print("Database already setup. Skipping CSV parsing.")
        return

    if not os.path.exists(CSV_PATH):
        print(f"Error: Could not find the CSV file at {CSV_PATH}. Please ensure it exists.")
        return

    conn = sqlite3.connect(DB_PATH)
    try:
        df = pd.read_csv(CSV_PATH)
        df.to_sql("financials", conn, if_exists="replace", index=False)
        print("Database setup complete.")
    except Exception as e:
        print(f"Error loading CSV to database: {str(e)}")
    finally:
        conn.close()

if __name__ == "__main__":
    setup_database()