from fastapi import status
from pydantic import BaseModel


class ErrorResponse(BaseModel):
    detail: str
    code: str
    error_type: str
    request_id: str | None = None


def build_error_response(
    *,
    detail: str,
    code: str,
    error_type: str,
    request_id: str | None,
) -> dict:
    return {
        "detail": detail,
        "code": code,
        "error_type": error_type,
        "request_id": request_id,
    }


def common_error_responses(*status_codes: int) -> dict[int, dict]:
    examples = {
        status.HTTP_400_BAD_REQUEST: {
            "description": "Falha de regra de negócio.",
            "content": {
                "application/json": {
                    "example": {
                        "detail": "Pedido sem itens (SC6)",
                        "code": "BUSINESS_ERROR",
                        "error_type": "business",
                        "request_id": "6df2d507-cf4a-4d85-b8db-7b8f81993db0",
                    }
                }
            },
        },
        status.HTTP_401_UNAUTHORIZED: {
            "description": "Falha de autenticação.",
            "content": {
                "application/json": {
                    "example": {
                        "detail": "Token inválido ou expirado",
                        "code": "AUTH_ERROR",
                        "error_type": "auth",
                        "request_id": "6df2d507-cf4a-4d85-b8db-7b8f81993db0",
                    }
                }
            },
        },
        status.HTTP_403_FORBIDDEN: {
            "description": "Acesso negado.",
            "content": {
                "application/json": {
                    "example": {
                        "detail": "Sem permissão. Perfil atual: user",
                        "code": "AUTHZ_ERROR",
                        "error_type": "authorization",
                        "request_id": "6df2d507-cf4a-4d85-b8db-7b8f81993db0",
                    }
                }
            },
        },
        status.HTTP_404_NOT_FOUND: {
            "description": "Recurso não encontrado ou endpoint indisponível nesse ambiente.",
            "content": {
                "application/json": {
                    "example": {
                        "detail": "Not Found",
                        "code": "HTTP_404",
                        "error_type": "http",
                        "request_id": "6df2d507-cf4a-4d85-b8db-7b8f81993db0",
                    }
                }
            },
        },
        status.HTTP_409_CONFLICT: {
            "description": "Conflito de dados.",
            "content": {
                "application/json": {
                    "example": {
                        "detail": "Conflito de dados",
                        "code": "CONFLICT_ERROR",
                        "error_type": "conflict",
                        "request_id": "6df2d507-cf4a-4d85-b8db-7b8f81993db0",
                    }
                }
            },
        },
        status.HTTP_422_UNPROCESSABLE_CONTENT: {
            "description": "Payload inválido.",
            "content": {
                "application/json": {
                    "example": {
                        "detail": "Payload inválido: body.qtd - Input should be greater than or equal to 1",
                        "code": "VALIDATION_ERROR",
                        "error_type": "validation",
                        "request_id": "6df2d507-cf4a-4d85-b8db-7b8f81993db0",
                    }
                }
            },
        },
        status.HTTP_500_INTERNAL_SERVER_ERROR: {
            "description": "Erro interno.",
            "content": {
                "application/json": {
                    "example": {
                        "detail": "Erro interno",
                        "code": "INTERNAL_ERROR",
                        "error_type": "internal",
                        "request_id": "6df2d507-cf4a-4d85-b8db-7b8f81993db0",
                    }
                }
            },
        },
    }

    response_map: dict[int, dict] = {}
    for status_code in status_codes:
        normalized_status = status.HTTP_422_UNPROCESSABLE_CONTENT if status_code == 422 else status_code
        response_map[status_code] = {
            "model": ErrorResponse,
            **examples[normalized_status],
        }
    return response_map
