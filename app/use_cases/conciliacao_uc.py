from app.use_cases.usuarios_uc import exigir_perfil_tx 
from app.infra.repositories.sd3_repo import saldo_sd3_tx 
from app.infra.repositories.logs_repo import log_tx 
from app.infra.db import fetchall_dict 
 
def recalcular_sb1_por_sd3_tx(cur, usuario: str, filial: str) -> dict: 
    exigir_perfil_tx(cur, usuario, {"admin"}) 
    cur.execute("SELECT B1_COD FROM SB1_PRODUTOS WHERE B1_FILIAL=?", (filial,)) 
    cods = [r["B1_COD"] for r in fetchall_dict(cur)] 
 
    for cod in cods: 
        saldo = saldo_sd3_tx(cur, cod, filial) 
        cur.execute( 
            "UPDATE SB1_PRODUTOS SET B1_ESTOQUE=? WHERE B1_COD=? AND B1_FILIAL=?", 
            (int(saldo), cod, filial), 
        ) 
 
    log_tx(cur, usuario, f"Recalcular SB1 por SD3 (filial={filial}) itens={len(cods)}") 
    return {"filial": filial, "itens": len(cods)}