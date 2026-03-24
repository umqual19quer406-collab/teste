from fastapi import APIRouter, Depends
from pydantic import BaseModel, Field

from app.api.deps import get_current_user
from app.infra.db import db_transaction
from app.use_cases.parceiros_uc import (
    criar_cliente_uc_tx,
    criar_fornecedor_uc_tx,
    inativar_cliente_uc_tx,
    inativar_fornecedor_uc_tx,
    listar_clientes_uc_tx,
    listar_fornecedores_uc_tx,
    obter_cliente_uc_tx,
    obter_fornecedor_uc_tx,
    set_tabela_cliente_uc_tx,
)

router = APIRouter(tags=["Parceiros"])


class ClienteInput(BaseModel):
    cod: str
    nome: str
    doc: str | None = None
    email: str | None = None
    tel: str | None = None
    end: str | None = None
    mun: str | None = None
    uf: str | None = None
    cep: str | None = None
    tabela_id: int | None = Field(default=None, ge=1)


class FornecedorInput(BaseModel):
    cod: str
    nome: str
    doc: str | None = None
    email: str | None = None
    tel: str | None = None
    end: str | None = None
    mun: str | None = None
    uf: str | None = None
    cep: str | None = None


class SetTabelaInput(BaseModel):
    cod: str
    tabela_id: int | None = Field(default=None, ge=1)


@router.post("/parceiros/sa1/clientes")
def criar_cliente(dados: ClienteInput, filial: str = "01", me: dict = Depends(get_current_user)):
    with db_transaction() as (_, cur):
        return criar_cliente_uc_tx(cur, me["login"], filial, **dados.model_dump())


@router.get("/parceiros/sa1/clientes")
def listar_clientes(
    filial: str = "01",
    ativo: bool = True,
    q: str | None = None,
    me: dict = Depends(get_current_user),
):
    with db_transaction() as (_, cur):
        return listar_clientes_uc_tx(cur, filial=filial, ativo=ativo, q=q)


@router.get("/parceiros/sa1/clientes/{cod}")
def obter_cliente(cod: str, filial: str = "01", me: dict = Depends(get_current_user)):
    with db_transaction() as (_, cur):
        return obter_cliente_uc_tx(cur, filial=filial, cod=cod)


@router.post("/parceiros/sa1/clientes/set-tabela")
def set_tabela_cliente(dados: SetTabelaInput, filial: str = "01", me: dict = Depends(get_current_user)):
    with db_transaction() as (_, cur):
        return set_tabela_cliente_uc_tx(cur, me["login"], filial, dados.cod, dados.tabela_id)


@router.delete("/parceiros/sa1/clientes/{cod}")
def inativar_cliente(cod: str, filial: str = "01", me: dict = Depends(get_current_user)):
    with db_transaction() as (_, cur):
        return inativar_cliente_uc_tx(cur, me["login"], filial, cod)


@router.post("/parceiros/sa2/fornecedores")
def criar_fornecedor(dados: FornecedorInput, filial: str = "01", me: dict = Depends(get_current_user)):
    with db_transaction() as (_, cur):
        return criar_fornecedor_uc_tx(cur, me["login"], filial, **dados.model_dump())


@router.get("/parceiros/sa2/fornecedores")
def listar_fornecedores(
    filial: str = "01",
    ativo: bool = True,
    q: str | None = None,
    me: dict = Depends(get_current_user),
):
    with db_transaction() as (_, cur):
        return listar_fornecedores_uc_tx(cur, filial=filial, ativo=ativo, q=q)


@router.get("/parceiros/sa2/fornecedores/{cod}")
def obter_fornecedor(cod: str, filial: str = "01", me: dict = Depends(get_current_user)):
    with db_transaction() as (_, cur):
        return obter_fornecedor_uc_tx(cur, filial=filial, cod=cod)


@router.delete("/parceiros/sa2/fornecedores/{cod}")
def inativar_fornecedor(cod: str, filial: str = "01", me: dict = Depends(get_current_user)):
    with db_transaction() as (_, cur):
        return inativar_fornecedor_uc_tx(cur, me["login"], filial, cod)
