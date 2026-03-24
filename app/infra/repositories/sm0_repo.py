from __future__ import annotations

from app.infra.db import fetchone_dict, fetchall_dict
from app.core.exceptions import BusinessError


def sm0_obter_series_tx(cur, filial: str) -> dict:
    cur.execute(
        """
        SELECT TOP 1 M0_FILIAL, M0_SERIE_NF, M0_SERIE_AR, M0_SERIE_AP
        FROM dbo.SM0_EMPRESA
        WHERE M0_FILIAL=?
        """,
        (filial,),
    )
    return fetchone_dict(cur) or {}


def sm0_existe_tx(cur, filial: str) -> bool:
    cur.execute(
        """
        SELECT 1
        FROM dbo.SM0_EMPRESA
        WHERE M0_FILIAL=?
          AND (D_E_L_E_T_ IS NULL OR D_E_L_E_T_ <> '*')
        """,
        (filial,),
    )
    return cur.fetchone() is not None


def sm0_listar_tx(cur):
    cur.execute(
        """
        SELECT M0_FILIAL, M0_SERIE_NF, M0_SERIE_AR, M0_SERIE_AP
        FROM dbo.SM0_EMPRESA
        WHERE (D_E_L_E_T_ IS NULL OR D_E_L_E_T_ <> '*')
        ORDER BY M0_FILIAL
        """
    )
    return fetchall_dict(cur)


def sm0_criar_tx(
    cur,
    filial: str,
    serie_nf: str | None,
    serie_ar: str | None,
    serie_ap: str | None,
):
    cur.execute(
        "SELECT 1 FROM dbo.SM0_EMPRESA WHERE M0_FILIAL=?",
        (filial,),
    )
    if cur.fetchone() is not None:
        raise BusinessError("Filial já existe")
    cur.execute(
        """
        INSERT INTO dbo.SM0_EMPRESA (M0_FILIAL, M0_SERIE_NF, M0_SERIE_AR, M0_SERIE_AP)
        VALUES (?, ?, ?, ?)
        """,
        (filial, serie_nf, serie_ar, serie_ap),
    )


def sm0_inativar_tx(cur, filial: str):
    cur.execute(
        """
        UPDATE dbo.SM0_EMPRESA
        SET D_E_L_E_T_='*',
            R_E_C_D_E_L_=COALESCE(R_E_C_D_E_L_, R_E_C_N_O_)
        WHERE M0_FILIAL=?
          AND (D_E_L_E_T_ IS NULL OR D_E_L_E_T_ <> '*')
        """,
        (filial,),
    )
    if cur.rowcount == 0:
        raise BusinessError("Filial não encontrada")


def sm0_definir_series_tx(cur, filial: str, serie_nf: str | None, serie_ar: str | None, serie_ap: str | None):
    atual = sm0_obter_series_tx(cur, filial)
    if not atual:
        raise BusinessError("Filial não encontrada em SM0_EMPRESA")

    cur.execute(
        """
        UPDATE dbo.SM0_EMPRESA
        SET M0_SERIE_NF = COALESCE(?, M0_SERIE_NF),
            M0_SERIE_AR = COALESCE(?, M0_SERIE_AR),
            M0_SERIE_AP = COALESCE(?, M0_SERIE_AP)
        WHERE M0_FILIAL=?
        """,
        (serie_nf, serie_ar, serie_ap, filial),
    )
