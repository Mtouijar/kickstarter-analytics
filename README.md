# Predicting Crowdfunding Success: US Kickstarter Campaigns (USD)

This repository is an end-to-end analytics pipeline for historical Kickstarter data: ingest and clean exports, store them locally, explore patterns, train classification models, and summarize findings in the report. The optional Google BigQuery path loads the same cleaned table into the cloud so you can run SQL there.

## Dataset

The data comes from Kaggle’s [Kickstarter Projects](https://www.kaggle.com/datasets/kemical/kickstarter-projects) dataset. The archive includes two CSV exports, `ks-projects-201612.csv` and `ks-projects-201801.csv`, and this project uses both. Please respect the license and terms on the Kaggle page.

The analysis restricts rows to campaigns from the **United States** with **USD** currency, and to finished outcomes only (**successful** or **failed**). That keeps funding amounts comparable and aligns with the write-up under `report/`. The 2016 file has a different column layout than the 2018 file, so the ETL script normalizes columns before merging. After filters, `data/cleaned/snapshot_comparison.json` summarizes counts and success rate **per export**; then the pipeline deduplicates on project `id` and keeps one row per id, preferring the **2018** row when the same id appears twice.

## Reproducibility

You will need **Python 3.10+** and a normal SQLite install (included with Python on most setups).

**Steps:**

1. **Data:** Either run `python scripts/01_download_data.py` with the [Kaggle API](https://github.com/Kaggle/kaggle-api) set up, or download the dataset from Kaggle, unzip it, and put both `ks-projects-201612.csv` and `ks-projects-201801.csv` under `data/raw/` (a subfolder is fine).

2. **ETL:** `python scripts/02_etl_clean.py` writes `data/cleaned/kickstarter_cleaned.csv`, `data/cleaned/data_dictionary.json`, and `data/cleaned/snapshot_comparison.json`.

3. **Storage:** `python scripts/03_store_cleaned.py` builds `data/cleaned/kickstarter.db` with table `projects`. You can run `python scripts/04_example_queries.py` to print sample SQL results.

4. **Notebook:** Open `notebooks/eda_and_prediction.ipynb` in Jupyter, or after `pip install nbconvert ipykernel` run  
   `python -m nbconvert --to notebook --execute notebooks/eda_and_prediction.ipynb --inplace`  
   to refresh outputs and the figures under `report/`.

5. **Write-up:** The narrative and figures live in `report/` (see `report_template.md`).

## Google BigQuery

To load the cleaned CSV into **Google BigQuery**, follow [CLOUD_SETUP.md](CLOUD_SETUP.md), set `GCP_PROJECT`, and run `python scripts/05_cloud_bigquery_upload.py`. For authentication you can use a service account JSON via `GOOGLE_APPLICATION_CREDENTIALS`, or **Application Default Credentials** if your organization blocks key downloads: install the [Google Cloud CLI](https://cloud.google.com/sdk/docs/install), run `gcloud auth application-default login`, then run the upload script without pointing at a key file.

## Project layout

```
kickstarter-analytics/
├── README.md
├── CLOUD_SETUP.md
├── data/
│   ├── raw/          # Original CSVs (obtain per steps above; not all stored in git)
│   └── cleaned/      # Processed outputs, dictionary JSON, snapshot comparison
├── scripts/          # Download, ETL, SQLite, example SQL, BigQuery upload
├── notebooks/        # EDA and modeling
├── report/           # Report markdown and figure PNGs
└── requirements.txt
```

## Repository

Source: [https://github.com/Mtouijar/kickstarter-analytics](https://github.com/Mtouijar/kickstarter-analytics)

If you clone this repo, do not commit **secrets** (Google Cloud JSON keys, API tokens, or Kaggle credentials). The `.gitignore` lists common key filenames. Using `gcloud auth application-default login` keeps cloud credentials on your machine instead of in the repo.

## Author

Mehdi Touijar
