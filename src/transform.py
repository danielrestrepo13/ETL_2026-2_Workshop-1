"""
transform.py
------------
Task 3 - 10.2 Data Preparation and 10.3 Business Transformation

Responsibility:
    - Correct data types (Application Date -> datetime).
    - Standardize categorical text (trim whitespace).
    - Handle missing values / duplicates if required (documented below).
    - Apply the HIRED business rule.
    - Create derived attributes required by R1-R5 (yoe_band, score_gap).

Preparation decisions (documented per workshop requirement 10.2):
    1. `Application Date` is cast from string to datetime64.
    2. Text columns (Country, Seniority, Technology) are stripped of
       leading/trailing whitespace to avoid duplicate dimension members
       caused only by formatting (e.g. "Norway " vs "Norway").
    3. No missing-value imputation is performed: profiling (Task 1)
       confirmed 0 nulls across all columns.
    4. No row deduplication is performed: profiling confirmed 0 fully
       duplicated rows. Rows sharing an email (repeat applicants) are
       kept, since the declared grain is "one application", not
       "one candidate".
    5. `YOE` is bucketed into experience bands for `DimCandidateProfile`
       (supports R3), because YOE is continuous and not analytically
       useful as a raw dimension attribute.
"""

import logging

import pandas as pd

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger(__name__)

# Business rule thresholds (Section 5.1 of the workshop)
HIRE_SCORE_THRESHOLD = 7

# YOE banding used by DimCandidateProfile (supports R3)
YOE_BANDS = [
    (0, 2, "Entry (0-2)"),
    (3, 5, "Junior (3-5)"),
    (6, 9, "Mid (6-9)"),
    (10, 15, "Senior (10-15)"),
    (16, 999, "Expert (16+)"),
]


def _yoe_to_band(yoe: int) -> str:
    for low, high, label in YOE_BANDS:
        if low <= yoe <= high:
            return label
    return "Unknown"


def prepare(df: pd.DataFrame) -> pd.DataFrame:
    """
    Task 10.2 - Data Preparation.
    Applies only the preparation required by the data and the analytical
    model. No business logic (hiring rule) is applied here.
    """
    df = df.copy()

    before_rows = len(df)

    # 1. Correct data types
    df["Application Date"] = pd.to_datetime(df["Application Date"], errors="coerce")
    invalid_dates = df["Application Date"].isna().sum()
    if invalid_dates:
        logger.warning("%d rows have an unparseable Application Date and will be dropped", invalid_dates)
        df = df.dropna(subset=["Application Date"])

    # 2. Standardize categorical text (trim whitespace only - values are
    #    already clean per profiling, this guards against future data drift)
    for col in ["Country", "Seniority", "Technology", "First Name", "Last Name", "Email"]:
        df[col] = df[col].str.strip()

    # 3. Missing values: none found in profiling, but guard defensively
    #    for any column required by the model.
    required_cols = [
        "Application Date", "Country", "Seniority", "Technology",
        "YOE", "Code Challenge Score", "Technical Interview Score",
    ]
    missing_before = df[required_cols].isnull().any(axis=1).sum()
    if missing_before:
        logger.warning("%d rows missing required fields and will be dropped", missing_before)
        df = df.dropna(subset=required_cols)

    # 4. Duplicates: profiling found 0 fully duplicated rows; guard anyway.
    dup_count = df.duplicated().sum()
    if dup_count:
        logger.warning("%d fully duplicated rows found and will be dropped", dup_count)
        df = df.drop_duplicates()

    logger.info("Data preparation: %d -> %d rows", before_rows, len(df))
    return df.reset_index(drop=True)


def apply_business_rules(df: pd.DataFrame) -> pd.DataFrame:
    """
    Task 10.3 - Business Transformation.
    Implements the HIRED rule and the derived attributes needed by R1-R5.
    """
    df = df.copy()

    # Hiring outcome (R1, R2, R3, R4, R5)
    df["is_hired"] = (
        (df["Code Challenge Score"] >= HIRE_SCORE_THRESHOLD)
        & (df["Technical Interview Score"] >= HIRE_SCORE_THRESHOLD)
    ).astype(int)

    # Score gap between the two assessments (R5)
    df["score_gap"] = df["Technical Interview Score"] - df["Code Challenge Score"]

    # YOE band for DimCandidateProfile (R3)
    df["yoe_band"] = df["YOE"].apply(_yoe_to_band)

    hire_rate = df["is_hired"].mean() * 100
    logger.info("Business rule applied: %d hired / %d total (%.2f%%)", df["is_hired"].sum(), len(df), hire_rate)

    return df


def transform(raw_df: pd.DataFrame) -> pd.DataFrame:
    """Full transformation pipeline: prepare -> apply business rules."""
    prepared = prepare(raw_df)
    transformed = apply_business_rules(prepared)
    return transformed


if __name__ == "__main__":
    from extract import extract

    raw = extract()
    result = transform(raw)
    print(result.head())
    print(result[["is_hired", "score_gap", "yoe_band"]].describe(include="all"))
