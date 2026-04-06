"""
Storage: load cleaned CSV into SQLite so the data is queryable (filters,
aggregates, joins). Creates data/cleaned/kickstarter.db and a single table.
"""

import sqlite3
import pandas as pd
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
CLEANED_DIR = PROJECT_ROOT / "data" / "cleaned"
CSV_PATH = CLEANED_DIR / "kickstarter_cleaned.csv"
DB_PATH = CLEANED_DIR / "kickstarter.db"


def main():
    if not CSV_PATH.exists():
        raise FileNotFoundError(
            f"Cleaned CSV not found: {CSV_PATH}. Run 02_etl_clean.py first."
        )

    df = pd.read_csv(CSV_PATH)

    # SQLite prefers column names that are valid identifiers
    df.columns = [c.replace(" ", "_").replace("-", "_") for c in df.columns]

    conn = sqlite3.connect(DB_PATH)
    df.to_sql("projects", conn, index=False, if_exists="replace")
    conn.close()

    print(f"Stored {len(df)} rows in {DB_PATH} (table: projects)")
    print("Example: query by main_category or country for EDA and modeling.")


if __name__ == "__main__":
    main()
