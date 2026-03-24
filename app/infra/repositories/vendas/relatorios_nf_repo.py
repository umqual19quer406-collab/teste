from __future__ import annotations

from app.infra.db import fetchall_dict


def nf_pedido_financeiro_resumo_tx(
    cur,
    pedido_id: int,
    nf_status: str | None = None,
    ar_status: str | None = None,
    sc9_status: str | None = None,
) -> list[dict]:
    filtros = ["f2.F2_PEDIDO_ID = ?"]
    params: list = [int(pedido_id)]

    if nf_status:
        filtros.append("f2.F2_STATUS = ?")
        params.append(str(nf_status).strip())
    if ar_status:
        filtros.append("e1.E1_STATUS = ?")
        params.append(str(ar_status).strip())
    if sc9_status:
        filtros.append("s.C9_STATUS = ?")
        params.append(str(sc9_status).strip())

    where_sql = " AND ".join(filtros)
    cur.execute(
        f"""
        SELECT
          f2.ID           AS nf_id,
          f2.F2_DOC       AS nf_doc,
          f2.F2_SERIE     AS nf_serie,
          f2.F2_EMISSAO   AS nf_emissao,
          f2.F2_STATUS    AS nf_status,
          f2.F2_TES       AS nf_tes,
          f2.F2_CFOP      AS nf_cfop,
          f2.F2_VALOR     AS nf_valor,
          f2.F2_ICMS      AS nf_icms,
          f2.F2_IPI       AS nf_ipi,
          f2.F2_PIS       AS nf_pis,
          f2.F2_COFINS    AS nf_cofins,
          f2.F2_ICMS_ST   AS nf_icms_st,
          f2.F2_DIFAL     AS nf_difal,
          f2.F2_TOTAL_BRUTO AS nf_total_bruto,

          s.C9_ITEM       AS sc9_item,
          s.C9_PRODUTO    AS sc9_produto,
          s.C9_QTD        AS sc9_qtd,
          s.C9_STATUS     AS sc9_status,

          e1.ID           AS ar_id,
          e1.E1_NUM       AS ar_num,
          e1.E1_SERIE     AS ar_serie,
          e1.E1_VALOR     AS ar_valor,
          e1.E1_STATUS    AS ar_status,
          e1.E1_VENC      AS ar_venc
        FROM dbo.SF2_NOTAS f2
        LEFT JOIN dbo.SC9_LIBERACAO s
          ON s.C9_PEDIDO_ID = f2.F2_PEDIDO_ID
         AND (s.D_E_L_E_T_ IS NULL OR s.D_E_L_E_T_ <> '*')
        LEFT JOIN dbo.SE1_AR e1
          ON TRY_CAST(e1.E1_REF AS INT) = f2.ID
         AND (e1.D_E_L_E_T_ IS NULL OR e1.D_E_L_E_T_ <> '*')
        WHERE {where_sql}
          AND (f2.D_E_L_E_T_ IS NULL OR f2.D_E_L_E_T_ <> '*')
        ORDER BY f2.ID DESC, s.C9_ITEM ASC
        """,
        tuple(params),
    )
    return fetchall_dict(cur)
