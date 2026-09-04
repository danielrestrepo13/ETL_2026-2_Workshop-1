import logging
from pathlib import Path

import pandas as pd
from sqlalchemy import text
from sqlalchemy.engine import Engine

from dimensional_model import DimensionalModel
from db_config import get_server_engine, get_engine, DB_NAME

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger(__name__)

PROJECT_ROOT = Path(__file__).resolve().parent.parent
SCHEMA_PATH = PROJECT_ROOT / "sql" / "create_tables.sql"

DIMENSION_TABLES = ["dim_date", "dim_technology", "dim_candidate_profile", "dim_country"]
FACT_TABLE = "fact_applications"


def ensure_database_exists() -> None:
    server_engine = get_server_engine()
    try:
        with server_engine.begin() as conn:
            conn.execute(text(f"CREATE DATABASE IF NOT EXISTS `{DB_NAME}` CHARACTER SET utf8mb4"))
        logger.info("Database '%s' is ready", DB_NAME)
    finally:
        server_engine.dispose()


def create_schema(engine: Engine) -> None:
    """Executes create_tables.sql (statement by statement) against the target database."""
    sql_script = SCHEMA_PATH.read_text(encoding="utf-8")


    code_lines = [
        line for line in sql_script.splitlines()
        if line.strip() and not line.strip().startswith("--")
    ]
    cleaned_script = "\n".join(code_lines)

    statements = [stmt.strip() for stmt in cleaned_script.split(";") if stmt.strip()]

    with engine.begin() as conn:
        for stmt in statements:
            conn.execute(text(stmt))
    logger.info("Schema created from %s (%d statements)", SCHEMA_PATH, len(statements))


def load_dimensions(engine: Engine, model: DimensionalModel) -> None:
    """Loads the four dimension tables"""
    model.dim_date.to_sql("dim_date", engine, if_exists="append", index=False)
    logger.info("Loaded DimDate: %d rows", len(model.dim_date))

    model.dim_technology.to_sql("dim_technology", engine, if_exists="append", index=False)
    logger.info("Loaded DimTechnology: %d rows", len(model.dim_technology))

    model.dim_candidate_profile.to_sql("dim_candidate_profile", engine, if_exists="append", index=False)
    logger.info("Loaded DimCandidateProfile: %d rows", len(model.dim_candidate_profile))

    model.dim_country.to_sql("dim_country", engine, if_exists="append", index=False)
    logger.info("Loaded DimCountry: %d rows", len(model.dim_country))


def load_fact(engine: Engine, model: DimensionalModel) -> None:
    """Loads FactApplications"""
    model.fact_applications.to_sql(FACT_TABLE, engine, if_exists="append", index=False, chunksize=5000)
    logger.info("Loaded FactApplications: %d rows", len(model.fact_applications))


def validate_load(engine: Engine, model: DimensionalModel) -> None:
    """
    Task 5 validation requirements:
    primary keys, foreign keys, referential integrity, record counts,
    absence of invalid dimension references.
    """
    with engine.connect() as conn:
        # 1. Foreign keys are enforced by InnoDB at DDL level (see create_tables.sql).
        #    Confirm they are actually registered in the information_schema.
        fk_count = conn.execute(text("""
            SELECT COUNT(*) FROM information_schema.TABLE_CONSTRAINTS
            WHERE CONSTRAINT_SCHEMA = :db
              AND TABLE_NAME = :tbl
              AND CONSTRAINT_TYPE = 'FOREIGN KEY'
        """), {"db": DB_NAME, "tbl": FACT_TABLE}).scalar()
        assert fk_count == 4, f"Expected 4 foreign keys on {FACT_TABLE}, found {fk_count}"
        logger.info("Foreign key constraints check: OK (%d FKs registered)", fk_count)

        # 2. Row counts match the in-memory model exactly
        counts = {
            "dim_date": len(model.dim_date),
            "dim_technology": len(model.dim_technology),
            "dim_candidate_profile": len(model.dim_candidate_profile),
            "dim_country": len(model.dim_country),
            "fact_applications": len(model.fact_applications),
        }
        for table, expected in counts.items():
            actual = conn.execute(text(f"SELECT COUNT(*) FROM {table};")).scalar()
            assert actual == expected, f"{table}: expected {expected}, found {actual}"
            logger.info("Row count OK - %s: %d rows", table, actual)

        # 3. No orphaned foreign keys (fact rows referencing a non-existent dimension row)
        orphan_query = text(f"""
            SELECT COUNT(*) FROM {FACT_TABLE} f
            LEFT JOIN dim_date d ON f.date_key = d.date_key
            LEFT JOIN dim_technology t ON f.technology_key = t.technology_key
            LEFT JOIN dim_candidate_profile p ON f.profile_key = p.profile_key
            LEFT JOIN dim_country c ON f.country_key = c.country_key
            WHERE d.date_key IS NULL
               OR t.technology_key IS NULL
               OR p.profile_key IS NULL
               OR c.country_key IS NULL;
        """)
        orphans = conn.execute(orphan_query).scalar()
        assert orphans == 0, f"{orphans} fact rows reference a missing dimension member"
        logger.info("Referential integrity check: OK (0 orphaned fact rows)")


def load_data_warehouse(model: DimensionalModel) -> None:
    """
    Orchestrates Task 5: ensure database exists, (re)create schema,
    load dimensions then fact, and validate the result.

    create_tables.sql already drops and recreates all five tables, so
    every run starts from a clean, consistent schema.
    """
    ensure_database_exists()
    engine = get_engine()
    try:
        create_schema(engine)
        load_dimensions(engine, model)
        load_fact(engine, model)
        validate_load(engine, model)
        logger.info("Data Warehouse successfully loaded into MySQL database '%s'", DB_NAME)
    finally:
        engine.dispose()


if __name__ == "__main__":
    from extract import extract
    from transform import transform
    from dimensional_model import build_dimensional_model

    raw = extract()
    prepared = transform(raw)
    dimensional_model = build_dimensional_model(prepared)
    load_data_warehouse(dimensional_model)
