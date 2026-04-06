"""
ETL and data quality: load raw Kickstarter data (2016 and/or 2018 CSVs from the same
Kaggle bundle), normalize schema, apply scope filters, and write cleaned data plus a
data dictionary. Raw data stays in data/raw/; outputs go to data/cleaned/.
"""

import json
from pathlib import Path
from typing import Optional

import pandas as pd

PROJECT_ROOT = Path(__file__).resolve().parent.parent
RAW_DIR = PROJECT_ROOT / "data" / "raw"
CLEANED_DIR = PROJECT_ROOT / "data" / "cleaned"

# Analysis scope: US + USD for comparable money fields
FILTER_COUNTRY = "US"
FILTER_CURRENCY = "USD"

# Expected raw filenames from Kaggle archive kemical/kickstarter-projects
RAW_2016_NAMES = ("ks-projects-201612.csv",)
RAW_2018_NAMES = ("ks-projects-201801.csv",)


def _normalize_columns(df: pd.DataFrame) -> pd.DataFrame:
    df = df.copy()
    df.columns = [c.strip().lower().replace(" ", "_") for c in df.columns]
    drop_cols = [c for c in df.columns if c.startswith("unnamed")]
    return df.drop(columns=drop_cols, errors="ignore")


def _load_one_csv(path: Path, snapshot_year: int, encoding: Optional[str] = None) -> pd.DataFrame:
    read_kw = {"low_memory": False}
    if encoding:
        read_kw["encoding"] = encoding
    df = pd.read_csv(path, **read_kw)
    df = _normalize_columns(df)
    # Harmonize id column name if present with trailing space in source
    if "id" not in df.columns and "id_" in df.columns:
        df = df.rename(columns={"id_": "id"})
    df["snapshot_year"] = snapshot_year
    return df


def _ensure_usd_real_columns(df: pd.DataFrame, source: str) -> pd.DataFrame:
    """2018 has usd_goal_real / usd_pledged_real; 2016 does not — derive for USD rows."""
    df = df.copy()
    if "usd_goal_real" not in df.columns or df["usd_goal_real"].isna().all():
        if "currency" in df.columns and "goal" in df.columns:
            is_usd = df["currency"].astype(str).str.upper().eq(FILTER_CURRENCY)
            df.loc[is_usd, "usd_goal_real"] = pd.to_numeric(df.loc[is_usd, "goal"], errors="coerce")
    if "usd_pledged_real" not in df.columns or df["usd_pledged_real"].isna().all():
        pledge_col = None
        for name in ("usd_pledged", "usd_pledged_real"):
            if name in df.columns:
                pledge_col = name
                break
        if pledge_col and "currency" in df.columns:
            is_usd = df["currency"].astype(str).str.upper().eq(FILTER_CURRENCY)
            df.loc[is_usd, "usd_pledged_real"] = pd.to_numeric(
                df.loc[is_usd, pledge_col], errors="coerce"
            )
    return df


def find_raw_paths() -> list[tuple[Path, int]]:
    """Return list of (path, snapshot_year) for 2016 and 2018 files if present."""
    found: list[tuple[Path, int]] = []
    for p in RAW_DIR.rglob("*.csv"):
        name = p.name.lower()
        if name in [n.lower() for n in RAW_2016_NAMES]:
            found.append((p, 2016))
        elif name in [n.lower() for n in RAW_2018_NAMES]:
            found.append((p, 2018))
    # De-dupe paths
    by_path = {path.resolve(): year for path, year in found}
    return sorted(by_path.items(), key=lambda x: x[1])


def load_all_raw() -> tuple[pd.DataFrame, list[str]]:
    paths = find_raw_paths()
    if not paths:
        raise FileNotFoundError(
            f"No ks-projects-201612.csv or ks-projects-201801.csv found under {RAW_DIR}. "
            "Download from Kaggle and unzip into data/raw/ (see README)."
        )

    frames = []
    names = []
    for path, year in paths:
        enc = "latin-1" if year == 2016 else None
        try:
            df = _load_one_csv(path, year, encoding=enc)
        except UnicodeDecodeError:
            df = _load_one_csv(path, year, encoding="latin-1")
        df = _ensure_usd_real_columns(df, str(path.name))
        frames.append(df)
        names.append(path.name)

    out = pd.concat(frames, ignore_index=True)
    return out, names


