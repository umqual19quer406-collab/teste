from datetime import datetime 
from app.infra.db import fetchall_dict 
 
def log_tx(cur, usuario: str, acao: str) -> None: 
    cur.execute( 
        "INSERT INTO dbo.LOGS (L_USUARIO, L_ACAO, L_DATA) VALUES (?, ?, ?)", 
        (usuario, acao, datetime.now()), 
    ) 
 
def listar_logs_tx(cur, usuario: str, perfil: str): 
    if perfil in {"admin", "auditor"}: 
        cur.execute(""" 
            SELECT * 
            FROM dbo.LOGS 
            ORDER BY ID DESC 
            OFFSET 0 ROWS FETCH NEXT 200 ROWS ONLY 
        """) 
    else: 
        cur.execute(""" 
            SELECT * 
            FROM dbo.LOGS 
            WHERE L_USUARIO=? 
            ORDER BY ID DESC 
            OFFSET 0 ROWS FETCH NEXT 200 ROWS ONLY 
        """, (usuario,)) 
    return fetchall_dict(cur)