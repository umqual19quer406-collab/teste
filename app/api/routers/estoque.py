from fastapi import APIRouter, Depends 
from pydantic import BaseModel 
from typing import Optional 
 
from app.api.deps import get_current_user 
from app.infra.db import db_transaction 
from app.use_cases.estoque_uc import entrada_estoque_tx, consultar_estoque_tx, extrato_sd3_uc_tx 
from app.use_cases.conciliacao_uc import recalcular_sb1_por_sd3_tx 
 
router = APIRouter(tags=["Estoque"]) 
 
class EntradaInput(BaseModel): 
    cod: str 
    qtd: int 
    filial: str = "01" 
    custo_unit: float = 0.0 
    forn: Optional[str] = None 
    venc_dias: int = 30 
 
class RecalcularInput(BaseModel): 
    filial: str = "01" 
 
@router.post("/estoque/entrada") 
def entrada(dados: EntradaInput, me: dict = Depends(get_current_user)): 
    with db_transaction() as (_, cur): 
        return entrada_estoque_tx(cur, me["login"], dados.cod, dados.qtd, dados.filial, dados.custo_unit, 
dados.forn, dados.venc_dias) 
 
@router.get("/estoque/{cod}") 
def consultar(cod: str, filial: str = "01", me: dict = Depends(get_current_user)): 
    with db_transaction() as (_, cur): 
        return consultar_estoque_tx(cur, cod, filial) 
 
@router.get("/estoque/extrato/{cod}") 
def extrato(cod: str, filial: str = "01", limite: int = 100, me: dict = Depends(get_current_user)): 
    with db_transaction() as (_, cur): 
        return extrato_sd3_uc_tx(cur, cod, filial, limite) 
 
@router.post("/estoque/recalcular") 
def recalcular(dados: RecalcularInput, me: dict = Depends(get_current_user)): 
    with db_transaction() as (_, cur): 
        return recalcular_sb1_por_sd3_tx(cur, me["login"], dados.filial)