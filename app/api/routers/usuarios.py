from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, ConfigDict

from app.api.deps import get_current_user
from app.api.schemas.errors import common_error_responses
from app.core import settings
from app.infra.db import db_transaction
from app.use_cases.usuarios_uc import criar_usuario_bootstrap_tx, criar_usuario_tx, obter_setup_status_tx

router = APIRouter(tags=["Usuários"])


class BootstrapInput(BaseModel):
    model_config = ConfigDict(json_schema_extra={"example": {"login": "admin", "senha": "Troque123!"}})

    login: str
    senha: str


class UsuarioCreateInput(BaseModel):
    model_config = ConfigDict(
        json_schema_extra={"example": {"login": "operador", "senha": "SenhaForte123!", "perfil": "user"}}
    )

    login: str
    senha: str
    perfil: str


def bootstrap_is_available() -> bool:
    return settings.BOOTSTRAP_ENABLED and settings.APP_ENV in settings.BOOTSTRAP_ALLOWED_ENVS


@router.post(
    "/bootstrap",
    responses=common_error_responses(400, 404, 422, 500),
)
def bootstrap(dados: BootstrapInput):
    # One-time setup endpoint: only exposed during explicit setup/dev windows.
    if not bootstrap_is_available():
        raise HTTPException(status_code=404, detail="Not Found")
    with db_transaction() as (_, cur):
        criar_usuario_bootstrap_tx(cur, dados.login, dados.senha)
        return {"status": "admin criado", "login": dados.login}


@router.post(
    "/usuarios",
    responses=common_error_responses(400, 401, 403, 409, 422, 500),
)
def criar_usuario(dados: UsuarioCreateInput, me: dict = Depends(get_current_user)):
    with db_transaction() as (_, cur):
        criar_usuario_tx(cur, me["login"], dados.login, dados.senha, dados.perfil)
        return {"status": "usuário criado", "login": dados.login}


@router.get(
    "/setup-status",
    responses=common_error_responses(401, 403, 500),
)
def obter_setup_status(me: dict = Depends(get_current_user)):
    with db_transaction() as (_, cur):
        return obter_setup_status_tx(cur, me["login"])
