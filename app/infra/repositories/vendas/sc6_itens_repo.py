from app.infra.db import fetchone_dict, fetchall_dict 


def _sc6_has_cmv_unit(cur) -> bool:
    cur.execute("SELECT CASE WHEN COL_LENGTH('dbo.SC6_ITENS', 'C6_CMV_UNIT') IS NULL THEN 0 ELSE 1 END")
    row = cur.fetchone()
    return bool(row and int(row[0]) == 1)


def _sc6_ensure_cmv_unit_column(cur) -> None:
    if _sc6_has_cmv_unit(cur):
        return
    cur.execute("ALTER TABLE dbo.SC6_ITENS ADD C6_CMV_UNIT DECIMAL(18,2) NULL")
 
def sc6_item_get_tx(cur, item_id: int) -> dict | None: 
    cur.execute(""" 
        SELECT * 
        FROM dbo.SC6_ITENS 
        WHERE ID=?  
          AND (D_E_L_E_T_ IS NULL OR D_E_L_E_T_ <> '*') 
    """, (int(item_id),)) 
    return fetchone_dict(cur) 
 
def sc6_itens_do_pedido_tx(cur, pedido_id: int) -> list[dict]: 
    cmv_select = "C6_CMV_UNIT" if _sc6_has_cmv_unit(cur) else "CAST(NULL AS DECIMAL(18,2)) AS C6_CMV_UNIT"
    cur.execute(f""" 
        SELECT ID, C6_PEDIDO_ID, C6_ITEM, C6_PRODUTO, C6_QTD, 
               C6_PRECO_UNIT, C6_TOTAL, C6_VALOR, C6_ATIVO, {cmv_select}
        FROM dbo.SC6_ITENS 
        WHERE C6_PEDIDO_ID=? AND C6_ATIVO=1 
          AND (D_E_L_E_T_ IS NULL OR D_E_L_E_T_ <> '*') 
        ORDER BY ID ASC 
    """, (int(pedido_id),)) 
    return fetchall_dict(cur) 
 
def sc6_item_atualizar_tx( 
    cur, 
    item_id: int, 
    qtd: int, 
    preco_unit: float, 
    total: float, 
    usuario: str, 
    cmv_unit: float | None = None,
) -> None: 
    _sc6_ensure_cmv_unit_column(cur)
    cur.execute(""" 
        UPDATE dbo.SC6_ITENS 
        SET C6_QTD=?, 
            C6_PRECO_UNIT=?, 
            C6_TOTAL=?, 
            C6_VALOR=?, 
            C6_CMV_UNIT=?,
            C6_DATA_ALT=SYSDATETIME(), 
            C6_USUARIO_ALT=? 
        WHERE ID=? AND C6_ATIVO=1 
    """, (int(qtd), float(preco_unit), float(total), float(total), (float(cmv_unit) if cmv_unit is not None else None), usuario, int(item_id))) 
 
def sc6_item_excluir_logico_tx(cur, item_id: int, usuario: str) -> None: 
    cur.execute(""" 
        UPDATE dbo.SC6_ITENS 
        SET C6_ATIVO=0, 
            C6_DATA_DEL=SYSDATETIME(), 
            C6_USUARIO_DEL=?, 
            D_E_L_E_T_='*', 
            R_E_C_D_E_L_=COALESCE(R_E_C_D_E_L_, R_E_C_N_O_) 
        WHERE ID=? AND C6_ATIVO=1 
    """, (usuario, int(item_id))) 


def sc6_itens_cancelar_por_pedido_tx(cur, pedido_id: int, usuario: str) -> int:
    cur.execute(
        """
        UPDATE dbo.SC6_ITENS
        SET C6_ATIVO=0,
            C6_DATA_DEL=SYSDATETIME(),
            C6_USUARIO_DEL=?,
            D_E_L_E_T_='*',
            R_E_C_D_E_L_=COALESCE(R_E_C_D_E_L_, R_E_C_N_O_)
        WHERE C6_PEDIDO_ID=? AND C6_ATIVO=1
        """,
        (usuario, int(pedido_id)),
    )
    return int(cur.rowcount or 0)
