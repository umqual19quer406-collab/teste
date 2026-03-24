from typing import Optional

from fastapi import APIRouter, Depends
from pydantic import BaseModel, ConfigDict

from app.api.deps import get_current_user
from app.api.schemas.errors import common_error_responses
from app.infra.db import db_transaction
from app.use_cases.reservas_uc import cancelar_reserva_tx, confirmar_reserva_tx, criar_reserva_tx

router = APIRouter(prefix="/reserva", tags=["Reserva"])


class ReservaInput(BaseModel):
    model_config = ConfigDict(
        json_schema_extra={"example": {"cod": "PROD002", "qtd": 2, "filial": "01", "cliente_cod": "C0002", "tabela_cod": "0001"}}
    )

    cod: str
    qtd: int
    filial: str = "01"
    cliente_cod: str | None = None
    tabela_cod: str = "0001"


class ConfirmarInput(BaseModel):
    model_config = ConfigDict(
        json_schema_extra={"example": {"reserva_id": 301, "cliente_cod": "C0002", "venc_dias": 20, "tes_cod": "001"}}
    )

    reserva_id: int
    cliente_cod: Optional[str] = None
    venc_dias: int = 30
    tes_cod: Optional[str] = "001"


class CancelarInput(BaseModel):
    model_config = ConfigDict(json_schema_extra={"example": {"reserva_id": 301}})

    reserva_id: int


@router.post("", responses=common_error_responses(400, 401, 403, 422, 500))
def criar(dados: ReservaInput, me: dict = Depends(get_current_user)):
    with db_transaction() as (_, cur):
        cod = (dados.cod or "").strip()
        filial = (dados.filial or "").strip()
        tabela_cod = (getattr(dados, "tabela_cod", None) or "0001").strip()
        cliente_cod = (getattr(dados, "cliente_cod", None) or None)
        if isinstance(cliente_cod, str):
            cliente_cod = cliente_cod.strip() or None

        return criar_reserva_tx(
            cur,
            usuario=me["login"],
            produto=cod,
            qtd=dados.qtd,
            filial=filial,
            cliente_cod=cliente_cod,
            tabela_cod=tabela_cod,
        )


@router.post("/cancelar", responses=common_error_responses(400, 401, 403, 422, 500))
def cancelar(dados: CancelarInput, me: dict = Depends(get_current_user)):
    with db_transaction() as (_, cur):
        return cancelar_reserva_tx(cur, me["login"], dados.reserva_id)


@router.post("/confirmar", responses=common_error_responses(400, 401, 403, 422, 500))
def confirmar(dados: ConfirmarInput, me: dict = Depends(get_current_user)):
    with db_transaction() as (_, cur):
        return confirmar_reserva_tx(cur, me["login"], dados.reserva_id, dados.cliente_cod, dados.venc_dias, dados.tes_cod)
