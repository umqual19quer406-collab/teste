from app.infra.db import fetchone_dict 
from app.infra.repositories.sx6_repo import sx6_next_tx
from app.core.exceptions import BusinessError 
 
def sc5_pedido_criar_simples_tx( 
    cur, 
    filial: str, 
    valor_total: float, 
    usuario: str, 
    status: str = "FATURADO", 
) -> int: 
    """ 
    Versão simples (legada): cria SC5 com campos básicos. 
    Útil se algum fluxo antigo não calcula impostos. 
    """ 
    cur.execute( 
        """ 
        INSERT INTO dbo.SC5_PEDIDOS (C5_DATA, C5_FILIAL, C5_VALOR_TOTAL, C5_USUARIO, C5_STATUS) 
        VALUES (SYSDATETIME(), ?, ?, ?, ?); 
        SELECT CAST(SCOPE_IDENTITY() AS INT) AS id; 
        """, 
        (filial, float(valor_total), usuario, status), 
    ) 
    row = fetchone_dict(cur) 
    return int(row["id"]) 
 
from app.infra.db import fetchone_dict 
 
def sc5_pedido_criar_tx( 
    cur, 
    filial: str, 
    valor_total: float, 
    usuario: str, 
    status: str = "ABERTO", 
    icms: float | None = None, 
    ipi: float | None = None, 
    total_bruto: float | None = None, 
    origem: str = "VENDA",   # <-- novo 
) -> int: 
    origem = (origem or "VENDA").strip().upper() 
    if origem not in {"VENDA", "RESERVA"}: 
        origem = "VENDA" 
 
    c5_num = sx6_next_tx(cur, filial=filial, serie="1", tabela="SC5")
    cur.execute( 
        """ 
        INSERT INTO dbo.SC5_PEDIDOS 
          (C5_DATA, C5_FILIAL, C5_NUM, C5_VALOR_TOTAL, C5_USUARIO, C5_STATUS, 
           C5_ICMS, C5_IPI, C5_TOTAL_BRUTO, C5_ORIGEM) 
        VALUES (SYSDATETIME(), ?, ?, ?, ?, ?, ?, ?, ?, ?); 
        SELECT CAST(SCOPE_IDENTITY() AS INT) AS id; 
        """, 
        (filial, str(c5_num).zfill(9), float(valor_total), usuario, status, icms, ipi, total_bruto, origem), 
    ) 
    row = fetchone_dict(cur) 
    return int(row["id"]) 
 
from app.infra.db import fetchone_dict 
 
def sc5_pedido_get_tx(cur, pedido_id: int) -> dict | None: 
    cur.execute( 
        """ 
        SELECT TOP 1 
          ID, 
          C5_DATA, 
          C5_FILIAL, 
          C5_STATUS, 
          C5_USUARIO, 
          C5_VALOR_TOTAL, 
          C5_ICMS, 
          C5_IPI, 
          C5_TOTAL_BRUTO, 
          C5_ORIGEM, 
          C5_DATA_CANCEL, 
          C5_USUARIO_CANCEL 
        FROM dbo.SC5_PEDIDOS 
        WHERE ID=? 
          AND (D_E_L_E_T_ IS NULL OR D_E_L_E_T_ <> '*') 
        """, 
        (int(pedido_id),), 
    ) 
    return fetchone_dict(cur) 
 
def sc5_pedido_atualizar_valor_total_tx(cur, pedido_id: int, valor_total: float) -> None: 
    cur.execute( 
        """ 
        UPDATE dbo.SC5_PEDIDOS 
        SET C5_VALOR_TOTAL=? 
        WHERE ID=? 
        """, 
        (float(valor_total), int(pedido_id)), 
    ) 
 
def sc5_pedido_status_tx(cur, pedido_id: int, status: str, usuario: str | None = None, motivo: str | None = None) -> None: 
    status_norm = str(status).strip().upper() 
    if status_norm == "CANCELADO": 
        cur.execute( 
            """ 
            UPDATE dbo.SC5_PEDIDOS 
            SET C5_STATUS='CANCELADO', 
                C5_MOTIVO_CANCEL=?, 
                C5_DATA_CANCEL=SYSDATETIME(), 
                C5_USUARIO_CANCEL=?, 
                D_E_L_E_T_='*', 
                R_E_C_D_E_L_=COALESCE(R_E_C_D_E_L_, R_E_C_N_O_) 
            WHERE ID=? 
            """, 
            (motivo, usuario, int(pedido_id)), 
        ) 
        return 
 
    cur.execute( 
        "UPDATE dbo.SC5_PEDIDOS SET C5_STATUS=? WHERE ID=?", 
        (status_norm, int(pedido_id)), 
    ) 
 
def sc5_pedido_atualizar_totais_tx( 
    cur, 
    pedido_id: int, 
    valor_total: float, 
    icms: float, 
    ipi: float, 
    total_bruto: float, 
    status: str = "FATURADO", 
) -> None: 
    cur.execute( 
        """ 
        UPDATE dbo.SC5_PEDIDOS 
        SET C5_VALOR_TOTAL=? 
        WHERE ID=? 
        """, 
        (float(valor_total), int(pedido_id)), 
    ) 
 
def sc5_pedido_marcar_faturado_tx(cur, pedido_id: int, icms: float, ipi: float, total_bruto: float) -> None: 
    cur.execute(""" 
        UPDATE dbo.SC5_PEDIDOS 
        SET C5_STATUS='FATURADO', 
            C5_ICMS=?, 
            C5_IPI=?, 
            C5_TOTAL_BRUTO=? 
        WHERE ID=? AND C5_STATUS='ABERTO' 
    """, (float(icms), float(ipi), float(total_bruto), int(pedido_id))) 
    if cur.rowcount == 0: 
        # ou não existe, ou não está ABERTO 
        pass 
 
def sc5_pedido_cancelar_faturado_tx(cur, pedido_id: int, usuario: str, motivo: str | None) -> None: 
    cur.execute(""" 
        UPDATE dbo.SC5_PEDIDOS 
        SET C5_STATUS='CANCELADO', 
            C5_MOTIVO_CANCEL=?, 
            C5_DATA_CANCEL=SYSDATETIME(), 
            C5_USUARIO_CANCEL=?, 
            D_E_L_E_T_='*', 
            R_E_C_D_E_L_=COALESCE(R_E_C_D_E_L_, R_E_C_N_O_) 
        WHERE ID=? AND C5_STATUS='FATURADO' 
    """, (motivo, usuario, int(pedido_id))) 
    if cur.rowcount == 0: 
        raise BusinessError("Pedido não está FATURADO (não é possível estornar)")
