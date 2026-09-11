import os

from dotenv import load_dotenv
from sqlalchemy import create_engine
from sqlalchemy.engine import Engine

load_dotenv()

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


def get_server_engine() -> Engine:
    return create_engine(_build_url(include_database=False))


def get_engine() -> Engine:
    return create_engine(_build_url(include_database=True))


if __name__ == "__main__":
    engine = get_server_engine()
    with engine.connect() as conn:
        version = conn.exec_driver_sql("SELECT VERSION();").scalar()
        print(f"Connected. MySQL server version: {version}")
        print(f"Target database (DB_NAME): {DB_NAME}")