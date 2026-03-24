class BusinessError(Exception):
    """Regra de negocio (vira HTTP 400)."""

    def __init__(self, message: str, code: str = "BUSINESS_ERROR"):
        super().__init__(message)
        self.code = code
        self.message = message


class AuthzError(Exception):
    """Sem permissao (vira HTTP 403)."""

    def __init__(self, message: str = "Sem permissao", code: str = "AUTHZ_ERROR"):
        super().__init__(message)
        self.code = code
        self.message = message


class ConflictError(Exception):
    """Conflito (vira HTTP 409)."""

    def __init__(self, message: str = "Conflito de dados", code: str = "CONFLICT_ERROR"):
        super().__init__(message)
        self.code = code
        self.message = message
