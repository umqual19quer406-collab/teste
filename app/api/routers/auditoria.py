from fastapi import APIRouter, Depends
from app.api.deps import get_current_user
from app.infra.db import db_transaction
from app.use_cases.auditoria_uc import listar_logs_uc_tx

router = APIRouter(tags=["Auditoria"])

@router.get("/auditoria")
def auditoria(me: dict = Depends(get_current_user)):
    with db_transaction() as (_, cur):
        return listar_logs_uc_tx(cur, me["login"])