from contextlib import contextmanager
from contextvars import ContextVar
from typing import Any, Dict, Iterator, List, Optional, Tuple

import pyodbc

from app.core import settings

_current_user: ContextVar[str | None] = ContextVar("db_current_user", default=None)
_current_request_id: ContextVar[str | None] = ContextVar("db_request_id", default=None)
_current_request_path: ContextVar[str | None] = ContextVar("db_request_path", default=None)


def set_current_user(login: str | None) -> None:
    _current_user.set((login or "").strip() or None)


def get_current_user_ctx() -> str | None:
    return _current_user.get()


def set_current_request(request_id: str | None, path: str | None) -> None:
    _current_request_id.set((request_id or "").strip() or None)
    _current_request_path.set((path or "").strip() or None)


def get_current_request_id() -> str | None:
    return _current_request_id.get()


def get_current_request_path() -> str | None:
    return _current_request_path.get()


def get_connection() -> pyodbc.Connection:
    return pyodbc.connect(settings.DB_CONN_STR, autocommit=False, timeout=30)


@contextmanager
def db_transaction() -> Iterator[Tuple[pyodbc.Connection, pyodbc.Cursor]]:
    conn = get_connection()
    cur = conn.cursor()
    try:
        cur.execute("SET NOCOUNT ON;")
        user = get_current_user_ctx()
        if user:
            cur.execute("EXEC sp_set_session_context @key=N'app_user', @value=?", (user,))
        req_id = get_current_request_id()
        req_path = get_current_request_path()
        if req_id:
            cur.execute("EXEC sp_set_session_context @key=N'app_req_id', @value=?", (req_id,))
        if req_path:
            cur.execute("EXEC sp_set_session_context @key=N'app_path', @value=?", (req_path,))
        yield conn, cur
        conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        try:
            cur.close()
        finally:
            conn.close()


def fetchone_dict(cur: pyodbc.Cursor) -> Optional[Dict[str, Any]]:
    row = cur.fetchone()
    if row is None:
        return None
    if cur.description is None:
        raise RuntimeError("fetchone_dict chamado sem SELECT (cur.description=None)")
    cols = [c[0] for c in cur.description]
    return dict(zip(cols, row))


def fetchall_dict(cur: pyodbc.Cursor) -> List[Dict[str, Any]]:
    rows = cur.fetchall()
    if cur.description is None:
        raise RuntimeError("fetchall_dict chamado sem SELECT (cur.description=None)")
    cols = [c[0] for c in cur.description]
    return [dict(zip(cols, r)) for r in rows]
