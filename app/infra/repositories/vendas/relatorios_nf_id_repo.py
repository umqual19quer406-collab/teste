from __future__ import annotations

from app.infra.db import fetchall_dict


def nf_rastreio_tx(cur, nf_id: int) -> list[dict]:
    cur.execute(
        """
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
          f2.F2_TOTAL_BRUTO AS nf_total_bruto,

          p.ID            AS pedido_id,
          p.C5_STATUS     AS pedido_status,
          p.C5_FILIAL     AS pedido_filial,
          p.C5_DATA       AS pedido_data,

          i.ID            AS item_id,
          i.C6_PRODUTO    AS item_produto,
          i.C6_QTD        AS item_qtd,
          i.C6_TOTAL      AS item_total,

          s.C9_ITEM       AS sc9_item,
          s.C9_QTD        AS sc9_qtd,
          s.C9_STATUS     AS sc9_status,

          e1.ID           AS ar_id,
          e1.E1_NUM       AS ar_num,
          e1.E1_SERIE     AS ar_serie,
          e1.E1_VALOR     AS ar_valor,
          e1.E1_STATUS    AS ar_status,
          e1.E1_VENC      AS ar_venc
        FROM dbo.SF2_NOTAS f2
        LEFT JOIN dbo.SC5_PEDIDOS p ON p.ID = f2.F2_PEDIDO_ID
         AND (p.D_E_L_E_T_ IS NULL OR p.D_E_L_E_T_ <> '*')
        LEFT JOIN dbo.SC6_ITENS i ON i.C6_PEDIDO_ID = p.ID
         AND (i.D_E_L_E_T_ IS NULL OR i.D_E_L_E_T_ <> '*')
        LEFT JOIN dbo.SC9_LIBERACAO s ON s.C9_PEDIDO_ID = p.ID AND s.C9_ITEM = i.ID
         AND (s.D_E_L_E_T_ IS NULL OR s.D_E_L_E_T_ <> '*')
        LEFT JOIN dbo.SE1_AR e1 ON TRY_CAST(e1.E1_REF AS INT) = f2.ID
         AND (e1.D_E_L_E_T_ IS NULL OR e1.D_E_L_E_T_ <> '*')
        WHERE f2.ID = ?
          AND (f2.D_E_L_E_T_ IS NULL OR f2.D_E_L_E_T_ <> '*')
        ORDER BY i.ID ASC
        """,
        (int(nf_id),),
    )
    return fetchall_dict(cur)
