from datetime import datetime 
from app.infra.db import fetchone_dict, fetchall_dict 
from app.core.exceptions import BusinessError 
 
def sd3_mov_tx( 
    cur, 
    filial: str, 
    produto: str, 
    tipo: str,     # 'E'/'S' 
    qtd: int, 
    custo_unit: float, 
    valor: float, 
    origem: str, 
    ref: str | None, 
    usuario: str, 
) -> None: 
    if tipo not in {"E", "S"}: 
        raise BusinessError("Tipo inválido (E/S)") 
    if qtd <= 0: 
        raise BusinessError("Quantidade deve ser > 0") 
 
    cur.execute( 
        """ 
        INSERT INTO SD3_MOV ( 
            D3_DATA, D3_FILIAL, D3_PRODUTO, D3_TIPO, D3_QTD, 
            D3_CUSTO_UNIT, D3_VALOR, D3_ORIGEM, D3_REF, D3_USUARIO 
        ) 
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?) 
        """, 
        (datetime.now(), filial, produto, tipo, int(qtd), float(custo_unit), float(valor), origem, ref, usuario), 
    ) 
 
def sd3_saldo_tx(cur, produto: str, filial: str) -> int: 
    cur.execute( 
        """ 
        SELECT COALESCE(SUM(CASE WHEN D3_TIPO='E' THEN D3_QTD ELSE -D3_QTD END), 0) AS SALDO 
        FROM SD3_MOV 
        WHERE D3_PRODUTO=? AND D3_FILIAL=? 
          AND (D_E_L_E_T_ IS NULL OR D_E_L_E_T_ <> '*') 
        """, 
        (produto, filial), 
    ) 
    row = fetchone_dict(cur) 
    return int(row["SALDO"]) if row else 0 
def extrato_sd3_tx(cur, produto: str, filial: str, limite: int) -> list[dict]: 
    cur.execute(""" 
        SELECT ID, D3_DATA, D3_TIPO, D3_QTD, D3_CUSTO_UNIT, D3_VALOR, D3_ORIGEM, D3_REF, 
D3_USUARIO 
        FROM SD3_MOV 
        WHERE D3_PRODUTO=? AND D3_FILIAL=? 
          AND (D_E_L_E_T_ IS NULL OR D_E_L_E_T_ <> '*') 
        ORDER BY ID DESC 
        OFFSET 0 ROWS FETCH NEXT ? ROWS ONLY 
    """, (produto, filial, int(limite))) 
    return fetchall_dict(cur) 
 
saldo_sd3_tx = sd3_saldo_tx 
