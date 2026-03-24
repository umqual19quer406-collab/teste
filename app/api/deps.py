from datetime import datetime, timedelta, timezone
from fastapi import Depends, HTTPException
from fastapi.security import OAuth2PasswordBearer
from jose import jwt, JWTError

from app.core import settings
from app.infra.db import set_current_user

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="login")


def create_access_token(data: dict, expires_minutes: int = settings.JWT_EXPIRE_MINUTES) -> str:
    to_encode = data.copy()
    expire = datetime.now(timezone.utc) + timedelta(minutes=expires_minutes)
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, settings.JWT_SECRET_KEY, algorithm=settings.JWT_ALGORITHM)


def get_current_user(token: str = Depends(oauth2_scheme)) -> dict:
    try:
        payload = jwt.decode(
            token,
            settings.JWT_SECRET_KEY,
            algorithms=[settings.JWT_ALGORITHM],
        )
        login: str = payload.get("sub")
        perfil: str = payload.get("perfil")
        if not login or not perfil:
            raise HTTPException(status_code=401, detail="Token inválido")
        set_current_user(login)
        return {"login": login, "perfil": perfil}
    except JWTError:
        raise HTTPException(status_code=401, detail="Token inválido ou expirado")
