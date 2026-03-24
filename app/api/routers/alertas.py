from fastapi import APIRouter, Depends
from pydantic import BaseModel, ConfigDict

from app.api.deps import get_current_user
from app.api.schemas.errors import common_error_responses
from app.infra.db import db_transaction
from app.use_cases.alertas_uc import listar_alertas_uc_tx

router = APIRouter(tags=["Alertas"])


class AlertItem(BaseModel):
    code: str
    severity: str
    title: str
    text: str
    route: str | None = None
    count: int | None = None
    action_label: str | None = None
    business_context: str | None = None


class AlertSummary(BaseModel):
    critical: int
    warning: int
    info: int
    total: int


class AlertResponse(BaseModel):
    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "filial": "01",
                "usuario": "admin",
                "generated_at": "2026-03-23T17:10:00",
                "summary": {"critical": 1, "warning": 2, "info": 0, "total": 3},
                "items": [
                    {
                        "code": "AR_OVERDUE",
                        "severity": "critical",
                        "title": "Recebiveis vencidos",
                        "text": "3 titulo(s) de contas a receber estao vencidos e seguem em aberto na filial 01.",
                        "route": "/financeiro/ar",
                        "count": 3,
                        "action_label": "Abrir recebiveis",
                        "business_context": "financeiro.ar.overdue",
                    }
                ],
            }
        }
    )

    filial: str
    usuario: str
    generated_at: str
    summary: AlertSummary
    items: list[AlertItem]


@router.get(
    "/alertas",
    response_model=AlertResponse,
    responses=common_error_responses(401, 403, 500),
)
def listar_alertas(filial: str = "01", me: dict = Depends(get_current_user)):
    with db_transaction() as (_, cur):
        return listar_alertas_uc_tx(cur, login=me["login"], perfil=me["perfil"], filial=filial)
