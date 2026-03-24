from datetime import datetime 
 
def transfer_registrar_tx(cur, produto: str, qtd: int, origem: str, destino: str, usuario: str, ref: str) -> None: 
    cur.execute(""" 
        INSERT INTO ST0_TRANSFER (T0_DATA, T0_PRODUTO, T0_QTD, T0_ORIGEM, T0_DESTINO, 
T0_USUARIO, T0_REF) 
        VALUES (?, ?, ?, ?, ?, ?, ?) 
    """, (datetime.now(), produto, int(qtd), origem, destino, usuario, ref))