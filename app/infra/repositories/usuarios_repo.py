from app.infra.db import fetchone_dict 
 
def usuarios_existem_tx(cur) -> bool: 
    cur.execute("SELECT TOP 1 1 AS X FROM USUARIOS") 
    return cur.fetchone() is not None 
 
def inserir_usuario_tx(cur, login: str, senha_hash: str, perfil: str) -> None: 
    cur.execute( 
        "INSERT INTO USUARIOS (U_LOGIN, U_SENHA_HASH, U_PERFIL) VALUES (?, ?, ?)", 
        (login, senha_hash, perfil), 
    ) 
 
def obter_usuario_por_login_tx(cur, login: str): 
    cur.execute("SELECT * FROM USUARIOS WHERE U_LOGIN=?", (login,)) 
    return fetchone_dict(cur) 
 
def obter_perfil_tx(cur, login: str) -> str: 
    cur.execute("SELECT U_PERFIL FROM USUARIOS WHERE U_LOGIN=?", (login,)) 
    row = fetchone_dict(cur) 
    return row["U_PERFIL"] if row else None 
