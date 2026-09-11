"""

Task 3 - 10.2 Data Preparation and 10.3 Business Transformation
Responsibility:
    - Correct data types (Application Date = datetime).
    - Standardize categorical text (trim whitespace).
    - Handle missing values / duplicates if required.
    - Apply the HIRED business rule.
    - Create derived attributes required by R1-R5 (yoe_band, score_gap).
"""

import logging

import pandas as pd

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger(__name__)

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
    """Task 10.2 - Data Preparation."""
    df = df.copy()
    before_rows = len(df)

    # Correct data types
    df["Application Date"] = pd.to_datetime(df["Application Date"], errors="coerce")
    invalid_dates = df["Application Date"].isna().sum()
    if invalid_dates:
        logger.warning("%d rows have an unparseable Application Date and will be dropped", invalid_dates)
        df = df.dropna(subset=["Application Date"])

    # Standardize categorical text
    for col in ["Country", "Seniority", "Technology", "First Name", "Last Name", "Email"]:
        df[col] = df[col].str.strip()

    # Missing values (none found in profiling, guarded defensively)
    required_cols = [
        "Application Date", "Country", "Seniority", "Technology",
        "YOE", "Code Challenge Score", "Technical Interview Score",
    ]
    missing_before = df[required_cols].isnull().any(axis=1).sum()
    if missing_before:
        logger.warning("%d rows missing required fields and will be dropped", missing_before)
        df = df.dropna(subset=required_cols)

    # Duplicates (0 found in profiling, guarded defensively)
    dup_count = df.duplicated().sum()
    if dup_count:
        logger.warning("%d fully duplicated rows found and will be dropped", dup_count)
        df = df.drop_duplicates()

    logger.info("Data preparation: %d -> %d rows", before_rows, len(df))
    return df.reset_index(drop=True)


def apply_business_rules(df: pd.DataFrame) -> pd.DataFrame:
    """Task 10.3 - Business Transformation."""
    df = df.copy()

    # Hiring outcome (R1-R5)
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
    return apply_business_rules(prepare(raw_df))


if __name__ == "__main__":
    from extract import extract

    raw = extract()
    result = transform(raw)
    print(result.head())
    print(result[["is_hired", "score_gap", "yoe_band"]].describe(include="all"))