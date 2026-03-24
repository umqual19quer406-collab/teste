from __future__ import annotations

from fastapi import APIRouter, Depends
from pydantic import BaseModel, ConfigDict

from app.api.deps import get_current_user
from app.api.schemas.errors import common_error_responses
from app.infra.db import db_transaction
from app.use_cases.ap_lancamento_uc import lancar_ap_uc_tx

router = APIRouter(prefix="/ap", tags=["AP (Lançamento)"])


class APLancarInput(BaseModel):
    model_config = ConfigDict(
        json_schema_extra={"example": {"forn_cod": "F0001", "valor": 80.0, "ref": "MANUAL-1", "venc_dias": 15, "filial": "01"}}
    )

    forn_cod: str
    valor: float
    ref: str = "MANUAL"
    venc_dias: int = 30
    filial: str = "01"


@router.post("/lancar", responses=common_error_responses(400, 401, 403, 422, 500))
def lancar(dados: APLancarInput, me: dict = Depends(get_current_user)):
    with db_transaction() as (_, cur):
        return lancar_ap_uc_tx(
            cur,
            usuario=me["login"],
            filial=dados.filial,
            forn_cod=dados.forn_cod,
            valor=dados.valor,
            ref=dados.ref,
            venc_dias=dados.venc_dias,
        )
