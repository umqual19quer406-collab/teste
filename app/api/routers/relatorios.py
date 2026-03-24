from fastapi import APIRouter, Depends 
from datetime import date 
 
from app.api.deps import get_current_user 
from app.infra.db import db_transaction 
from app.infra.repositories.relatorios_repo import dre_simples_tx, margem_por_produto_tx 
from app.use_cases.conciliacao_nf_uc import conciliacao_nf_financeiro_uc_tx
from app.use_cases.consistencia_uc import consistencia_fiscal_uc_tx
 
router = APIRouter(tags=["Relatórios"]) 
 
@router.get("/relatorios/dre") 
def dre(filial: str="01", de: date | None=None, ate: date | None=None, me=Depends(get_current_user)): 
    with db_transaction() as (_, cur): 
        return dre_simples_tx(cur, filial, de, ate) 
 
@router.get("/relatorios/margem-produto") 
def margem_produto(filial: str="01", de: date | None=None, ate: date | None=None, 
me=Depends(get_current_user)): 
    with db_transaction() as (_, cur): 
        return margem_por_produto_tx(cur, filial, de, ate) 


@router.get("/relatorios/conciliacao-nf")
def conciliacao_nf(
    filial: str = "01",
    de: date | None = None,
    ate: date | None = None,
    tolerancia: float = 0.01,
    limit: int = 200,
    me=Depends(get_current_user),
):
    with db_transaction() as (_, cur):
        return conciliacao_nf_financeiro_uc_tx(
            cur,
            usuario=me["login"],
            filial=filial,
            de=de,
            ate=ate,
            tolerancia=float(tolerancia),
            limit=int(limit),
        )


@router.get("/relatorios/consistencia-fiscal")
def consistencia_fiscal(
    filial: str = "01",
    de: date | None = None,
    ate: date | None = None,
    limit: int = 200,
    me=Depends(get_current_user),
):
    with db_transaction() as (_, cur):
        return consistencia_fiscal_uc_tx(
            cur,
            usuario=me["login"],
            filial=filial,
            de=de,
            ate=ate,
            limit=int(limit),
        )
