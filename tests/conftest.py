import sys
from pathlib import Path
import os
from contextlib import contextmanager

import pyodbc
import pytest


ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

os.environ.setdefault("APP_ENV", "development")
os.environ.setdefault("JWT_SECRET_KEY", "test-only-secret-key")


def get_integration_db_conn_str() -> str | None:
    return os.getenv("TEST_DB_CONN_STR") or None


@contextmanager
def integration_db_cursor():
    conn_str = get_integration_db_conn_str()
    if not conn_str:
        pytest.skip("TEST_DB_CONN_STR nao configurada; testes de integracao com banco real ignorados.")

    try:
        conn = pyodbc.connect(conn_str, autocommit=False, timeout=30)
    except pyodbc.Error as exc:
        pytest.skip(f"Nao foi possivel conectar ao banco de integracao: {exc}")

    cur = conn.cursor()
    try:
        cur.execute("SET NOCOUNT ON;")
        yield conn, cur
    finally:
        conn.rollback()
        cur.close()
        conn.close()
