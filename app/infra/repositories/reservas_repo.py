
from app.infra.db import fetchone_dict 
from app.domain.errors import BusinessError  # se você usa BusinessError 
 
def reserva_get_tx(cur, reserva_id: int) -> dict | None: 
    cur.execute("SELECT * FROM dbo.SZ0_RESERVA WHERE ID=?", (int(reserva_id),)) 
    return fetchone_dict(cur) 
 
def reserva_criar_tx( 
    cur, 
    filial: str, 
    produto: str, 
    qtd: int, 
    usuario: str, 
    cliente_cod: str | None = None, 
    tabela_id: int | None = None, 
    preco_unit: float | None = None, 
    total: float | None = None, 
) -> int: 
    cur.execute(""" 
        INSERT INTO dbo.SZ0_RESERVA 
          (Z0_DATA, Z0_FILIAL, Z0_PRODUTO, Z0_QTD, Z0_USUARIO, Z0_STATUS, 
           Z0_CLIENTE_COD, Z0_TABELA_ID, Z0_PRECO_UNIT, Z0_TOTAL) 
        VALUES (SYSDATETIME(), ?, ?, ?, ?, 'ABERTA', ?, ?, ?, ?); 
        SELECT CAST(SCOPE_IDENTITY() AS INT) AS id; 
    """, (filial, produto, int(qtd), usuario, cliente_cod, tabela_id, preco_unit, total)) 
    row = fetchone_dict(cur) 
    return int(row["id"]) 
 
def reserva_status_tx(cur, reserva_id: int, status: str) -> None: 
    cur.execute("UPDATE dbo.SZ0_RESERVA SET Z0_STATUS=? WHERE ID=?", (status, int(reserva_id))) 
    if cur.rowcount == 0: 
        raise BusinessError("Reserva não encontrada para atualizar status") 
     
def reserva_set_cliente_preco_tx( 
    cur, 
    reserva_id: int, 
    cliente_cod: str | None, 
    tabela_id: int | None, 
    preco_unit: float | None, 
    total: float | None, 
) -> None: 
    cur.execute(""" 
        UPDATE dbo.SZ0_RESERVA 
        SET 
          Z0_CLIENTE_COD = COALESCE(?, Z0_CLIENTE_COD), 
          Z0_TABELA_ID   = COALESCE(?, Z0_TABELA_ID), 
          Z0_PRECO_UNIT  = COALESCE(?, Z0_PRECO_UNIT), 
          Z0_TOTAL       = COALESCE(?, Z0_TOTAL) 
        WHERE ID = ? 
    """, (cliente_cod, tabela_id, preco_unit, total, int(reserva_id))) 
    if cur.rowcount == 0: 
        raise BusinessError("Reserva não encontrada para atualizar snapshot")     