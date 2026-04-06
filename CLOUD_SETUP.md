# Google BigQuery setup

This project can load the cleaned Kickstarter table into **Google BigQuery** so the data lives in the cloud and you can query it with SQL, including from the BigQuery console or from Python.

## What this adds

Cleaned data is uploaded to a BigQuery table, which means it is stored in the cloud and can be queried at scale. You run example SQL in BigQuery, and you can optionally run queries from Python as well. This file and the README document the setup so the process is reproducible.

## Step-by-step setup

### 1. Google Cloud account

Go to [Google Cloud](https://cloud.google.com/) and sign in, or create an account if you need one. BigQuery has a [free tier](https://cloud.google.com/bigquery/pricing), and new users often also get free credits.

### 2. Create a project

In the [Cloud Console](https://console.cloud.google.com/), click the project dropdown, and then create a new project by selecting **New Project**. Name the project, for example `kickstarter-analytics`, and copy the **Project ID** because you will use it as `GCP_PROJECT`.

### 3. Enable BigQuery API

In the console, open **APIs & Services**, then open **Library**. Search for **BigQuery API**, open it, and click **Enable**.

### 4. Create a service account (for the script)

Go to **IAM & Admin**, and then open **Service Accounts**. Create a service account, name it for example `bigquery-upload`, and click **Create and Continue**. Under **Grant access**, add the role **BigQuery Data Editor**, and add **BigQuery Job User** if it is available. Click **Done** when you finish. After the service account is created, open it, go to **Keys**, and then click **Add Key** to create a new JSON key, which you can download. Place the downloaded JSON file somewhere safe, for example directly in your project folder as `gcp-key.json`. Do not commit the key file to Git, and add it to `.gitignore`.

### 5. Set environment variables

**Windows (PowerShell):**

```powershell
$env:GOOGLE_APPLICATION_CREDENTIALS = "C:\path\to\your\gcp-key.json"
$env:GCP_PROJECT = "your-actual-project-id"
```

**Optional:** `BQ_DATASET` is the dataset name used in BigQuery, and it defaults to `kickstarter`:

```powershell
$env:BQ_DATASET = "kickstarter"
```

Use your real Project ID and the path to the JSON key file you downloaded.

### 6. Install Python dependencies

From the project root, install the required packages:

```powershell
pip install google-cloud-bigquery pyarrow
```

### 7. Run the upload script

From the project root, with `GOOGLE_APPLICATION_CREDENTIALS` and `GCP_PROJECT` set, run:

```powershell
python scripts/05_cloud_bigquery_upload.py
```

The script will read `data/cleaned/kickstarter_cleaned.csv`, create the BigQuery dataset if it does not exist, upload the table named `projects`, and then run an example SQL query that calculates success rate by `main_category`. It will print the query results in your terminal.

### Troubleshooting

- **`403` / `User does not have bigquery.datasets.create permission`:** The service account needs permission to create datasets and load tables. In **IAM & Admin → IAM**, find the principal matching your upload service account (email like `bigquery-upload@PROJECT_ID.iam.gserviceaccount.com`), click **Edit principal**, and ensure it has at least **BigQuery Data Editor** and **BigQuery Job User** (as in step 4). Save, wait a minute, then run the upload script again.

- **Organization policy blocks service account key creation (`iam.disableServiceAccountKeyCreation`):** Some accounts cannot create JSON keys. Install the [Google Cloud CLI](https://cloud.google.com/sdk/docs/install), then run `gcloud auth application-default login` and sign in with the Google account that has access to the project. Do **not** set `GOOGLE_APPLICATION_CREDENTIALS`. Run `python scripts/05_cloud_bigquery_upload.py` with `GCP_PROJECT` set; the script uses **Application Default Credentials** (your user identity) instead of a key file. Your user needs BigQuery permissions on the project (for example **Owner**, or **BigQuery Admin** / **BigQuery Data Editor** plus **BigQuery Job User**).

## Why use BigQuery here

Storing the cleaned Kickstarter data (US and USD scope, see README) in BigQuery shows the full path from local ETL to a cloud data warehouse, and you can validate the pipeline with the same SQL in the console or in Python. The steps above are also referenced from the README and from `scripts/05_cloud_bigquery_upload.py`.
