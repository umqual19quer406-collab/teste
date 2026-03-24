from app.infra.db import fetchone_dict


def _sc6_has_cmv_unit(cur) -> bool:
    cur.execute("SELECT CASE WHEN COL_LENGTH('dbo.SC6_ITENS', 'C6_CMV_UNIT') IS NULL THEN 0 ELSE 1 END")
    row = cur.fetchone()
    return bool(row and int(row[0]) == 1)


def _sc6_ensure_cmv_unit_column(cur) -> None:
    if _sc6_has_cmv_unit(cur):
        return
    cur.execute("ALTER TABLE dbo.SC6_ITENS ADD C6_CMV_UNIT DECIMAL(18,2) NULL")


def sc6_item_criar_tx( 
    cur, 
    pedido_id: int, 
    produto: str, 
    qtd: int, 
    total: float, 
    preco_unit: float | None = None, 
    cmv_unit: float | None = None,
) -> dict: 
    """ 
    Insere item SC6. Mantém compatibilidade com C6_VALOR (total), 
    e também grava C6_PRECO_UNIT e C6_TOTAL (novo padrão). 
    """ 
    if preco_unit is None: 
        preco_unit = (float(total) / int(qtd)) if int(qtd) > 0 else float(total) 
 
    cur.execute(
        """
        SELECT COALESCE(MAX(C6_ITEM), 0) + 1 AS prox
        FROM dbo.SC6_ITENS
        WHERE C6_PEDIDO_ID=?
          AND (D_E_L_E_T_ IS NULL OR D_E_L_E_T_ <> '*')
        """,
        (int(pedido_id),),
    )
    prox = fetchone_dict(cur) or {"prox": 1}
    c6_item = int(prox["prox"])

    _sc6_ensure_cmv_unit_column(cur)

    cur.execute( 
        """ 
        INSERT INTO dbo.SC6_ITENS 
          (C6_PEDIDO_ID, C6_ITEM, C6_PRODUTO, C6_QTD, C6_VALOR, C6_PRECO_UNIT, C6_TOTAL, C6_CMV_UNIT) 
        VALUES (?, ?, ?, ?, ?, ?, ?, ?); 
        SELECT CAST(SCOPE_IDENTITY() AS INT) AS id; 
        """, 
        (
            int(pedido_id),
            c6_item,
            str(produto),
            int(qtd),
            float(total),
            float(preco_unit),
            float(total),
            (float(cmv_unit) if cmv_unit is not None else None),
        ), 
    )
    row = cur.fetchone()
    item_id = int(row[0]) if row else 0
    return {"id": item_id, "item": c6_item}
