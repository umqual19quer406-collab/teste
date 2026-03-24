from app.infra.db import fetchone_dict 
 
def venda_buscar_reserva_id_por_pedido_tx(cur, pedido_id: int) -> int | None: 
    """ 
    Retorna a reserva (SZ0_RESERVA.ID) que gerou esse pedido, se existir. 
    """ 
    cur.execute(""" 
        SELECT TOP 1 ID 
        FROM dbo.SZ0_RESERVA 
        WHERE Z0_PEDIDO_ID=? 
        ORDER BY ID DESC 
    """, (int(pedido_id),)) 
    row = fetchone_dict(cur) 
    return int(row["ID"]) if row else None 