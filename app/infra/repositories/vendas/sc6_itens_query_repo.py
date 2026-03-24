from app.infra.db import fetchall_dict 
 
def sc6_itens_do_pedido_tx(cur, pedido_id: int) -> list[dict]: 
    cur.execute("SELECT CASE WHEN COL_LENGTH('dbo.SC6_ITENS', 'C6_CMV_UNIT') IS NULL THEN 0 ELSE 1 END")
    row = cur.fetchone()
    cmv_select = "C6_CMV_UNIT" if row and int(row[0]) == 1 else "CAST(NULL AS DECIMAL(18,2)) AS C6_CMV_UNIT"
    cur.execute( 
        f""" 
        SELECT ID, C6_PEDIDO_ID, C6_ITEM, C6_PRODUTO, C6_QTD, C6_VALOR, C6_PRECO_UNIT, C6_TOTAL, C6_ATIVO, {cmv_select}
        FROM dbo.SC6_ITENS 
        WHERE C6_PEDIDO_ID=? 
          AND (D_E_L_E_T_ IS NULL OR D_E_L_E_T_ <> '*') 
        ORDER BY ID 
        """, 
        (int(pedido_id),), 
    ) 
    return fetchall_dict(cur)