def clean(
    df: pd.DataFrame, *, dedupe_across_snapshots: bool = True
) -> tuple[pd.DataFrame, dict, Optional[dict]]:
    """Clean the dataset: types, missing values, duplicates, scope filters.

    If dedupe_across_snapshots is True, duplicate project ids across 2016/2018 exports
    keep the later snapshot (2018) so modeling has one row per project.
    """
    df = df.copy()
    n_before = len(df)
    df = df.drop_duplicates()
    n_dupes = n_before - len(df)

    for col in ["launched", "deadline"]:
        if col in df.columns:
            df[col] = pd.to_datetime(df[col], errors="coerce")

    for col in ["goal", "pledged", "backers", "usd_goal_real", "usd_pledged_real"]:
        if col in df.columns:
            df[col] = pd.to_numeric(df[col], errors="coerce")

    if "usd_pledged" in df.columns:
        df["usd_pledged"] = pd.to_numeric(df["usd_pledged"], errors="coerce")

    if "state" in df.columns:
        df = df[df["state"].isin(["successful", "failed"])].copy()
        df["state"] = df["state"].astype(str).str.strip().str.lower()

    if "country" in df.columns:
        df = df[df["country"].astype(str).str.upper() == FILTER_COUNTRY].copy()

    if "currency" in df.columns:
        df = df[df["currency"].astype(str).str.upper() == FILTER_CURRENCY].copy()

    if "usd_goal_real" in df.columns:
        df = df[df["usd_goal_real"].notna() & (df["usd_goal_real"] > 0)]
    if "usd_pledged_real" in df.columns:
        df["usd_pledged_real"] = df["usd_pledged_real"].fillna(0)

    snapshot_summary = None
    if "snapshot_year" in df.columns:
        g = df.groupby("snapshot_year", dropna=False)
        snapshot_summary = {}
        for year, part in g:
            n = len(part)
            succ = (part["state"] == "successful").sum() if "state" in part.columns else 0
            snapshot_summary[int(year) if pd.notna(year) else year] = {
                "rows_after_filters": int(n),
                "success_rate": float(succ / n) if n else 0.0,
            }

    # Same project can appear in both exports; keep the later snapshot for one row per id
    if (
        dedupe_across_snapshots
        and "id" in df.columns
        and "snapshot_year" in df.columns
    ):
        df = df.sort_values("snapshot_year")
        df = df.drop_duplicates(subset=["id"], keep="last")

    missing = df.isnull().sum()

    cleaning_notes = {
        "duplicates_removed": n_dupes,
        "scope": f"country={FILTER_COUNTRY}, currency={FILTER_CURRENCY}",
        "dedupe_rule": "If a project id appears in both snapshots, keep the row from the later snapshot_year.",
        "snapshot_summary_before_id_dedupe": snapshot_summary,
        "missing_after_clean": missing.to_dict(),
    }
    return df, cleaning_notes, snapshot_summary


def build_data_dictionary(df: pd.DataFrame, cleaning_notes: dict, raw_files: list[str]) -> dict:
    d = {
        "source": "Kickstarter Projects (Kaggle), 2016 and/or 2018 CSVs in the same archive",
        "raw_files_used": raw_files,
        "cleaning_notes": cleaning_notes,
        "columns": {},
    }
    for col in df.columns:
        d["columns"][col] = {
            "dtype": str(df[col].dtype),
            "non_null": int(df[col].notna().sum()),
            "description": _describe_column(col),
        }
    return d


def _describe_column(col: str) -> str:
    desc = {
        "id": "Kickstarter project ID",
        "name": "Project name",
        "category": "Subcategory (e.g. Video Games)",
        "main_category": "Main category (e.g. Games)",
        "currency": "Currency code",
        "deadline": "Campaign deadline date",
        "goal": "Funding goal in original currency",
        "launched": "Launch date",
        "pledged": "Amount pledged in original currency",
        "state": "Outcome: successful or failed (completed only)",
        "backers": "Number of backers",
        "country": "Country code",
        "usd_pledged": "Pledged amount in USD (column name from Kaggle)",
        "usd_pledged_real": "Pledged amount in USD (aligned; see ETL for 2016)",
        "usd_goal_real": "Goal in USD (aligned; for USD rows matches goal in USD)",
        "snapshot_year": "Which Kaggle export the row came from after id deduplication",
    }
    return desc.get(col.lower(), "See dataset documentation.")


def main():
    CLEANED_DIR.mkdir(parents=True, exist_ok=True)

    df_raw, raw_names = load_all_raw()
    df_clean, cleaning_notes, snapshot_summary = clean(df_raw)

    if snapshot_summary:
        snap_path = CLEANED_DIR / "snapshot_comparison.json"
        with open(snap_path, "w", encoding="utf-8") as f:
            json.dump(
                {
                    "description": "Counts and success rates by Kaggle export after US+USD+completed filters, before dropping duplicate project ids across snapshots.",
                    "by_snapshot_year": snapshot_summary,
                },
                f,
                indent=2,
            )
        print(f"Saved snapshot comparison: {snap_path}")

    out_csv = CLEANED_DIR / "kickstarter_cleaned.csv"
    df_clean.to_csv(out_csv, index=False)
    print(f"Saved cleaned data: {out_csv} ({len(df_clean)} rows)")
    print(f"  Raw files: {raw_names}")
    print(f"  Scope: {FILTER_COUNTRY} + {FILTER_CURRENCY}")

    data_dict = build_data_dictionary(df_clean, cleaning_notes, raw_names)
    dict_path = CLEANED_DIR / "data_dictionary.json"
    with open(dict_path, "w", encoding="utf-8") as f:
        json.dump(data_dict, f, indent=2)
    print(f"Saved data dictionary: {dict_path}")


if __name__ == "__main__":
    main()
