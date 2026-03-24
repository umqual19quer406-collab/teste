from __future__ import annotations 
 
from fastapi import APIRouter, Depends 
from pydantic import BaseModel 
from typing import Optional 
 
from app.api.deps import get_current_user 
from app.infra.db import db_transaction 
from app.use_cases.clientes_uc import ( 
    cliente_get_uc_tx, 
    cliente_listar_uc_tx, 
    cliente_buscar_uc_tx, 
    cliente_criar_uc_tx, 
    cliente_atualizar_uc_tx, 
    cliente_set_ativo_uc_tx, 
) 
 
router = APIRouter(prefix="/clientes", tags=["Clientes"]) 
 
class ClienteCreateInput(BaseModel): 
    cod: str 
    nome: str 
    doc: Optional[str] = None 
    email: Optional[str] = None 
    fone: Optional[str] = None 
    filial: str = "01" 
 
class ClienteUpdateInput(BaseModel): 
    nome: Optional[str] = None 
    doc: Optional[str] = None 
    email: Optional[str] = None 
    fone: Optional[str] = None 
    filial: str = "01" 
 
class ClienteAtivoInput(BaseModel): 
    ativo: bool 
    filial: str = "01" 
 
@router.get("") 
def listar(ativos: bool = True, filial: str = "01", me: dict = Depends(get_current_user)): 
    with db_transaction() as (_, cur): 
        return cliente_listar_uc_tx(cur, usuario=me["login"], filial=filial, ativos=ativos) 
 
@router.get("/buscar") 
def buscar(q: str, filial: str = "01", me: dict = Depends(get_current_user)): 
    with db_transaction() as (_, cur): 
        return cliente_buscar_uc_tx(cur, usuario=me["login"], filial=filial, termo=q) 
 
@router.get("/{cod}") 
def get(cod: str, filial: str = "01", me: dict = Depends(get_current_user)): 
    with db_transaction() as (_, cur): 
        return cliente_get_uc_tx(cur, usuario=me["login"], filial=filial, cod=cod) 
 
@router.post("") 
def criar(dados: ClienteCreateInput, me: dict = Depends(get_current_user)): 
    with db_transaction() as (_, cur): 
        return cliente_criar_uc_tx( 
            cur, 
            usuario=me["login"], 
            filial=dados.filial, 
            cod=dados.cod, 
            nome=dados.nome, 
            doc=dados.doc, 
            email=dados.email, 
            fone=dados.fone, 
        ) 
 
@router.put("/{cod}") 
def atualizar(cod: str, dados: ClienteUpdateInput, me: dict = Depends(get_current_user)): 
    with db_transaction() as (_, cur): 
        return cliente_atualizar_uc_tx( 
            cur, 
            usuario=me["login"], 
            filial=dados.filial, 
            cod=cod, 
            nome=dados.nome, 
            doc=dados.doc, 
            email=dados.email, 
            fone=dados.fone, 
        ) 
 
@router.post("/{cod}/ativo") 
def set_ativo(cod: str, dados: ClienteAtivoInput, me: dict = Depends(get_current_user)): 
    with db_transaction() as (_, cur): 
        return cliente_set_ativo_uc_tx(cur, usuario=me["login"], filial=dados.filial, cod=cod, ativo=dados.ativo) 