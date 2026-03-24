from __future__ import annotations

from app.infra.db import fetchall_dict


def sc9_resumo_por_pedido_tx(cur, pedido_id: int) -> list[dict]:
    cur.execute(
        """
        SELECT
          i.ID AS item_id,
          i.C6_PRODUTO AS produto,
          i.C6_QTD AS qtd_pedido,
          COALESCE(l.qtd_liberada, 0) AS qtd_liberada,
          (i.C6_QTD - COALESCE(l.qtd_liberada, 0)) AS qtd_pendente
        FROM dbo.SC6_ITENS i
        LEFT JOIN (
          SELECT C9_PEDIDO_ID, C9_PRODUTO, C9_ITEM, SUM(C9_QTD) AS qtd_liberada
          FROM dbo.SC9_LIBERACAO
          WHERE C9_PEDIDO_ID = ?
            AND C9_STATUS = 'LIBERADO'
            AND (D_E_L_E_T_ IS NULL OR D_E_L_E_T_ <> '*')
          GROUP BY C9_PEDIDO_ID, C9_PRODUTO, C9_ITEM
        ) l ON l.C9_PEDIDO_ID = i.C6_PEDIDO_ID AND l.C9_PRODUTO = i.C6_PRODUTO AND l.C9_ITEM = i.ID
        WHERE i.C6_PEDIDO_ID = ?
          AND i.C6_ATIVO = 1
          AND (i.D_E_L_E_T_ IS NULL OR i.D_E_L_E_T_ <> '*')
        ORDER BY i.C6_PRODUTO
        """,
        (int(pedido_id), int(pedido_id)),
    )
    return fetchall_dict(cur)
