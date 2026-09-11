import logging
from dataclasses import dataclass

import pandas as pd

from transform import YOE_BANDS

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger(__name__)


@dataclass
class DimensionalModel:
    """Container for the four dimension tables and the fact table."""
    dim_date: pd.DataFrame
    dim_technology: pd.DataFrame
    dim_candidate_profile: pd.DataFrame
    dim_country: pd.DataFrame
    fact_applications: pd.DataFrame


def build_dim_date(df: pd.DataFrame) -> pd.DataFrame:
    """DimDate - supports R1 (hiring trends over time)."""
    dates = pd.Series(df["Application Date"].dt.normalize().unique()).sort_values()
    dim = pd.DataFrame({"full_date": dates})
    dim["date_key"] = dim["full_date"].dt.strftime("%Y%m%d").astype(int)
    dim["day"] = dim["full_date"].dt.day
    dim["month"] = dim["full_date"].dt.month
    dim["month_name"] = dim["full_date"].dt.strftime("%B")
    dim["quarter"] = dim["full_date"].dt.quarter
    dim["year"] = dim["full_date"].dt.year
    dim = dim[["date_key", "full_date", "day", "month", "month_name", "quarter", "year"]]
    dim = dim.sort_values("date_key").reset_index(drop=True)
    logger.info("DimDate: %d distinct dates", len(dim))
    return dim


def _build_lookup_dimension(df: pd.DataFrame, source_col: str, key_col: str, name_col: str) -> pd.DataFrame:
    values = sorted(df[source_col].unique())
    dim = pd.DataFrame({name_col: values})
    dim.insert(0, key_col, range(1, len(dim) + 1))
    return dim


def build_dim_technology(df: pd.DataFrame) -> pd.DataFrame:
    """DimTechnology - supports R2 (technology comparison)."""
    dim = _build_lookup_dimension(df, "Technology", "technology_key", "technology_name")
    logger.info("DimTechnology: %d technologies", len(dim))
    return dim


def build_dim_country(df: pd.DataFrame) -> pd.DataFrame:
    """DimCountry - supports R4 (geographic recruitment analysis)."""
    dim = _build_lookup_dimension(df, "Country", "country_key", "country_name")
    logger.info("DimCountry: %d countries", len(dim))
    return dim


def build_dim_candidate_profile(df: pd.DataFrame) -> pd.DataFrame:
    """DimCandidateProfile - supports R3 (seniority + years of experience)."""
    combos = (
        df[["Seniority", "yoe_band"]]
        .drop_duplicates()
        .sort_values(["Seniority", "yoe_band"])
        .reset_index(drop=True)
    )

    # Reuses the same YOE_BANDS defined in transform.py, so the band
    # boundaries only live in one place in the whole pipeline.
    band_bounds = {label: (low, high) for low, high, label in YOE_BANDS}
    combos["yoe_min"] = combos["yoe_band"].map(lambda b: band_bounds[b][0])
    combos["yoe_max"] = combos["yoe_band"].map(lambda b: band_bounds[b][1])

    combos.insert(0, "profile_key", range(1, len(combos) + 1))
    combos = combos.rename(columns={"Seniority": "seniority"})
    combos = combos[["profile_key", "seniority", "yoe_band", "yoe_min", "yoe_max"]]

    logger.info("DimCandidateProfile: %d seniority/experience combinations", len(combos))
    return combos


def build_fact_applications(
    df: pd.DataFrame,
    dim_date: pd.DataFrame,
    dim_technology: pd.DataFrame,
    dim_candidate_profile: pd.DataFrame,
    dim_country: pd.DataFrame,
) -> pd.DataFrame:
    """FactApplications - grain: one row per candidate application."""
    fact = df.copy()
    fact["date_key"] = fact["Application Date"].dt.strftime("%Y%m%d").astype(int)

    fact = fact.merge(dim_technology, left_on="Technology", right_on="technology_name", how="left")
    fact = fact.merge(dim_country, left_on="Country", right_on="country_name", how="left")
    fact = fact.merge(
        dim_candidate_profile[["profile_key", "seniority", "yoe_band"]],
        left_on=["Seniority", "yoe_band"],
        right_on=["seniority", "yoe_band"],
        how="left",
    )

    # Referential integrity check before finalizing the fact table
    fk_cols = ["date_key", "technology_key", "country_key", "profile_key"]
    unmatched = fact[fk_cols].isnull().any(axis=1).sum()
    if unmatched:
        raise ValueError(
            f"{unmatched} fact rows could not be mapped to a valid dimension "
            "surrogate key. Aborting load to avoid orphaned foreign keys."
        )

    fact["application_id"] = range(1, len(fact) + 1)

    fact = fact[[
        "application_id", "date_key", "technology_key", "profile_key", "country_key",
        "Code Challenge Score", "Technical Interview Score", "score_gap", "is_hired",
    ]].rename(columns={
        "Code Challenge Score": "code_challenge_score",
        "Technical Interview Score": "technical_interview_score",
    })

    for col in ["date_key", "technology_key", "profile_key", "country_key"]:
        fact[col] = fact[col].astype(int)

    logger.info("FactApplications: %d rows, %d columns", *fact.shape)
    return fact


def build_dimensional_model(transformed_df: pd.DataFrame) -> DimensionalModel:
    """Orchestrates Task 4: builds all dimensions and the fact table."""
    dim_date = build_dim_date(transformed_df)
    dim_technology = build_dim_technology(transformed_df)
    dim_country = build_dim_country(transformed_df)
    dim_candidate_profile = build_dim_candidate_profile(transformed_df)

    fact_applications = build_fact_applications(
        transformed_df, dim_date, dim_technology, dim_candidate_profile, dim_country
    )

    return DimensionalModel(
        dim_date=dim_date,
        dim_technology=dim_technology,
        dim_candidate_profile=dim_candidate_profile,
        dim_country=dim_country,
        fact_applications=fact_applications,
    )


if __name__ == "__main__":
    from extract import extract
    from transform import transform

    raw = extract()
    prepared = transform(raw)
    model = build_dimensional_model(prepared)

    print("DimDate:\n", model.dim_date.head())
    print("\nDimTechnology:\n", model.dim_technology.head())
    print("\nDimCandidateProfile:\n", model.dim_candidate_profile)
    print("\nDimCountry:\n", model.dim_country.head())
    print("\nFactApplications:\n", model.fact_applications.head())