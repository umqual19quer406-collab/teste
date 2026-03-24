from app.domain.errors import BusinessError
from app.infra.db import fetchall_dict, fetchone_dict


def _has_column(cur, table_name: str, column_name: str) -> bool:
    cur.execute(f"SELECT COL_LENGTH('{table_name}', '{column_name}') AS col")
    row = cur.fetchone()
    return bool(row and row[0] is not None)


def sa1_criar_tx(
    cur,
    filial: str,
    cod: str,
    nome: str,
    doc: str | None,
    email: str | None,
    tel: str | None,
    end: str | None,
    mun: str | None,
    uf: str | None,
    cep: str | None,
    tabela_id: int | None,
) -> int:
    cur.execute(
        """
        INSERT INTO dbo.SA1_CLIENTES
          (A1_FILIAL, A1_COD, A1_NOME, A1_DOC, A1_EMAIL, A1_TEL, A1_END, A1_MUN, A1_UF, A1_CEP,
           A1_TABELA_ID, A1_ATIVO)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 1);
        SELECT CAST(SCOPE_IDENTITY() AS INT) AS id;
    """,
        (filial, cod, nome, doc, email, tel, end, mun, uf, cep, tabela_id),
    )
    return int(fetchone_dict(cur)["id"])


def sa1_listar_tx(cur, filial: str, ativo: bool = True, q: str | None = None):
    sql = """
      SELECT
        c.*,
        t.P0_COD AS TABELA_COD,
        t.P0_DESC AS TABELA_DESC
      FROM dbo.SA1_CLIENTES c
      LEFT JOIN dbo.PR0_TABELA t ON t.ID = c.A1_TABELA_ID
      WHERE c.A1_FILIAL = ?
        AND (c.D_E_L_E_T_ IS NULL OR c.D_E_L_E_T_ <> '*')
    """
    params = [filial]
    if ativo:
        sql += " AND c.A1_ATIVO = 1"
    if q:
        sql += " AND (c.A1_NOME LIKE ? OR c.A1_COD LIKE ? OR c.A1_DOC LIKE ?)"
        like = f"%{q}%"
        params.extend([like, like, like])
    if _has_column(cur, "dbo.SA1_CLIENTES", "ID"):
        sql += " ORDER BY c.ID DESC"
    else:
        sql += " ORDER BY c.A1_COD DESC"
    cur.execute(sql, tuple(params))
    return fetchall_dict(cur)


def sa1_obter_tx(cur, filial: str, cod: str):
    cur.execute(
        """
        SELECT
          c.*,
          t.P0_COD AS TABELA_COD,
          t.P0_DESC AS TABELA_DESC
        FROM dbo.SA1_CLIENTES c
        LEFT JOIN dbo.PR0_TABELA t ON t.ID = c.A1_TABELA_ID
        WHERE c.A1_FILIAL=? AND c.A1_COD=?
          AND (c.D_E_L_E_T_ IS NULL OR c.D_E_L_E_T_ <> '*')
    """,
        (filial, cod),
    )
    return fetchone_dict(cur)


def sa1_set_tabela_tx(cur, filial: str, cod: str, tabela_id: int | None):
    cur.execute(
        """
        UPDATE dbo.SA1_CLIENTES
        SET A1_TABELA_ID = ?
        WHERE A1_FILIAL=? AND A1_COD=? AND A1_ATIVO=1
    """,
        (tabela_id, filial, cod),
    )
    if cur.rowcount == 0:
        raise BusinessError("Cliente não encontrado/ativo")


def sa1_inativar_tx(cur, filial: str, cod: str):
    cur.execute(
        """
        UPDATE dbo.SA1_CLIENTES
        SET A1_ATIVO=0
        WHERE A1_FILIAL=? AND A1_COD=? AND A1_ATIVO=1
    """,
        (filial, cod),
    )
    if cur.rowcount == 0:
        raise BusinessError("Cliente não encontrado/ativo")


def sa2_criar_tx(
    cur,
    filial: str,
    cod: str,
    nome: str,
    doc: str | None,
    email: str | None,
    tel: str | None,
    end: str | None,
    mun: str | None,
    uf: str | None,
    cep: str | None,
) -> int:
    cur.execute(
        """
        INSERT INTO dbo.SA2_FORNECEDORES
          (A2_FILIAL, A2_COD, A2_NOME, A2_DOC, A2_EMAIL, A2_TEL, A2_END, A2_MUN, A2_UF, A2_CEP,
           A2_ATIVO)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 1);
        SELECT CAST(SCOPE_IDENTITY() AS INT) AS id;
    """,
        (filial, cod, nome, doc, email, tel, end, mun, uf, cep),
    )
    return int(fetchone_dict(cur)["id"])


def sa2_listar_tx(cur, filial: str, ativo: bool = True, q: str | None = None):
    sql = "SELECT * FROM dbo.SA2_FORNECEDORES WHERE A2_FILIAL=? AND (D_E_L_E_T_ IS NULL OR D_E_L_E_T_ <> '*')"
    params = [filial]
    if ativo:
        sql += " AND A2_ATIVO=1"
    if q:
        sql += " AND (A2_NOME LIKE ? OR A2_COD LIKE ? OR A2_DOC LIKE ?)"
        like = f"%{q}%"
        params.extend([like, like, like])
    if _has_column(cur, "dbo.SA2_FORNECEDORES", "ID"):
        sql += " ORDER BY ID DESC"
    else:
        sql += " ORDER BY A2_COD DESC"
    cur.execute(sql, tuple(params))
    return fetchall_dict(cur)


def sa2_obter_tx(cur, filial: str, cod: str):
    cur.execute(
        """
        SELECT * FROM dbo.SA2_FORNECEDORES
        WHERE A2_FILIAL=? AND A2_COD=?
          AND (D_E_L_E_T_ IS NULL OR D_E_L_E_T_ <> '*')
    """,
        (filial, cod),
    )
    return fetchone_dict(cur)


def sa2_inativar_tx(cur, filial: str, cod: str):
    cur.execute(
        """
        UPDATE dbo.SA2_FORNECEDORES
        SET A2_ATIVO=0
        WHERE A2_FILIAL=? AND A2_COD=? AND A2_ATIVO=1
    """,
        (filial, cod),
    )
    if cur.rowcount == 0:
        raise BusinessError("Fornecedor não encontrado/ativo")
