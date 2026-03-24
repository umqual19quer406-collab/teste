from datetime import date 
from app.infra.db import fetchall_dict, fetchone_dict 
 
def sc5_pedidos_listar_tx( 
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
        f""" 
        SELECT 
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
        {where_sql} 
        ORDER BY ID DESC 
        OFFSET ? ROWS FETCH NEXT ? ROWS ONLY 
        """, 
        tuple(params + [int(offset), int(limit)]), 
    ) 
    return fetchall_dict(cur) 
 
def sc5_pedidos_contar_tx( 
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
