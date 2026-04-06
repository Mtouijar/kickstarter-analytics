"""
Data acquisition: Kickstarter Projects dataset.

Dataset: https://www.kaggle.com/datasets/kemical/kickstarter-projects
- Data from May 2009 to March 2018.
- Zip contains two CSVs (2016 and 2018). The ETL script uses **both** for the scoped analysis (see README).

Reproducible options:
  A) Kaggle API (if kaggle installed and credentials in ~/.kaggle/kaggle.json):
       kaggle datasets download -d kemical/kickstarter-projects -p data/raw
       Then unzip the archive so both ks-projects-201612.csv and ks-projects-201801.csv are under data/raw/.

  B) Manual: Download the dataset from the link above, unzip, and place both CSVs under data/raw/ (or a subfolder).

This script tries (A) and unzips into data/raw/. If the API is not set up,
do (B) and re-run the rest of the pipeline; the ETL script expects the two Kaggle snapshot files.
"""

import os
import subprocess
import zipfile
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
RAW_DIR = PROJECT_ROOT / "data" / "raw"


def main():
    RAW_DIR.mkdir(parents=True, exist_ok=True)
    zip_path = RAW_DIR / "kickstarter-projects.zip"

    try:
        subprocess.run(
            [
                "kaggle", "datasets", "download",
                "-d", "kemical/kickstarter-projects",
                "-p", str(RAW_DIR),
            ],
            check=True,
            capture_output=True,
            text=True,
        )
    except (subprocess.CalledProcessError, FileNotFoundError):
        print(
            "Kaggle API not used (not installed or not configured).\n"
            "Download the dataset manually from:\n"
            "  https://www.kaggle.com/datasets/kemical/kickstarter-projects\n"
            "Unzip it and place both snapshot CSVs (201612 and 201801) in:\n"
            f"  {RAW_DIR}"
        )
        return

    if zip_path.exists():
        with zipfile.ZipFile(zip_path, "r") as z:
            z.extractall(RAW_DIR)
        zip_path.unlink()
        print(f"Extracted files into {RAW_DIR}")
    else:
        print("Zip file not found. Use manual download (see message above).")


if __name__ == "__main__":
    main()
