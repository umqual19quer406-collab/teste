from __future__ import annotations 
 
from typing import Optional, Dict, Any, List 
from app.core.exceptions import BusinessError 
from app.infra.repositories.logs_repo import log_tx 
from app.infra.repositories.sa2_repo import ( 
    sa2_get_tx, 
    sa2_listar_tx, 
    sa2_buscar_tx, 
    sa2_criar_tx, 
    sa2_atualizar_tx, 
    sa2_set_ativo_tx, 
) 
from app.use_cases.usuarios_uc import exigir_perfil_tx 
 
def forn_get_uc_tx(cur, usuario: str, filial: str, cod: str) -> Dict[str, Any]: 
    exigir_perfil_tx(cur, usuario, {"admin", "operador", "auditor"}) 
    f = sa2_get_tx(cur, filial=filial, cod=cod) 
    if not f: 
        raise BusinessError("Fornecedor não encontrado") 
    return f 
 
def forn_listar_uc_tx(cur, usuario: str, filial: str, ativos: bool = True) -> List[Dict[str, Any]]: 
    exigir_perfil_tx(cur, usuario, {"admin", "operador", "auditor"}) 
    return sa2_listar_tx(cur, filial=filial, ativos=ativos) 
 
def forn_buscar_uc_tx(cur, usuario: str, filial: str, termo: str) -> List[Dict[str, Any]]: 
    exigir_perfil_tx(cur, usuario, {"admin", "operador", "auditor"}) 
    return sa2_buscar_tx(cur, filial=filial, termo=termo) 
 
def forn_criar_uc_tx( 
    cur, 
    usuario: str, 
    filial: str, 
    cod: str, 
    nome: str, 
    doc: Optional[str] = None, 
    email: Optional[str] = None, 
    fone: Optional[str] = None, 
) -> Dict[str, Any]: 
    exigir_perfil_tx(cur, usuario, {"admin", "operador"}) 
    f = sa2_criar_tx(cur, filial=filial, cod=cod, nome=nome, doc=doc, email=email, fone=fone) 
    log_tx(cur, usuario, f"SA2.CRIAR filial={filial} cod={cod} nome={nome}") 
    return f 
 
def forn_atualizar_uc_tx( 
    cur, 
    usuario: str, 
    filial: str, 
    cod: str, 
    nome: Optional[str] = None, 
    doc: Optional[str] = None, 
    email: Optional[str] = None, 
    fone: Optional[str] = None, 
) -> Dict[str, Any]: 
    exigir_perfil_tx(cur, usuario, {"admin", "operador"}) 
    f = sa2_atualizar_tx(cur, filial=filial, cod=cod, nome=nome, doc=doc, email=email, fone=fone) 
    log_tx(cur, usuario, f"SA2.ATUALIZAR filial={filial} cod={cod}") 
    return f 
 
def forn_set_ativo_uc_tx(cur, usuario: str, filial: str, cod: str, ativo: bool) -> Dict[str, Any]: 
    exigir_perfil_tx(cur, usuario, {"admin"}) 
    sa2_set_ativo_tx(cur, filial=filial, cod=cod, ativo=ativo) 
    log_tx(cur, usuario, f"SA2.ATIVO filial={filial} cod={cod} ativo={ativo}") 
    return {"filial": filial, "cod": cod, "ativo": bool(ativo)}