from __future__ import annotations 
 
from typing import Optional, Dict, Any, List 
from app.core.exceptions import BusinessError 
from app.infra.repositories.logs_repo import log_tx 
from app.infra.repositories.sa1_repo import ( 
    sa1_get_tx, 
    sa1_listar_tx, 
    sa1_buscar_tx, 
    sa1_criar_tx, 
    sa1_atualizar_tx, 
    sa1_set_ativo_tx, 
) 
 
# (opcional) se você já usa exigir_perfil_tx, mantenha 
from app.use_cases.usuarios_uc import exigir_perfil_tx 
 
def cliente_get_uc_tx(cur, usuario: str, filial: str, cod: str) -> Dict[str, Any]: 
    exigir_perfil_tx(cur, usuario, {"admin", "operador", "auditor"}) 
    c = sa1_get_tx(cur, filial=filial, cod=cod) 
    if not c: 
        raise BusinessError("Cliente não encontrado") 
    return c 
 
def cliente_listar_uc_tx(cur, usuario: str, filial: str, ativos: bool = True) -> List[Dict[str, Any]]: 
    exigir_perfil_tx(cur, usuario, {"admin", "operador", "auditor"}) 
    return sa1_listar_tx(cur, filial=filial, ativos=ativos) 
 
def cliente_buscar_uc_tx(cur, usuario: str, filial: str, termo: str) -> List[Dict[str, Any]]: 
    exigir_perfil_tx(cur, usuario, {"admin", "operador", "auditor"}) 
    return sa1_buscar_tx(cur, filial=filial, termo=termo) 
 
def cliente_criar_uc_tx( 
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
    c = sa1_criar_tx(cur, filial=filial, cod=cod, nome=nome, doc=doc, email=email, fone=fone) 
    log_tx(cur, usuario, f"SA1.CRIAR filial={filial} cod={cod} nome={nome}") 
    return c 
 
def cliente_atualizar_uc_tx( 
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
    c = sa1_atualizar_tx(cur, filial=filial, cod=cod, nome=nome, doc=doc, email=email, fone=fone) 
    log_tx(cur, usuario, f"SA1.ATUALIZAR filial={filial} cod={cod}") 
    return c 
 
def cliente_set_ativo_uc_tx(cur, usuario: str, filial: str, cod: str, ativo: bool) -> Dict[str, Any]: 
    exigir_perfil_tx(cur, usuario, {"admin"}) 
    sa1_set_ativo_tx(cur, filial=filial, cod=cod, ativo=ativo) 
    log_tx(cur, usuario, f"SA1.ATIVO filial={filial} cod={cod} ativo={ativo}") 
    return {"filial": filial, "cod": cod, "ativo": bool(ativo)}