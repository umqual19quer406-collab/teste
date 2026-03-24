from datetime import date 
from app.infra.db import fetchall_dict, fetchone_dict 
 
def sc5_pedidos_enriq_listar_tx( 
    cur, 
    filial: str | None, 
    status: str | None, 
    origem: str | None, 
    de: date | None, 
    ate: date | None, 
    limit: int, 
    offset: int, 
) -> list[dict]: 
    filtros = [] 
    params: list = [] 
 
    if filial: 
        filtros.append("p.C5_FILIAL = ?") 
        params.append(str(filial)) 
 
    if status: 
        filtros.append("p.C5_STATUS = ?") 
        params.append(str(status)) 
 
    if origem: 
        filtros.append("p.C5_ORIGEM = ?") 
        params.append(str(origem)) 
 
    if de is not None: 
        filtros.append("CAST(p.C5_DATA AS DATE) >= ?") 
        params.append(de) 
 
    if ate is not None: 
        filtros.append("CAST(p.C5_DATA AS DATE) <= ?") 
        params.append(ate) 
 
    filtros.append("(p.D_E_L_E_T_ IS NULL OR p.D_E_L_E_T_ <> '*')") 
    where_sql = ("WHERE " + " AND ".join(filtros)) if filtros else "" 
 
    # Observações: 
    # - AggSC6 agrega itens por pedido 
    # - ARLast pega o último título por pedido (maior ID) 
    # - ARStat calcula status consolidado (BAIXADO > ABERTO > CANCELADO) 
    cur.execute( 
        f""" 
        WITH AggSC6 AS ( 
          SELECT 
            C6_PEDIDO_ID, 
            SUM(CAST(C6_QTD AS INT)) AS qtd_itens, 
            SUM(CAST(COALESCE(C6_TOTAL, C6_VALOR, 0) AS FLOAT)) AS valor_itens 
          FROM dbo.SC6_ITENS 
          WHERE (D_E_L_E_T_ IS NULL OR D_E_L_E_T_ <> '*') 
          GROUP BY C6_PEDIDO_ID 
        ), 
        ARJoin AS ( 
          SELECT 
            f2.F2_PEDIDO_ID AS pedido_id, 
            e1.* 
          FROM dbo.SE1_AR e1 
          INNER JOIN dbo.SF2_NOTAS f2 ON f2.ID = TRY_CAST(e1.E1_REF AS INT) 
          WHERE (e1.D_E_L_E_T_ IS NULL OR e1.D_E_L_E_T_ <> '*') 
        ), 
        ARLast AS ( 
          SELECT a.* 
          FROM ARJoin a 
          JOIN ( 
            SELECT pedido_id, MAX(ID) AS max_id 
            FROM ARJoin 
            GROUP BY pedido_id 
          ) x ON x.pedido_id = a.pedido_id AND x.max_id = a.ID 
        ), 
        ARStat AS ( 
          SELECT 
            pedido_id, 
            CASE 
              WHEN SUM(CASE WHEN E1_STATUS='BAIXADO' THEN 1 ELSE 0 END) > 0 THEN 'BAIXADO' 
              WHEN SUM(CASE WHEN E1_STATUS='ABERTO'  THEN 1 ELSE 0 END) > 0 THEN 'ABERTO' 
              WHEN SUM(CASE WHEN E1_STATUS='CANCELADO' THEN 1 ELSE 0 END) > 0 THEN 'CANCELADO' 
              ELSE NULL 
            END AS ar_status 
          FROM ARJoin 
          GROUP BY pedido_id 
        ) 
        SELECT 
          p.ID, 
          p.C5_DATA, 
          p.C5_FILIAL, 
          p.C5_STATUS, 
          p.C5_USUARIO, 
          p.C5_VALOR_TOTAL, 
          p.C5_ICMS, 
          p.C5_IPI, 
          p.C5_TOTAL_BRUTO, 
          p.C5_ORIGEM, 
          p.C5_DATA_CANCEL, 
          p.C5_USUARIO_CANCEL, 
 
          COALESCE(s.qtd_itens, 0) AS qtd_itens, 
          COALESCE(s.valor_itens, 0) AS valor_itens, 
 
          st.ar_status, 
          al.ID        AS ar_id, 
          al.E1_VALOR  AS ar_valor, 
          al.E1_VENC   AS ar_venc, 
          al.E1_SE5_ID AS ar_se5_id, 
          al.E1_STATUS AS ar_status_ultimo 
        FROM dbo.SC5_PEDIDOS p 
        LEFT JOIN AggSC6 s 
          ON s.C6_PEDIDO_ID = p.ID 
        LEFT JOIN ARStat st 
          ON st.pedido_id = p.ID 
        LEFT JOIN ARLast al 
          ON al.pedido_id = p.ID 
        {where_sql} 
        ORDER BY p.ID DESC 
        OFFSET ? ROWS FETCH NEXT ? ROWS ONLY 
        """, 
        tuple(params + [int(offset), int(limit)]), 
    ) 
    return fetchall_dict(cur) 
 
def sc5_pedidos_enriq_contar_tx( 
    cur, 
    filial: str | None, 
    status: str | None, 
    origem: str | None, 
    de: date | None, 
    ate: date | None, 
) -> int: 
    filtros = [] 
    params: list = [] 
 
    if filial: 
        filtros.append("C5_FILIAL = ?") 
        params.append(str(filial)) 
 
    if status: 
        filtros.append("C5_STATUS = ?") 
        params.append(str(status)) 
 
    if origem: 
        filtros.append("C5_ORIGEM = ?") 
        params.append(str(origem)) 
 
    if de is not None: 
        filtros.append("CAST(C5_DATA AS DATE) >= ?") 
        params.append(de) 
 
    if ate is not None: 
        filtros.append("CAST(C5_DATA AS DATE) <= ?") 
        params.append(ate) 

    filtros.append("(D_E_L_E_T_ IS NULL OR D_E_L_E_T_ <> '*')") 
 
    where_sql = ("WHERE " + " AND ".join(filtros)) if filtros else "" 
 
    cur.execute( 
        f"SELECT COUNT(1) AS total FROM dbo.SC5_PEDIDOS {where_sql}", 
        tuple(params), 
    ) 
    row = fetchone_dict(cur) or {"total": 0} 
    return int(row["total"])
