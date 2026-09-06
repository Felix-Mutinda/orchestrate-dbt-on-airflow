import urllib.request
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
DATA_DIR = REPO_ROOT / "var" / "data"
SEEDS_DIR = REPO_ROOT / "dbt_project" / "seeds"

# Latest available full month (May 2026)
DATASET_MONTH = "2026-05"
RAW_PARQUET_URL = f"https://d37ci6vzurychx.cloudfront.net/trip-data/yellow_tripdata_{DATASET_MONTH}.parquet"
ZONES_CSV_URL = "https://d37ci6vzurychx.cloudfront.net/misc/taxi_zone_lookup.csv"

RAW_PARQUET_PATH = DATA_DIR / f"yellow_tripdata_{DATASET_MONTH}.parquet"
ZONES_CSV_PATH = SEEDS_DIR / "taxi_zone_lookup.csv"


def main():
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    SEEDS_DIR.mkdir(parents=True, exist_ok=True)

    if not ZONES_CSV_PATH.exists():
        print(f"Downloading taxi zone lookup to {ZONES_CSV_PATH}...")
        urllib.request.urlretrieve(ZONES_CSV_URL, ZONES_CSV_PATH)

    if not RAW_PARQUET_PATH.exists():
        print(f"Downloading FULL {DATASET_MONTH} raw trips to {RAW_PARQUET_PATH}...")
        urllib.request.urlretrieve(RAW_PARQUET_URL, RAW_PARQUET_PATH)
        print("Download complete.")
    else:
        print(f"Dataset already exists at {RAW_PARQUET_PATH}. Skipping download.")

    print("Data fetch complete. Ready for DuckDB.")


if __name__ == "__main__":
    main()
