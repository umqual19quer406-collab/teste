from app.infra.db import fetchone_dict 
 
def sc6_totais_do_pedido_tx(cur, pedido_id: int) -> dict: 
    """ 
    Retorna totais calculados a partir dos itens SC6: 
      - qtd_itens: soma de C6_QTD 
      - valor_itens: soma de C6_TOTAL (ou C6_VALOR) 
    """ 
    cur.execute( 
        """ 
        SELECT 
          COALESCE(SUM(CAST(C6_QTD AS INT)), 0) AS qtd_itens, 
          COALESCE(SUM(CAST(COALESCE(C6_TOTAL, C6_VALOR, 0) AS FLOAT)), 0) AS valor_itens 
        FROM dbo.SC6_ITENS 
        WHERE C6_PEDIDO_ID=? 
          AND (D_E_L_E_T_ IS NULL OR D_E_L_E_T_ <> '*') 
        """, 
        (int(pedido_id),), 
    ) 
    row = fetchone_dict(cur) or {"qtd_itens": 0, "valor_itens": 0} 
    return {"qtd_itens": int(row["qtd_itens"]), "valor_itens": float(row["valor_itens"])}
