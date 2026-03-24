import os


def _to_bool(value: str | None, default: bool = False) -> bool:
    if value is None:
        return default
    return value.strip().lower() in {"1", "true", "yes", "on"}


def _require_safe_jwt_secret(app_env: str, secret: str) -> str:
    secret = (secret or "").strip()
    if app_env == "production" and secret in {"", "dev-only-change-me", "change-me-in-production"}:
        raise RuntimeError(
            "JWT_SECRET_KEY must be explicitly set to a non-default value when APP_ENV=production."
        )
    return secret


APP_TITLE = os.getenv("APP_TITLE", "Mini Protheus - ERP (SQL Server + JWT)")
APP_ENV = os.getenv("APP_ENV", "production").strip().lower() or "production"

JWT_SECRET_KEY = _require_safe_jwt_secret(APP_ENV, os.getenv("JWT_SECRET_KEY", "dev-only-change-me"))
JWT_ALGORITHM = os.getenv("JWT_ALGORITHM", "HS256")
JWT_EXPIRE_MINUTES = int(os.getenv("JWT_EXPIRE_MINUTES", "240"))
BOOTSTRAP_ENABLED = _to_bool(os.getenv("BOOTSTRAP_ENABLED"), default=False)
BOOTSTRAP_ALLOWED_ENVS = {"development", "setup"}
BOOTSTRAP_POLICY = (
    "One-time setup: /bootstrap only responds in development/setup environments, "
    "must be explicitly enabled, and is permanently blocked by business rule after "
    "the first user exists."
)
CORS_ALLOW_ORIGINS = [
    origin.strip()
    for origin in os.getenv("CORS_ALLOW_ORIGINS", "http://localhost:5173").split(",")
    if origin.strip()
]

DB_CONN_STR = os.getenv(
    "DB_CONN_STR",
    (
        "DRIVER={ODBC Driver 18 for SQL Server};"
        "SERVER=localhost;"
        "DATABASE=ERP_PROTHEUS;"
        "Trusted_Connection=yes;"
        "Encrypt=yes;"
        "TrustServerCertificate=yes;"
    ),
)
