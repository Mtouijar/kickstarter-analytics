"""
Upload cleaned Kickstarter data to Google BigQuery and run example queries
(storage plus queryability in the cloud).

Authentication (pick one):
  - Service account JSON: set GOOGLE_APPLICATION_CREDENTIALS to the key file path.
  - No JSON keys allowed (org policy): install Google Cloud CLI and run
    `gcloud auth application-default login` so your user account provides credentials.
    Your user needs BigQuery permissions on the project (e.g. Owner or BigQuery roles).

Other prerequisites: BigQuery API enabled, pip install google-cloud-bigquery pyarrow
"""

import os
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
CLEANED_CSV = PROJECT_ROOT / "data" / "cleaned" / "kickstarter_cleaned.csv"

# Set these for your GCP project (or use env vars)
GCP_PROJECT = os.environ.get("GCP_PROJECT", "your-gcp-project-id")
BQ_DATASET = os.environ.get("BQ_DATASET", "kickstarter")
BQ_TABLE = "projects"


def main():
    if not CLEANED_CSV.exists():
        print(f"Cleaned CSV not found: {CLEANED_CSV}. Run 02_etl_clean.py first.")
        return

    try:
        from google.cloud import bigquery
        import pandas as pd
    except ImportError:
        print("Install cloud dependencies: pip install google-cloud-bigquery pyarrow")
        return

    if not os.environ.get("GOOGLE_APPLICATION_CREDENTIALS"):
        print(
            "Using Application Default Credentials (no GOOGLE_APPLICATION_CREDENTIALS set)."
        )
        print(
            "If upload fails with auth errors, run: gcloud auth application-default login"
        )

    if GCP_PROJECT == "your-gcp-project-id":
        print("Set GCP_PROJECT (or env GCP_PROJECT) to your Google Cloud project ID.")
        return

    client = bigquery.Client(project=GCP_PROJECT)
    table_id = f"{GCP_PROJECT}.{BQ_DATASET}.{BQ_TABLE}"

    # Ensure dataset exists
    dataset_id = f"{GCP_PROJECT}.{BQ_DATASET}"
    try:
        client.get_dataset(dataset_id)
    except Exception:
        dataset = bigquery.Dataset(dataset_id)
        dataset.location = "US"
        client.create_dataset(dataset)
        print(f"Created dataset {BQ_DATASET}.")

    # Load cleaned CSV into BigQuery
    print(f"Reading {CLEANED_CSV}...")
    df = pd.read_csv(CLEANED_CSV, nrows=None)
    # BigQuery prefers standard types; keep dates as strings if needed
    for col in ["launched", "deadline"]:
        if col in df.columns:
            df[col] = pd.to_datetime(df[col], errors="coerce").astype(str)

    print(f"Uploading {len(df)} rows to BigQuery table {table_id}...")
    job = client.load_table_from_dataframe(df, table_id)
    job.result()
    print("Upload complete.")

    # Run example query to demonstrate queryability
    print("\n--- Example query: success rate by main_category (top 5) ---")
    query = f"""
        SELECT main_category,
               COUNT(*) AS n,
               SAFE_DIVIDE(SUM(CASE WHEN state = 'successful' THEN 1 ELSE 0 END), COUNT(*)) AS success_rate
        FROM `{table_id}`
        GROUP BY main_category
        ORDER BY success_rate DESC
        LIMIT 5
    """
    rows = client.query(query).result()
    for row in rows:
        print(f"  {row.main_category}: n={row.n}, success_rate={row.success_rate:.2%}")

    print("\nCloud integration done. Data is stored and queryable in BigQuery.")


if __name__ == "__main__":
    main()
