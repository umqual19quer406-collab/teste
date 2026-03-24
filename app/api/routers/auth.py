from fastapi import APIRouter, Depends
from fastapi.security import OAuth2PasswordRequestForm

from app.api.deps import create_access_token
from app.api.schemas.errors import common_error_responses
from app.infra.db import db_transaction
from app.use_cases.auth_uc import autenticar_usuario_tx


router = APIRouter(tags=["Auth"])

@router.post("/login", responses=common_error_responses(401, 422, 500))
def login(form_data: OAuth2PasswordRequestForm = Depends()):
    with db_transaction() as (_, cur):
        user = autenticar_usuario_tx(cur, form_data.username, form_data.password)
        token = create_access_token({"sub": user["U_LOGIN"], "perfil": user["U_PERFIL"]})
        return {"access_token": token, "token_type": "bearer"}
    
