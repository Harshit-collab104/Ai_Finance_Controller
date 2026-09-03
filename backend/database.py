import sqlite3
import pandas as pd
from typing import List, Dict, Any, Optional
from backend.config import DB_FILE_PATH, CSV_FILE_PATH
from backend.ratio_engine import compute_financial_ratios

def get_connection():
    conn = sqlite3.connect(str(DB_FILE_PATH))
    conn.row_factory = sqlite3.Row
    return conn

def init_db(df: Optional[pd.DataFrame] = None):
    if df is None:
        if CSV_FILE_PATH.exists():
            df = pd.read_csv(CSV_FILE_PATH)
        else:
            from backend.data_generator import save_dataset
            df = save_dataset()

    df_ratios = compute_financial_ratios(df)
    
    conn = get_connection()
    df_ratios.to_sql("financial_records", conn, if_exists="replace", index=False)
    conn.commit()
    conn.close()
    print("SQLite database initialized successfully.")

def get_all_records() -> pd.DataFrame:
    conn = get_connection()
    df = pd.read_sql("SELECT * FROM financial_records", conn)
    conn.close()
    return df

def get_company_records(company_id: str) -> pd.DataFrame:
    conn = get_connection()
    df = pd.read_sql("SELECT * FROM financial_records WHERE company_id = ? ORDER BY period_idx ASC", conn, params=(company_id,))
    conn.close()
    return df

def get_company_list() -> List[Dict[str, Any]]:
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("""
        SELECT company_id, company_name, category, 
               COUNT(*) as total_periods,
               MAX(cash) as latest_cash
        FROM financial_records
        GROUP BY company_id
        ORDER BY company_id ASC
    """)
    rows = cursor.fetchall()
    conn.close()
    return [dict(r) for r in rows]
