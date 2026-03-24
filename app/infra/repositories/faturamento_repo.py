from __future__ import annotations

from datetime import datetime
from app.infra.db import fetchone_dict
from app.infra.repositories.sx6_repo import sx6_next_tx
from app.infra.repositories.serie_repo import resolve_serie_tx, validar_serie_tx


def _nf_doc_from_id(nf_id: int) -> str:
    # Protheus-like: número sequencial como string (zero-padded)
    return f"{int(nf_id):09d}"


def sf2_criar_tx(
    cur,
    filial: str,
    pedido_id: int | None,
    cliente: str | None,
    cliente_cod: str | None,
    valor_total: float,
    icms: float,
    ipi: float,
    total_bruto: float,
    tes_cod: str,
    cfop: str | None = None,
    doc: str | None = None,
    serie: str | None = None,
    status: str = "EMITIDA",
    origem: str = "VENDA",
    pis: float = 0.0,
    cofins: float = 0.0,
    icms_st: float = 0.0,
    difal: float = 0.0,
) -> dict:
    if not serie:
        serie = resolve_serie_tx(cur, filial=filial, tabela="NF")
    validar_serie_tx(cur, filial=filial, tabela="NF", serie=serie)
    if not doc:
        doc = str(sx6_next_tx(cur, filial=filial, serie=serie, tabela="SF2")).zfill(9)

    cur.execute(
        """
        INSERT INTO dbo.SF2_NOTAS
          (F2_DOC, F2_SERIE, F2_EMISSAO, F2_FILIAL, F2_CLIENTE, F2_CLIENTE_COD,
           F2_VALOR, F2_ICMS, F2_IPI, F2_PIS, F2_COFINS, F2_ICMS_ST, F2_DIFAL,
           F2_TOTAL_BRUTO, F2_STATUS, F2_PEDIDO_ID,
           F2_TES, F2_CFOP, F2_ORIGEM)
        VALUES (?, ?, SYSDATETIME(), ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?);
        SELECT CAST(SCOPE_IDENTITY() AS INT) AS id;
        """,
        (
            doc,
            serie,
            filial,
            cliente,
            cliente_cod,
            float(valor_total),
            float(icms),
            float(ipi),
            float(pis),
            float(cofins),
            float(icms_st),
            float(difal),
            float(total_bruto),
            status,
            int(pedido_id) if pedido_id is not None else None,
            tes_cod,
            cfop,
            origem,
        ),
    )
    row = fetchone_dict(cur)
    nf_id = int(row["id"])

    return {"id": nf_id, "doc": doc, "serie": serie}


