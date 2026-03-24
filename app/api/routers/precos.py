from datetime import date

from fastapi import APIRouter, Depends
from pydantic import BaseModel

from app.api.deps import get_current_user
from app.infra.db import db_transaction
from app.use_cases.preco_uc import (
    buscar_preco_uc_tx,
    criar_tabela_uc_tx,
    definir_preco_uc_tx,
    listar_precos_tabela_uc_tx,
    listar_tabelas_uc_tx,
)

router = APIRouter(tags=["Preços"])


class TabelaCreate(BaseModel):
    codigo: str
    descricao: str


class PrecoInput(BaseModel):
    tabela_id: int
    produto: str
    preco: float
    dt_ini: date


@router.get("/precos/tabelas")
def listar_tabelas(filial: str = "01", me=Depends(get_current_user)):
    with db_transaction() as (_, cur):
        return listar_tabelas_uc_tx(cur, filial)


@router.get("/precos/tabelas/{tabela_id}/itens")
def listar_precos_tabela(tabela_id: int, filial: str = "01", me=Depends(get_current_user)):
    with db_transaction() as (_, cur):
        return listar_precos_tabela_uc_tx(cur, filial, tabela_id)


@router.post("/precos/tabelas")
def criar_tabela(dados: TabelaCreate, filial: str = "01", me=Depends(get_current_user)):
    with db_transaction() as (_, cur):
        return criar_tabela_uc_tx(cur, me["login"], filial, dados.codigo, dados.descricao)


@router.post("/precos/definir")
def definir_preco(dados: PrecoInput, filial: str = "01", me=Depends(get_current_user)):
    with db_transaction() as (_, cur):
        return definir_preco_uc_tx(
            cur,
            me["login"],
            filial,
            dados.tabela_id,
            dados.produto,
            dados.preco,
            dados.dt_ini,
        )


@router.get("/precos/buscar")
def buscar_preco(produto: str, tabela_id: int, data: date, filial: str = "01", me=Depends(get_current_user)):
    with db_transaction() as (_, cur):
        return buscar_preco_uc_tx(cur, filial, tabela_id, produto, data)
