class BusinessError(Exception):
    """
    Erro de regra de negócio (vira 400/422 na API).
    """

    def __init__(self, message: str, code: str = "BUSINESS_ERROR"):
        super().__init__(message)
        self.code = code
        self.message = message


class AuthError(Exception):
    """
    Erro de autenticação/autorização (vira 401/403).
    """

    def __init__(self, message: str = "Não autorizado", code: str = "AUTH_ERROR"):
        super().__init__(message)
        self.code = code
        self.message = message
