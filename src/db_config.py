"""
db_config.py
------------
Centralizes the MySQL connection configuration for the Data Warehouse.

Credentials are never hardcoded: they are read from environment
variables, optionally loaded from a local .env file (see .env.example
for the expected variable names). This keeps secrets out of the
repository and out of version control (.env is listed in .gitignore).

Two engines are provided:
    - get_server_engine(): connects to the MySQL server WITHOUT
      selecting a database. Used once, to run `CREATE DATABASE IF NOT
      EXISTS` before the schema exists.
    - get_engine(): connects directly to the target database
      (DB_NAME). Used for schema creation, loading, and querying.
"""

import os

from dotenv import load_dotenv
from sqlalchemy import create_engine
from sqlalchemy.engine import Engine

load_dotenv()  # loads a local .env file if present; does nothing otherwise

DB_HOST = os.getenv("DB_HOST", "127.0.0.1")
DB_PORT = os.getenv("DB_PORT", "3306")
DB_NAME = os.getenv("DB_NAME", "recruitment_dw")
DB_USER = os.getenv("DB_USER", "workshop_user")
DB_PASSWORD = os.getenv("DB_PASSWORD", "workshop_pass")


def _build_url(include_database: bool) -> str:
    base = f"mysql+pymysql://{DB_USER}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}"
    if include_database:
        base += f"/{DB_NAME}"
    return base + "?charset=utf8mb4"


def get_server_engine(echo: bool = False) -> Engine:
    """Engine connected to the MySQL server, no database selected."""
    return create_engine(_build_url(include_database=False), echo=echo)


def get_engine(echo: bool = False) -> Engine:
    """Engine connected directly to DB_NAME (the Data Warehouse)."""
    return create_engine(_build_url(include_database=True), echo=echo)


if __name__ == "__main__":
    # Quick connectivity check: python src/db_config.py
    engine = get_server_engine()
    with engine.connect() as conn:
        version = conn.exec_driver_sql("SELECT VERSION();").scalar()
        print(f"Connected. MySQL server version: {version}")
        print(f"Target database (DB_NAME): {DB_NAME}")
