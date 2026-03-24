from app.core.exceptions import BusinessError 
from app.use_cases.usuarios_uc import exigir_perfil_tx 
from app.infra.repositories.sb1_repo import sb1_upsert_tx, sb1_get_tx, sb1_buscar_tx 
from app.infra.repositories.sd3_repo import saldo_sd3_tx 
from app.infra.repositories.logs_repo import log_tx 
 
def upsert_produto_tx(cur, usuario: str, cod: str, desc: str, preco: float, filial: str) -> dict: 
    exigir_perfil_tx(cur, usuario, {"admin"}) 
    if preco < 0: 
        raise BusinessError("Preço não pode ser negativo") 
 
    sb1_upsert_tx(cur, cod, desc, preco, filial) 
    log_tx(cur, usuario, f"Produto upsert {cod}/{filial}") 
 
    snap = sb1_get_tx(cur, cod, filial) 
    snap["saldo_sd3"] = saldo_sd3_tx(cur, cod, filial) 
    return snap


def buscar_produtos_tx(cur, filial: str, q: str, limite: int = 20) -> list[dict]:
    return sb1_buscar_tx(cur, filial, q, limite)
