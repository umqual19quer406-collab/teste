from uuid import uuid4

from fastapi import FastAPI, HTTPException, Request
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from app.api.schemas.errors import build_error_response
from app.api.routers import (
    ap_lancamento,
    alertas,
    auditoria,
    auth,
    clientes,
    estoque,
    financeiro,
    fornecedores,
    parametros,
    parceiros,
    precos,
    produtos,
    relatorios,
    reservas,
    usuarios,
)
from app.api.routers.vendas import router as vendas_router
from app.core import settings
from app.infra.db import set_current_request
from app.core.exceptions import (
    AuthzError,
    BusinessError as CoreBusinessError,
    ConflictError,
)
from app.domain.errors import AuthError, BusinessError as DomainBusinessError

app = FastAPI(title=settings.APP_TITLE)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ALLOW_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/healthz", tags=["Health"])
def healthcheck():
    return {"status": "ok"}


@app.middleware("http")
async def request_context_middleware(request: Request, call_next):
    req_id = request.headers.get("X-Request-Id") or str(uuid4())
    request.state.request_id = req_id
    set_current_request(req_id, request.url.path)
    response = await call_next(request)
    response.headers["X-Request-Id"] = req_id
    return response


def _request_id(request: Request) -> str | None:
    return getattr(request.state, "request_id", None)


@app.exception_handler(CoreBusinessError)
@app.exception_handler(DomainBusinessError)
def business_error_handler(request: Request, exc: Exception):
    return JSONResponse(
        status_code=400,
        content=build_error_response(
            detail=str(exc),
            code=getattr(exc, "code", "BUSINESS_ERROR"),
            error_type="business",
            request_id=_request_id(request),
        ),
    )


@app.exception_handler(AuthError)
def auth_error_handler(request: Request, exc: AuthError):
    return JSONResponse(
        status_code=401,
        content=build_error_response(
            detail=exc.message,
            code=exc.code,
            error_type="auth",
            request_id=_request_id(request),
        ),
    )


@app.exception_handler(AuthzError)
def authz_error_handler(request: Request, exc: AuthzError):
    return JSONResponse(
        status_code=403,
        content=build_error_response(
            detail=exc.message,
            code=exc.code,
            error_type="authorization",
            request_id=_request_id(request),
        ),
    )


@app.exception_handler(ConflictError)
def conflict_handler(request: Request, exc: ConflictError):
    return JSONResponse(
        status_code=409,
        content=build_error_response(
            detail=exc.message,
            code=exc.code,
            error_type="conflict",
            request_id=_request_id(request),
        ),
    )


@app.exception_handler(HTTPException)
def http_exception_handler(request: Request, exc: HTTPException):
    detail = exc.detail if isinstance(exc.detail, str) else "Erro HTTP"
    return JSONResponse(
        status_code=exc.status_code,
        content=build_error_response(
            detail=detail,
            code=f"HTTP_{exc.status_code}",
            error_type="http",
            request_id=_request_id(request),
        ),
    )


@app.exception_handler(RequestValidationError)
def validation_handler(request: Request, exc: RequestValidationError):
    first_error = exc.errors()[0] if exc.errors() else {}
    loc = ".".join(str(part) for part in first_error.get("loc", []))
    msg = first_error.get("msg", "Payload inválido")
    detail = f"Payload inválido: {loc} - {msg}" if loc else f"Payload inválido: {msg}"
    return JSONResponse(
        status_code=422,
        content=build_error_response(
            detail=detail,
            code="VALIDATION_ERROR",
            error_type="validation",
            request_id=_request_id(request),
        ),
    )


@app.exception_handler(Exception)
def generic_handler(request: Request, __: Exception):
    return JSONResponse(
        status_code=500,
        content=build_error_response(
            detail="Erro interno",
            code="INTERNAL_ERROR",
            error_type="internal",
            request_id=_request_id(request),
        ),
    )


app.include_router(auth.router)
app.include_router(usuarios.router)
app.include_router(alertas.router)
app.include_router(produtos.router)
app.include_router(estoque.router)
app.include_router(reservas.router)
app.include_router(financeiro.router)
app.include_router(auditoria.router)
app.include_router(parceiros.router)
app.include_router(precos.router)
app.include_router(relatorios.router)
app.include_router(clientes.router)
app.include_router(fornecedores.router)
app.include_router(ap_lancamento.router)
app.include_router(parametros.router)
app.include_router(vendas_router)
