from passlib.context import CryptContext 
 
_pwd_ctx = CryptContext( 
    schemes=["pbkdf2_sha256"], 
    deprecated="auto" 
) 
 
def hash_password(password: str) -> str: 
    return _pwd_ctx.hash(password) 
 
def verify_password(password: str, password_hash: str) -> bool: 
    return _pwd_ctx.verify(password, password_hash)