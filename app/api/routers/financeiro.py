from datetime import date

from fastapi import APIRouter, Depends
from pydantic import BaseModel, ConfigDict, Field

from app.api.deps import get_current_user
from app.api.schemas.errors import common_error_responses
from app.infra.db import db_transaction
from app.use_cases.financeiro_uc import (
    criar_categoria_uc_tx,
    definir_categoria_mov_uc_tx,
    dre_simples_uc_tx,
    extrato_caixa_uc_tx,
    listar_ap_uc_tx,
    listar_ar_uc_tx,
    listar_categorias_uc_tx,
    listar_contas_caixa_uc_tx,
    obter_movimento_uc_tx,
    pagar_ap_uc_tx,
    receber_ar_uc_tx,
    saldo_caixa_uc_tx,
)

router = APIRouter(tags=["Financeiro"])


class LiquidarInput(BaseModel):
    model_config = ConfigDict(json_schema_extra={"example": {"titulo_id": 123, "conta_id": 1}})

    titulo_id: int = Field(..., ge=1)
    conta_id: int = Field(..., ge=1)


class CategoriaCreateInput(BaseModel):
    nome: str
    tipo: str


class MovSetCategoriaInput(BaseModel):
    mov_id: int = Field(..., ge=1)
    categ_id: int | None = Field(default=None, ge=1)


@router.get("/financeiro/ar")
def listar_ar(filial: str = "01", status: str = "ABERTO", me=Depends(get_current_user)):
    with db_transaction() as (_, cur):
        return listar_ar_uc_tx(cur, filial=filial, status=status)


@router.get("/financeiro/ap")
def listar_ap(filial: str = "01", status: str = "ABERTO", me: dict = Depends(get_current_user)):
    with db_transaction() as (_, cur):
        return listar_ap_uc_tx(cur, usuario=me["login"], filial=filial, status=status)


@router.post("/financeiro/ar/baixar")
def baixar_ar(dados: LiquidarInput, me: dict = Depends(get_current_user)):
    with db_transaction() as (_, cur):
        return receber_ar_uc_tx(cur, me["login"], dados.titulo_id, dados.conta_id)


@router.post("/financeiro/ap/baixar")
def baixar_ap(dados: LiquidarInput, me: dict = Depends(get_current_user)):
    with db_transaction() as (_, cur):
        return pagar_ap_uc_tx(cur, me["login"], dados.titulo_id, dados.conta_id)


@router.post("/financeiro/ar/receber", responses=common_error_responses(400, 401, 403, 422, 500))
def receber_ar(dados: LiquidarInput, me: dict = Depends(get_current_user)):
    with db_transaction() as (_, cur):
        return receber_ar_uc_tx(cur, me["login"], dados.titulo_id, dados.conta_id)


@router.post("/financeiro/ap/pagar", responses=common_error_responses(400, 401, 403, 422, 500))
def pagar_ap(dados: LiquidarInput, me: dict = Depends(get_current_user)):
    with db_transaction() as (_, cur):
        return pagar_ap_uc_tx(cur, me["login"], dados.titulo_id, dados.conta_id)


@router.get("/financeiro/caixa/contas")
def listar_contas_caixa(filial: str = "01", me: dict = Depends(get_current_user)):
    with db_transaction() as (_, cur):
        return listar_contas_caixa_uc_tx(cur, filial=filial)


@router.get("/financeiro/caixa/extrato")
def extrato_caixa(
    filial: str = "01",
    conta_id: int = 1,
    de: date | None = None,
    ate: date | None = None,
    me: dict = Depends(get_current_user),
):
    with db_transaction() as (_, cur):
        return extrato_caixa_uc_tx(cur, filial=filial, conta_id=conta_id, de=de, ate=ate)


@router.get("/financeiro/caixa/saldo")
def saldo_caixa(
    filial: str = "01",
    conta_id: int = 1,
    ate: date | None = None,
    me: dict = Depends(get_current_user),
):
    with db_transaction() as (_, cur):
        return saldo_caixa_uc_tx(cur, filial=filial, conta_id=conta_id, ate=ate)


@router.get("/financeiro/categorias")
def listar_categorias(filial: str = "01", ativas: bool = True, me: dict = Depends(get_current_user)):
    with db_transaction() as (_, cur):
        return listar_categorias_uc_tx(cur, filial=filial, ativas=ativas)


@router.post("/financeiro/categorias")
def criar_categoria(dados: CategoriaCreateInput, filial: str = "01", me: dict = Depends(get_current_user)):
    with db_transaction() as (_, cur):
        return criar_categoria_uc_tx(cur, usuario=me["login"], filial=filial, nome=dados.nome, tipo=dados.tipo)


@router.post("/financeiro/movimentos/categoria")
def set_categoria_mov(dados: MovSetCategoriaInput, me: dict = Depends(get_current_user)):
    with db_transaction() as (_, cur):
        return definir_categoria_mov_uc_tx(cur, usuario=me["login"], mov_id=dados.mov_id, categ_id=dados.categ_id)


@router.get("/financeiro/movimentos/{mov_id}")
def obter_movimento(mov_id: int, me: dict = Depends(get_current_user)):
    with db_transaction() as (_, cur):
        return obter_movimento_uc_tx(cur, mov_id=mov_id)


@router.get("/financeiro/relatorios/dre")
def dre_simples(
    filial: str = "01",
    de: date | None = None,
    ate: date | None = None,
    me: dict = Depends(get_current_user),
):
    with db_transaction() as (_, cur):
        return dre_simples_uc_tx(cur, filial=filial, de=de, ate=ate)
