from __future__ import annotations 
from typing import Optional, List, Dict, Any 
from app.infra.db import fetchone_dict, fetchall_dict 
from app.core.exceptions import BusinessError 
 
def sa1_get_tx(cur, filial: str, cod: str) -> Optional[Dict[str, Any]]: 
    cur.execute(""" 
        SELECT * 
        FROM dbo.SA1_CLIENTES 
        WHERE A1_FILIAL = ? AND A1_COD = ? 
          AND (D_E_L_E_T_ IS NULL OR D_E_L_E_T_ <> '*') 
    """, (filial, cod)) 
    return fetchone_dict(cur) 
 
def sa1_listar_tx(cur, filial: str, ativos: bool = True, limit: int = 200) -> List[Dict[str, Any]]: 
    if ativos: 
        cur.execute(""" 
            SELECT TOP (?) * 
            FROM dbo.SA1_CLIENTES 
            WHERE A1_FILIAL = ? AND A1_ATIVO = 1 
              AND (D_E_L_E_T_ IS NULL OR D_E_L_E_T_ <> '*') 
            ORDER BY A1_NOME 
        """, (int(limit), filial)) 
    else: 
        cur.execute(""" 
            SELECT TOP (?) * 
            FROM dbo.SA1_CLIENTES 
            WHERE A1_FILIAL = ? 
              AND (D_E_L_E_T_ IS NULL OR D_E_L_E_T_ <> '*') 
            ORDER BY A1_NOME 
        """, (int(limit), filial)) 
    return fetchall_dict(cur) 
 
def sa1_buscar_tx(cur, filial: str, termo: str, limit: int = 50) -> List[Dict[str, Any]]: 
    termo = (termo or "").strip() 
    if not termo: 
        return [] 
    like = f"%{termo}%" 
    cur.execute(""" 
        SELECT TOP (?) * 
        FROM dbo.SA1_CLIENTES 
        WHERE A1_FILIAL = ? 
          AND (D_E_L_E_T_ IS NULL OR D_E_L_E_T_ <> '*') 
          AND (A1_COD LIKE ? OR A1_NOME LIKE ? OR A1_DOC LIKE ? OR A1_EMAIL LIKE ?) 
        ORDER BY A1_NOME 
    """, (int(limit), filial, like, like, like, like)) 
    return fetchall_dict(cur) 
 
def sa1_criar_tx( 
    cur, 
    filial: str, 
    cod: str, 
    nome: str, 
    doc: Optional[str] = None, 
    email: Optional[str] = None, 
    fone: Optional[str] = None, 
) -> Dict[str, Any]: 
    cod = (cod or "").strip() 
    nome = (nome or "").strip() 
    doc = (doc or None) 
    email = (email or None) 
    fone = (fone or None) 
 
    if not cod: 
        raise BusinessError("A1_COD é obrigatório") 
    if not nome: 
        raise BusinessError("A1_NOME é obrigatório") 
 
    # evita sobrescrever sem querer 
    existe = sa1_get_tx(cur, filial=filial, cod=cod) 
    if existe: 
        raise BusinessError("Cliente já existe nesta filial") 
 
    cur.execute(""" 
        INSERT INTO dbo.SA1_CLIENTES (A1_COD, A1_FILIAL, A1_NOME, A1_DOC, A1_EMAIL, A1_FONE, 
A1_ATIVO) 
        VALUES (?, ?, ?, ?, ?, ?, 1) 
    """, (cod, filial, nome, doc, email, fone)) 
 
    return sa1_get_tx(cur, filial=filial, cod=cod) or {"A1_COD": cod, "A1_FILIAL": filial} 
 
def sa1_atualizar_tx( 
    cur, 
    filial: str, 
    cod: str, 
    nome: Optional[str] = None, 
    doc: Optional[str] = None, 
    email: Optional[str] = None, 
    fone: Optional[str] = None, 
) -> Dict[str, Any]: 
    atual = sa1_get_tx(cur, filial=filial, cod=cod) 
    if not atual: 
        raise BusinessError("Cliente não encontrado") 
 
    # mantém valores atuais quando None 
    nome2 = atual["A1_NOME"] if nome is None else (nome or "").strip() 
    doc2 = atual.get("A1_DOC") if doc is None else (doc or None) 
    email2 = atual.get("A1_EMAIL") if email is None else (email or None) 
    fone2 = atual.get("A1_FONE") if fone is None else (fone or None) 
 
    if not nome2: 
        raise BusinessError("A1_NOME não pode ficar vazio") 
 
    cur.execute(""" 
        UPDATE dbo.SA1_CLIENTES 
        SET A1_NOME=?, A1_DOC=?, A1_EMAIL=?, A1_FONE=? 
        WHERE A1_FILIAL=? AND A1_COD=? 
    """, (nome2, doc2, email2, fone2, filial, cod)) 
 
    return sa1_get_tx(cur, filial=filial, cod=cod) or atual 
 
def sa1_set_ativo_tx(cur, filial: str, cod: str, ativo: bool) -> None: 
    cur.execute(""" 
        UPDATE dbo.SA1_CLIENTES 
        SET A1_ATIVO=? 
        WHERE A1_FILIAL=? AND A1_COD=? 
    """, (1 if ativo else 0, filial, cod)) 
    if cur.rowcount == 0: 
        raise BusinessError("Cliente não encontrado")