def sd2_item_criar_tx(
    cur,
    nf_id: int,
    doc: str,
    serie: str,
    item: int,
    filial: str,
    pedido_id: int | None,
    produto: str,
    qtd: int,
    preco_unit: float | None,
    total: float,
    icms: float,
    ipi: float,
    tes_cod: str,
    cfop: str | None = None,
    pis: float = 0.0,
    cofins: float = 0.0,
    icms_st: float = 0.0,
    difal: float = 0.0,
    cst_icms: str | None = None,
    csosn: str | None = None,
    cst_pis: str | None = None,
    cst_cofins: str | None = None,
) -> None:
    d2_item = str(int(item)).zfill(4)
    cur.execute(
        """
        INSERT INTO dbo.SD2_ITENS
          (D2_NF_ID, D2_DOC, D2_SERIE, D2_ITEM, D2_FILIAL, D2_PEDIDO_ID,
           D2_PRODUTO, D2_QTD, D2_PRECO_UNIT, D2_TOTAL, D2_ICMS, D2_IPI,
           D2_PIS, D2_COFINS, D2_ICMS_ST, D2_DIFAL,
           D2_CST_ICMS, D2_CSOSN, D2_CST_PIS, D2_CST_COFINS,
           D2_TES, D2_CFOP, D2_ITEM_NUM)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
        (
            int(nf_id),
            doc,
            serie,
            int(item),
            filial,
            int(pedido_id) if pedido_id is not None else None,
            produto,
            int(qtd),
            float(preco_unit) if preco_unit is not None else None,
            float(total),
            float(icms),
            float(ipi),
            float(pis),
            float(cofins),
            float(icms_st),
            float(difal),
            cst_icms,
            csosn,
            cst_pis,
            cst_cofins,
            tes_cod,
            cfop,
            d2_item,
        ),
    )


def sd2_itens_por_nf_tx(cur, nf_id: int, somente_ativos: bool = True) -> list[dict]:
    sql = """
        SELECT *
        FROM dbo.SD2_ITENS
        WHERE D2_NF_ID=?
    """
    params: list = [int(nf_id)]
    if somente_ativos:
        sql += " AND (D2_STATUS IS NULL OR D2_STATUS<>'CANCELADO')"
    sql += " ORDER BY ID ASC"
    cur.execute(sql, tuple(params))
    rows = cur.fetchall()
    if not rows:
        return []
    cols = [c[0] for c in cur.description]
    return [dict(zip(cols, r)) for r in rows]


def sd2_count_por_nf_tx(cur, nf_id: int) -> int:
    cur.execute(
        """
        SELECT COUNT(*) AS qtd
        FROM dbo.SD2_ITENS
        WHERE D2_NF_ID=?
          AND (D_E_L_E_T_ IS NULL OR D_E_L_E_T_ <> '*')
        """,
        (int(nf_id),),
    )
    row = fetchone_dict(cur)
    return int(row["qtd"] or 0) if row else 0


def sf2_buscar_por_pedido_tx(cur, filial: str, pedido_id: int) -> list[dict]:
    cur.execute(
        """
        SELECT *
        FROM dbo.SF2_NOTAS
        WHERE F2_FILIAL=? AND F2_PEDIDO_ID=?
        ORDER BY ID DESC
        """,
        (filial, int(pedido_id)),
    )
    rows = cur.fetchall()
    if not rows:
        return []
    cols = [c[0] for c in cur.description]
    return [dict(zip(cols, r)) for r in rows]


def sf2_get_tx(cur, nf_id: int) -> dict | None:
    cur.execute(
        """
        SELECT *
        FROM dbo.SF2_NOTAS
        WHERE ID=?
        """,
        (int(nf_id),),
    )
    row = fetchone_dict(cur)
    return row


def sf2_buscar_por_doc_serie_tx(cur, filial: str, doc: str, serie: str) -> dict | None:
    cur.execute(
        """
        SELECT TOP 1 *
        FROM dbo.SF2_NOTAS
        WHERE F2_FILIAL=? AND F2_DOC=? AND F2_SERIE=?
          AND (D_E_L_E_T_ IS NULL OR D_E_L_E_T_ <> '*')
        ORDER BY ID DESC
        """,
        (filial, str(doc).strip(), str(serie).strip()),
    )
    return fetchone_dict(cur)


def sd2_itens_por_nf_id_tx(cur, nf_id: int) -> list[dict]:
    cur.execute(
        """
        SELECT *
        FROM dbo.SD2_ITENS
        WHERE D2_NF_ID=?
          AND (D_E_L_E_T_ IS NULL OR D_E_L_E_T_ <> '*')
        ORDER BY ID ASC
        """,
        (int(nf_id),),
    )
    rows = cur.fetchall()
    if not rows:
        return []
    cols = [c[0] for c in cur.description]
    return [dict(zip(cols, r)) for r in rows]


def sf2_cancelar_tx(cur, nf_id: int, usuario: str | None, motivo: str | None) -> None:
    cur.execute(
        """
        UPDATE dbo.SF2_NOTAS
        SET F2_STATUS='CANCELADA',
            F2_DATA_CANCEL=SYSDATETIME(),
            F2_USUARIO_CANCEL=?,
            F2_MOTIVO_CANCEL=?,
            D_E_L_E_T_='*',
            R_E_C_D_E_L_=COALESCE(R_E_C_D_E_L_, R_E_C_N_O_)
        WHERE ID=? AND F2_STATUS<>'CANCELADA'
        """,
        (usuario, motivo, int(nf_id)),
    )


def sd2_cancelar_por_nf_tx(cur, nf_id: int, usuario: str | None, motivo: str | None) -> int:
    cur.execute(
        """
        UPDATE dbo.SD2_ITENS
        SET D2_STATUS='CANCELADO',
            D2_DATA_CANCEL=SYSDATETIME(),
            D2_USUARIO_CANCEL=?,
            D2_MOTIVO_CANCEL=?,
            D_E_L_E_T_='*',
            R_E_C_D_E_L_=COALESCE(R_E_C_D_E_L_, R_E_C_N_O_)
        WHERE D2_NF_ID=? AND (D2_STATUS IS NULL OR D2_STATUS<>'CANCELADO')
        """,
        (usuario, motivo, int(nf_id)),
    )
    return int(cur.rowcount or 0)
