from __future__ import annotations

from app.infra.db import fetchall_dict, fetchone_dict


def sc9_liberar_tx(
    cur,
    pedido_id: int,
    filial: str,
    produto: str,
    qtd: int,
    usuario: str,
    item: int | None = None,
) -> int:
    cur.execute(
        """
        INSERT INTO dbo.SC9_LIBERACAO
          (C9_PEDIDO_ID, C9_FILIAL, C9_PRODUTO, C9_QTD, C9_STATUS, C9_USUARIO, C9_DATA, C9_ITEM)
        VALUES (?, ?, ?, ?, 'LIBERADO', ?, SYSDATETIME(), ?);
        SELECT CAST(SCOPE_IDENTITY() AS INT) AS id;
        """,
        (int(pedido_id), filial, produto, int(qtd), usuario, int(item) if item is not None else None),
    )
    row = fetchone_dict(cur)
    return int(row["id"])


def sc9_qtd_liberada_por_pedido_tx(cur, pedido_id: int) -> dict:
    cur.execute(
        """
        SELECT
          C9_ITEM,
          COALESCE(SUM(C9_QTD), 0) AS qtd_liberada
        FROM dbo.SC9_LIBERACAO
        WHERE C9_PEDIDO_ID = ?
          AND C9_STATUS = 'LIBERADO'
          AND (D_E_L_E_T_ IS NULL OR D_E_L_E_T_ <> '*')
        GROUP BY C9_ITEM
        """,
        (int(pedido_id),),
    )
    rows = fetchall_dict(cur)
    return {int(r["C9_ITEM"]): int(r["qtd_liberada"]) for r in rows if r["C9_ITEM"] is not None}


def sc9_cancelar_por_pedido_tx(cur, pedido_id: int, usuario: str | None = None) -> int:
    cur.execute(
        """
        UPDATE dbo.SC9_LIBERACAO
        SET C9_STATUS='CANCELADO',
            C9_USUARIO_CANCEL=?,
            C9_DATA_CANCEL=SYSDATETIME(),
            D_E_L_E_T_='*',
            R_E_C_D_E_L_=COALESCE(R_E_C_D_E_L_, R_E_C_N_O_)
        WHERE C9_PEDIDO_ID=? AND C9_STATUS='LIBERADO'
        """,
        (usuario, int(pedido_id)),
    )
    return int(cur.rowcount or 0)
