"""
extract.py
----------
Task 3 - 10.1 Extract

Responsibility:
    - Read the raw source file (candidates.csv).
    - Preserve the original source file (never overwritten).
    - Load the source data into a Pandas DataFrame with no business
      transformations applied (no derived columns, no filtering, no
      hiring-rule logic here).

The candidates.csv file uses ';' as the field separator, so it is
made explicit rather than relying on Pandas' default ','.
"""

from pathlib import Path
import logging

import pandas as pd

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger(__name__)

RAW_DATA_PATH = Path(__file__).resolve().parent.parent / "data" / "raw" / "candidates.csv"


def extract(source_path: Path = RAW_DATA_PATH) -> pd.DataFrame:
    """
    Read the raw candidates dataset into a DataFrame.

    Parameters
    ----------
    source_path : Path
        Location of the raw CSV file. Defaults to data/raw/candidates.csv.

    Returns
    -------
    pd.DataFrame
        Raw, untransformed candidate application records.
    """
    if not source_path.exists():
        raise FileNotFoundError(f"Source file not found at {source_path}")

    logger.info("Extracting raw data from %s", source_path)

    df = pd.read_csv(
        source_path,
        sep=";",
        encoding="utf-8",
        dtype={
            "First Name": "string",
            "Last Name": "string",
            "Email": "string",
            "Country": "string",
            "Seniority": "string",
            "Technology": "string",
        },
    )

    logger.info("Extracted %d rows and %d columns", df.shape[0], df.shape[1])
    return df


if __name__ == "__main__":
    raw_df = extract()
    print(raw_df.head())
    print(raw_df.dtypes)
