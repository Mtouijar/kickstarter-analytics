"""
Run example SQL against the SQLite database: aggregates and filters by category
to show how the stored data can be queried.
"""

import sqlite3
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
DB_PATH = PROJECT_ROOT / "data" / "cleaned" / "kickstarter.db"


def main():
    if not DB_PATH.exists():
        print(f"Database not found: {DB_PATH}. Run 03_store_cleaned.py first.")
        return

    conn = sqlite3.connect(DB_PATH)

    # Query 1: Count by main_category
    print("--- Count by main_category ---")
    q1 = conn.execute(
        "SELECT main_category, COUNT(*) AS n FROM projects GROUP BY main_category ORDER BY n DESC"
    )
    for row in q1:
        print(f"  {row[0]}: {row[1]}")

    # Query 2: Success rate by main_category (aggregate)
    print("\n--- Success rate by main_category ---")
    q2 = conn.execute("""
        SELECT main_category,
               SUM(CASE WHEN state = 'successful' THEN 1 ELSE 0 END) * 1.0 / COUNT(*) AS success_rate
        FROM projects
        GROUP BY main_category
        ORDER BY success_rate DESC
        LIMIT 5
    """)
    for row in q2:
        print(f"  {row[0]}: {row[1]:.2%}")

    # Query 3: Filter + aggregate (e.g. Games only, avg goal)
    print("\n--- Games: avg usd_goal_real and project count ---")
    q3 = conn.execute("""
        SELECT COUNT(*) AS n, AVG(usd_goal_real) AS avg_goal
        FROM projects
        WHERE main_category = 'Games'
    """)
    row = q3.fetchone()
    print(f"  Projects: {row[0]}, Avg goal (USD): ${row[1]:,.0f}")

    # Query 4: Rows by snapshot_year (after ETL dedupe, typically 2018 only)
    print("\n--- Count by snapshot_year ---")
    try:
        q4 = conn.execute(
            "SELECT snapshot_year, COUNT(*) AS n FROM projects GROUP BY snapshot_year ORDER BY snapshot_year"
        )
        for row in q4:
            print(f"  {row[0]}: {row[1]}")
    except Exception as e:
        print(f"  (skip) {e}")

    conn.close()
    print("\nDone. Queryability demonstrated.")


if __name__ == "__main__":
    main()
