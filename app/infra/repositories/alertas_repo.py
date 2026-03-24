from datetime import date

from app.infra.db import fetchone_dict


def _count_query(cur, sql: str, params: tuple) -> int:
    cur.execute(sql, params)
    row = fetchone_dict(cur) or {}
    return int(row.get("total") or 0)


def contar_ar_aberto_tx(cur, filial: str) -> int:
    return _count_query(
        cur,
        """
        SELECT COUNT(1) AS total
        FROM dbo.SE1_AR
        WHERE E1_FILIAL = ? AND E1_STATUS = 'ABERTO'
          AND (D_E_L_E_T_ IS NULL OR D_E_L_E_T_ <> '*')
        """,
        (filial,),
    )


def contar_ar_vencido_tx(cur, filial: str, hoje: date) -> int:
    return _count_query(
        cur,
        """
        SELECT COUNT(1) AS total
        FROM dbo.SE1_AR
        WHERE E1_FILIAL = ? AND E1_STATUS = 'ABERTO' AND E1_VENC < ?
          AND (D_E_L_E_T_ IS NULL OR D_E_L_E_T_ <> '*')
        """,
        (filial, hoje),
    )


def contar_ar_vence_hoje_tx(cur, filial: str, hoje: date) -> int:
    return _count_query(
        cur,
        """
        SELECT COUNT(1) AS total
        FROM dbo.SE1_AR
        WHERE E1_FILIAL = ? AND E1_STATUS = 'ABERTO' AND CAST(E1_VENC AS DATE) = ?
          AND (D_E_L_E_T_ IS NULL OR D_E_L_E_T_ <> '*')
        """,
        (filial, hoje),
    )


def contar_ar_vencendo_ate_tx(cur, filial: str, de: date, ate: date) -> int:
    return _count_query(
        cur,
        """
        SELECT COUNT(1) AS total
        FROM dbo.SE1_AR
        WHERE E1_FILIAL = ? AND E1_STATUS = 'ABERTO'
          AND CAST(E1_VENC AS DATE) >= ? AND CAST(E1_VENC AS DATE) <= ?
          AND (D_E_L_E_T_ IS NULL OR D_E_L_E_T_ <> '*')
        """,
        (filial, de, ate),
    )


def contar_ap_aberto_tx(cur, filial: str) -> int:
    return _count_query(
        cur,
        """
        SELECT COUNT(1) AS total
        FROM dbo.SF1_AP
        WHERE F1_FILIAL = ? AND F1_STATUS = 'ABERTO'
          AND (D_E_L_E_T_ IS NULL OR D_E_L_E_T_ <> '*')
        """,
        (filial,),
    )


def contar_ap_vencido_tx(cur, filial: str, hoje: date) -> int:
    return _count_query(
        cur,
        """
        SELECT COUNT(1) AS total
        FROM dbo.SF1_AP
        WHERE F1_FILIAL = ? AND F1_STATUS = 'ABERTO' AND F1_VENC < ?
          AND (D_E_L_E_T_ IS NULL OR D_E_L_E_T_ <> '*')
        """,
        (filial, hoje),
    )


def contar_ap_vence_hoje_tx(cur, filial: str, hoje: date) -> int:
    return _count_query(
        cur,
        """
        SELECT COUNT(1) AS total
        FROM dbo.SF1_AP
        WHERE F1_FILIAL = ? AND F1_STATUS = 'ABERTO' AND CAST(F1_VENC AS DATE) = ?
          AND (D_E_L_E_T_ IS NULL OR D_E_L_E_T_ <> '*')
        """,
        (filial, hoje),
    )


def contar_ap_vencendo_ate_tx(cur, filial: str, de: date, ate: date) -> int:
    return _count_query(
        cur,
        """
        SELECT COUNT(1) AS total
        FROM dbo.SF1_AP
        WHERE F1_FILIAL = ? AND F1_STATUS = 'ABERTO'
          AND CAST(F1_VENC AS DATE) >= ? AND CAST(F1_VENC AS DATE) <= ?
          AND (D_E_L_E_T_ IS NULL OR D_E_L_E_T_ <> '*')
        """,
        (filial, de, ate),
    )


def contar_reservas_abertas_tx(cur, filial: str) -> int:
    return _count_query(
        cur,
        """
        SELECT COUNT(1) AS total
        FROM dbo.SZ0_RESERVA
        WHERE Z0_FILIAL = ? AND Z0_STATUS = 'ABERTA'
        """,
        (filial,),
    )


def contar_pedidos_abertos_sem_itens_tx(cur, filial: str) -> int:
    return _count_query(
        cur,
        """
        WITH AggSC6 AS (
          SELECT C6_PEDIDO_ID, COUNT(1) AS qtd_itens
          FROM dbo.SC6_ITENS
          WHERE (D_E_L_E_T_ IS NULL OR D_E_L_E_T_ <> '*')
          GROUP BY C6_PEDIDO_ID
        )
        SELECT COUNT(1) AS total
        FROM dbo.SC5_PEDIDOS p
        LEFT JOIN AggSC6 s ON s.C6_PEDIDO_ID = p.ID
        WHERE p.C5_FILIAL = ? AND p.C5_STATUS = 'ABERTO'
          AND COALESCE(s.qtd_itens, 0) = 0
          AND (p.D_E_L_E_T_ IS NULL OR p.D_E_L_E_T_ <> '*')
        """,
        (filial,),
    )


def contar_pedidos_abertos_com_itens_tx(cur, filial: str) -> int:
    return _count_query(
        cur,
        """
        WITH AggSC6 AS (
          SELECT C6_PEDIDO_ID, COUNT(1) AS qtd_itens
          FROM dbo.SC6_ITENS
          WHERE (D_E_L_E_T_ IS NULL OR D_E_L_E_T_ <> '*')
          GROUP BY C6_PEDIDO_ID
        )
        SELECT COUNT(1) AS total
        FROM dbo.SC5_PEDIDOS p
        INNER JOIN AggSC6 s ON s.C6_PEDIDO_ID = p.ID
        WHERE p.C5_FILIAL = ? AND p.C5_STATUS = 'ABERTO'
          AND s.qtd_itens > 0
          AND (p.D_E_L_E_T_ IS NULL OR p.D_E_L_E_T_ <> '*')
        """,
        (filial,),
    )


def contar_contas_caixa_ativas_tx(cur, filial: str) -> int:
    return _count_query(
        cur,
        """
        SELECT COUNT(1) AS total
        FROM dbo.SE5_CONTAS
        WHERE E5_FILIAL = ? AND E5_ATIVA = 1
          AND (D_E_L_E_T_ IS NULL OR D_E_L_E_T_ <> '*')
        """,
        (filial,),
    )
