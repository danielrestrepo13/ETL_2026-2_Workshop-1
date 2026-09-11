"""
Usage:
    python src/main.py                 # full pipeline: extract -> transform -> model -> load -> queries
    python src/main.py --schema        # (re)create schema only
    python src/main.py --load          # extract + transform + model + load only
    python src/main.py --queries       # run the R1-R5 analytical queries only (DW must already be loaded)
"""

import argparse

from extract import extract
from transform import transform
from dimensional_model import build_dimensional_model
from load import load_data_warehouse, create_schema, ensure_database_exists
from db_config import get_engine
from queries import run_all_queries


def run_load_only() -> None:
    raw = extract()
    prepared = transform(raw)
    model = build_dimensional_model(prepared)
    load_data_warehouse(model)


def run_full_pipeline() -> None:
    run_load_only()
    run_all_queries()


def run_schema_only() -> None:
    ensure_database_exists()
    engine = get_engine()
    try:
        create_schema(engine)
    finally:
        engine.dispose()


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Workshop-1 ETL pipeline (MySQL)")
    parser.add_argument("--schema", action="store_true", help="Create schema only")
    parser.add_argument("--load", action="store_true", help="Run ETL and load the Data Warehouse only")
    parser.add_argument("--queries", action="store_true", help="Run the R1-R5 analytical queries only")
    args = parser.parse_args()

    if args.schema:
        run_schema_only()
    elif args.load:
        run_load_only()
    elif args.queries:
        run_all_queries()
    else:
        run_full_pipeline()