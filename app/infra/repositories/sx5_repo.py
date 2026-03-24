from __future__ import annotations

from app.infra.db import fetchall_dict, fetchone_dict
from app.core.exceptions import BusinessError


def sx5_listar_tx(cur, filial: str, tabela: str, ativos: bool = True):
    sql = """
        SELECT *
        FROM dbo.SX5_TABELAS
        WHERE X5_FILIAL=? AND X5_TABELA=?
          AND (D_E_L_E_T_ IS NULL OR D_E_L_E_T_ <> '*')
    """
    params: list = [filial, tabela]
    if ativos:
        sql += " AND X5_ATIVO=1"
    sql += " ORDER BY X5_CHAVE"
    cur.execute(sql, tuple(params))
    return fetchall_dict(cur)


def sx5_obter_tx(cur, filial: str, tabela: str, chave: str):
    cur.execute(
        """
        SELECT *
        FROM dbo.SX5_TABELAS
        WHERE X5_FILIAL=? AND X5_TABELA=? AND X5_CHAVE=?
          AND (D_E_L_E_T_ IS NULL OR D_E_L_E_T_ <> '*')
        """,
        (filial, tabela, chave),
    )
    return fetchone_dict(cur)


def sx5_criar_tx(cur, filial: str, tabela: str, chave: str, descr: str, ativo: bool = True) -> None:
    existe = sx5_obter_tx(cur, filial, tabela, chave)
    if existe:
        raise BusinessError("Registro SX5 já existe")
    cur.execute(
        """
        INSERT INTO dbo.SX5_TABELAS
          (X5_FILIAL, X5_TABELA, X5_CHAVE, X5_DESCR, X5_ATIVO)
        VALUES (?, ?, ?, ?, ?)
        """,
        (filial, tabela, chave, descr, 1 if ativo else 0),
    )


def sx5_atualizar_tx(cur, filial: str, tabela: str, chave: str, descr: str | None, ativo: bool | None):
    atual = sx5_obter_tx(cur, filial, tabela, chave)
    if not atual:
        raise BusinessError("Registro SX5 não encontrado")

    descr2 = descr if descr is not None else atual.get("X5_DESCR")
    ativo2 = atual.get("X5_ATIVO") if ativo is None else (1 if ativo else 0)

    cur.execute(
        """
        UPDATE dbo.SX5_TABELAS
        SET X5_DESCR=?, X5_ATIVO=?
        WHERE X5_FILIAL=? AND X5_TABELA=? AND X5_CHAVE=?
        """,
        (descr2, ativo2, filial, tabela, chave),
    )


def sx5_inativar_tx(cur, filial: str, tabela: str, chave: str) -> None:
    cur.execute(
        """
        UPDATE dbo.SX5_TABELAS
        SET X5_ATIVO=0,
            D_E_L_E_T_='*',
            R_E_C_D_E_L_=COALESCE(R_E_C_D_E_L_, R_E_C_N_O_)
        WHERE X5_FILIAL=? AND X5_TABELA=? AND X5_CHAVE=?
        """,
        (filial, tabela, chave),
    )
    if cur.rowcount == 0:
        raise BusinessError("Registro SX5 não encontrado")
