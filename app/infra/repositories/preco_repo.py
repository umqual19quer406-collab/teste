from datetime import date

from app.domain.errors import BusinessError
from app.infra.db import fetchall_dict, fetchone_dict


def _has_deleted_column(cur, table_name: str) -> bool:
    cur.execute(f"SELECT COL_LENGTH('{table_name}','D_E_L_E_T_') AS col")
    row = cur.fetchone()
    return bool(row and row[0] is not None)


def listar_tabelas_tx(cur, filial: str):
    sql = """
        SELECT ID, P0_FILIAL, P0_COD, P0_DESC, P0_ATIVA
        FROM dbo.PR0_TABELA
        WHERE P0_FILIAL=? AND P0_ATIVA=1
    """
    if _has_deleted_column(cur, "dbo.PR0_TABELA"):
        sql += " AND (D_E_L_E_T_ IS NULL OR D_E_L_E_T_ <> '*')"
    sql += " ORDER BY P0_COD"

    cur.execute(sql, (filial,))
    return fetchall_dict(cur)


def criar_tabela_tx(cur, filial: str, cod: str, desc: str) -> int:
    cur.execute(
        """
        INSERT INTO dbo.PR0_TABELA (P0_FILIAL, P0_COD, P0_DESC)
        VALUES (?, ?, ?);
        SELECT CAST(SCOPE_IDENTITY() AS INT) AS id;
        """,
        (filial, cod, desc),
    )
    return int(fetchone_dict(cur)["id"])


def definir_preco_tx(cur, filial: str, tabela_id: int, produto: str, preco: float, dt_ini: date):
    sql = """
        UPDATE dbo.PR1_PRECO
        SET P1_DTFIM = DATEADD(DAY, -1, ?)
        WHERE P1_FILIAL=? AND P1_TABELA_ID=? AND P1_PRODUTO=? AND P1_DTFIM IS NULL
    """
    if _has_deleted_column(cur, "dbo.PR1_PRECO"):
        sql += " AND (D_E_L_E_T_ IS NULL OR D_E_L_E_T_ <> '*')"

    cur.execute(sql, (dt_ini, filial, tabela_id, produto))

    cur.execute(
        """
        INSERT INTO dbo.PR1_PRECO
          (P1_FILIAL, P1_TABELA_ID, P1_PRODUTO, P1_PRECO, P1_DTINI)
        VALUES (?, ?, ?, ?, ?)
        """,
        (filial, tabela_id, produto, float(preco), dt_ini),
    )


def listar_precos_tabela_tx(cur, filial: str, tabela_id: int):
    sql = """
        SELECT ID, P1_FILIAL, P1_TABELA_ID, P1_PRODUTO, P1_PRECO, P1_DTINI, P1_DTFIM
        FROM dbo.PR1_PRECO
        WHERE P1_FILIAL=? AND P1_TABELA_ID=?
    """
    if _has_deleted_column(cur, "dbo.PR1_PRECO"):
        sql += " AND (D_E_L_E_T_ IS NULL OR D_E_L_E_T_ <> '*')"
    sql += " ORDER BY P1_PRODUTO, P1_DTINI DESC"

    cur.execute(sql, (filial, tabela_id))
    return fetchall_dict(cur)


def buscar_preco_vigente_tx(cur, filial: str, tabela_id: int, produto: str, data: date):
    sql = """
        SELECT TOP 1 P1_PRECO
        FROM dbo.PR1_PRECO
        WHERE P1_FILIAL=? AND P1_TABELA_ID=? AND P1_PRODUTO=?
          AND P1_DTINI <= ?
          AND (P1_DTFIM IS NULL OR P1_DTFIM >= ?)
    """
    if _has_deleted_column(cur, "dbo.PR1_PRECO"):
        sql += " AND (D_E_L_E_T_ IS NULL OR D_E_L_E_T_ <> '*')"
    sql += " ORDER BY P1_DTINI DESC"

    cur.execute(sql, (filial, tabela_id, produto, data, data))
    row = fetchone_dict(cur)
    if not row:
        raise BusinessError("Preco nao encontrado")
    return float(row["P1_PRECO"])
