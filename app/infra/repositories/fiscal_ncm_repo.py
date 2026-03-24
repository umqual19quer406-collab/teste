from app.infra.db import fetchone_dict, fetchall_dict
from app.core.exceptions import BusinessError
from app.infra.repositories.sx5_repo import sx5_obter_tx


def ncm_obter_tx(cur, filial: str, ncm: str) -> dict | None:
    cur.execute(
        """
        SELECT TOP 1 *
        FROM dbo.SF8_FISCAL_NCM
        WHERE F8_FILIAL=? AND F8_NCM=?
          AND F8_ATIVO=1
          AND (D_E_L_E_T_ IS NULL OR D_E_L_E_T_ <> '*')
        """,
        (filial, str(ncm).strip()),
    )
    return fetchone_dict(cur)


def ncm_listar_tx(cur, filial: str, ativos: bool = True):
    sql = """
        SELECT *
        FROM dbo.SF8_FISCAL_NCM
        WHERE F8_FILIAL=?
          AND (D_E_L_E_T_ IS NULL OR D_E_L_E_T_ <> '*')
    """
    params: list = [filial]
    if ativos:
        sql += " AND F8_ATIVO=1"
    sql += " ORDER BY F8_NCM"
    cur.execute(sql, tuple(params))
    return fetchall_dict(cur)


def ncm_upsert_tx(
    cur,
    filial: str,
    ncm: str,
    cfop: str,
    icms: float | None,
    ipi: float | None,
    ativo: bool = True,
):
    ncm = (ncm or "").strip()
    cfop = (cfop or "").strip()
    if not ncm:
        raise BusinessError("NCM é obrigatório")
    if not cfop:
        raise BusinessError("CFOP é obrigatório")
    if sx5_obter_tx(cur, filial=filial, tabela="CFOP", chave=cfop) is None:
        raise BusinessError("CFOP não cadastrado no SX5 (tabela CFOP)")

    cur.execute(
        """
        SELECT ID FROM dbo.SF8_FISCAL_NCM
        WHERE F8_FILIAL=? AND F8_NCM=?
          AND (D_E_L_E_T_ IS NULL OR D_E_L_E_T_ <> '*')
        """,
        (filial, ncm),
    )
    row = cur.fetchone()
    if row:
        cur.execute(
            """
            UPDATE dbo.SF8_FISCAL_NCM
            SET F8_CFOP=?, F8_ICMS=?, F8_IPI=?, F8_ATIVO=?
            WHERE F8_FILIAL=? AND F8_NCM=?
            """,
            (cfop, icms, ipi, 1 if ativo else 0, filial, ncm),
        )
        return

    cur.execute(
        """
        INSERT INTO dbo.SF8_FISCAL_NCM
          (F8_FILIAL, F8_NCM, F8_CFOP, F8_ICMS, F8_IPI, F8_ATIVO)
        VALUES (?, ?, ?, ?, ?, ?)
        """,
        (filial, ncm, cfop, icms, ipi, 1 if ativo else 0),
    )
