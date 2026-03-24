from __future__ import annotations 
 
from typing import Optional, Dict, Any 
from app.core.exceptions import BusinessError 
from app.use_cases.usuarios_uc import exigir_perfil_tx 
from app.infra.repositories.sa2_repo import sa2_get_tx 
from app.infra.repositories.financeiro_repo import ap_criar_tx 
from app.infra.repositories.logs_repo import log_tx 
 
def lancar_ap_uc_tx( 
    cur, 
    usuario: str, 
    filial: str, 
    forn_cod: str, 
    valor: float, 
    ref: str, 
    venc_dias: int = 30, 
) -> Dict[str, Any]: 
    exigir_perfil_tx(cur, usuario, {"admin", "operador"}) 
 
    forn_cod = (forn_cod or "").strip() 
    if not forn_cod: 
        raise BusinessError("forn_cod é obrigatório") 
    if float(valor) <= 0: 
        raise BusinessError("valor deve ser > 0") 
 
    f = sa2_get_tx(cur, filial=filial, cod=forn_cod) 
    if not f: 
        raise BusinessError("Fornecedor não encontrado (SA2)") 
 
    forn_nome = f["A2_NOME"] 
 
    ap_criar_tx( 
        cur, 
        filial=filial, 
        forn=forn_nome,          # snapshot 
        forn_cod=forn_cod,       # chave SA2 
        valor=float(valor), 
        ref=ref, 
        venc_dias=int(venc_dias), 
    ) 
 
    log_tx(cur, usuario, f"SF1.LANCAR filial={filial} forn_cod={forn_cod} valor={valor} ref={ref}") 
    return {"ok": True, "filial": filial, "forn_cod": forn_cod, "forn_nome": forn_nome, "valor": float(valor), "ref": ref} 