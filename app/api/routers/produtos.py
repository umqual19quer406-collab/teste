from fastapi import APIRouter, Depends 
from pydantic import BaseModel 
 
from app.api.deps import get_current_user 
from app.infra.db import db_transaction 
from app.use_cases.produtos_uc import upsert_produto_tx, buscar_produtos_tx 
 
router = APIRouter(tags=["Produtos"]) 
 
class ProdutoInput(BaseModel): 
    cod: str 
    desc: str 
    preco: float 
    filial: str = "01" 
 
@router.post("/produto") 
def upsert_produto(dados: ProdutoInput, me: dict = Depends(get_current_user)): 
    with db_transaction() as (_, cur): 
        return upsert_produto_tx(cur, me["login"], dados.cod, dados.desc, dados.preco, dados.filial)


@router.get("/produtos/buscar")
def buscar_produtos(q: str, filial: str = "01", limite: int = 20, me: dict = Depends(get_current_user)):
    with db_transaction() as (_, cur):
        return buscar_produtos_tx(cur, filial=filial, q=q, limite=limite)
