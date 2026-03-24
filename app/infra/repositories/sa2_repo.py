from __future__ import annotations 
 
from typing import Optional, List, Dict, Any 
from app.infra.db import fetchone_dict, fetchall_dict 
from app.core.exceptions import BusinessError 
 
def sa2_get_tx(cur, filial: str, cod: str) -> Optional[Dict[str, Any]]: 
    cur.execute(""" 
        SELECT * 
        FROM dbo.SA2_FORNECEDORES 
        WHERE A2_FILIAL = ? AND A2_COD = ? 
          AND (D_E_L_E_T_ IS NULL OR D_E_L_E_T_ <> '*') 
    """, (filial, cod)) 
    return fetchone_dict(cur) 
 
def sa2_listar_tx(cur, filial: str, ativos: bool = True, limit: int = 200) -> List[Dict[str, Any]]: 
    if ativos: 
        cur.execute(""" 
            SELECT TOP (?) * 
            FROM dbo.SA2_FORNECEDORES 
            WHERE A2_FILIAL = ? AND A2_ATIVO = 1 
              AND (D_E_L_E_T_ IS NULL OR D_E_L_E_T_ <> '*') 
            ORDER BY A2_NOME 
        """, (int(limit), filial)) 
    else: 
        cur.execute(""" 
            SELECT TOP (?) * 
            FROM dbo.SA2_FORNECEDORES 
            WHERE A2_FILIAL = ? 
              AND (D_E_L_E_T_ IS NULL OR D_E_L_E_T_ <> '*') 
            ORDER BY A2_NOME 
        """, (int(limit), filial)) 
    return fetchall_dict(cur) 
 
def sa2_buscar_tx(cur, filial: str, termo: str, limit: int = 50) -> List[Dict[str, Any]]: 
    termo = (termo or "").strip() 
    if not termo: 
        return [] 
    like = f"%{termo}%" 
    cur.execute(""" 
        SELECT TOP (?) * 
        FROM dbo.SA2_FORNECEDORES 
        WHERE A2_FILIAL = ? 
          AND (D_E_L_E_T_ IS NULL OR D_E_L_E_T_ <> '*') 
          AND (A2_COD LIKE ? OR A2_NOME LIKE ? OR A2_DOC LIKE ? OR A2_EMAIL LIKE ?) 
        ORDER BY A2_NOME 
    """, (int(limit), filial, like, like, like, like)) 
    return fetchall_dict(cur) 
 
def sa2_criar_tx( 
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
        raise BusinessError("A2_COD é obrigatório") 
    if not nome: 
        raise BusinessError("A2_NOME é obrigatório") 
 
    existe = sa2_get_tx(cur, filial=filial, cod=cod) 
    if existe: 
        raise BusinessError("Fornecedor já existe nesta filial") 
 
    cur.execute(""" 
        INSERT INTO dbo.SA2_FORNECEDORES (A2_COD, A2_FILIAL, A2_NOME, A2_DOC, A2_EMAIL, 
A2_FONE, A2_ATIVO) 
        VALUES (?, ?, ?, ?, ?, ?, 1) 
    """, (cod, filial, nome, doc, email, fone)) 
 
    return sa2_get_tx(cur, filial=filial, cod=cod) or {"A2_COD": cod, "A2_FILIAL": filial} 
 
def sa2_atualizar_tx( 
    cur, 
    filial: str, 
    cod: str, 
    nome: Optional[str] = None, 
    doc: Optional[str] = None, 
    email: Optional[str] = None, 
    fone: Optional[str] = None, 
) -> Dict[str, Any]: 
    atual = sa2_get_tx(cur, filial=filial, cod=cod) 
    if not atual: 
        raise BusinessError("Fornecedor não encontrado") 
 
    nome2 = atual["A2_NOME"] if nome is None else (nome or "").strip() 
    doc2 = atual.get("A2_DOC") if doc is None else (doc or None) 
    email2 = atual.get("A2_EMAIL") if email is None else (email or None) 
    fone2 = atual.get("A2_FONE") if fone is None else (fone or None) 
 
    if not nome2: 
        raise BusinessError("A2_NOME não pode ficar vazio") 
 
    cur.execute(""" 
        UPDATE dbo.SA2_FORNECEDORES 
        SET A2_NOME=?, A2_DOC=?, A2_EMAIL=?, A2_FONE=? 
        WHERE A2_FILIAL=? AND A2_COD=? 
    """, (nome2, doc2, email2, fone2, filial, cod)) 
 
    return sa2_get_tx(cur, filial=filial, cod=cod) or atual 
 
def sa2_set_ativo_tx(cur, filial: str, cod: str, ativo: bool) -> None: 
    cur.execute(""" 
        UPDATE dbo.SA2_FORNECEDORES 
        SET A2_ATIVO=? 
        WHERE A2_FILIAL=? AND A2_COD=? 
    """, (1 if ativo else 0, filial, cod)) 
    if cur.rowcount == 0: 
        raise BusinessError("Fornecedor não encontrado")
