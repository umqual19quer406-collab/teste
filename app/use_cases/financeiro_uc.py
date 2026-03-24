from __future__ import annotations

from datetime import date
from typing import Any, Dict

import pyodbc

from app.domain.errors import BusinessError
from app.infra.repositories.financeiro_repo import (
    criar_categoria_tx,
    definir_categoria_mov_tx,
    dre_simples_tx,
    extrato_caixa_tx,
    listar_ap_tx,
    listar_ar_tx,
    listar_categorias_tx,
    listar_contas_caixa_tx,
    obter_movimento_tx,
    pagar_ap_e_gerar_caixa_tx,
    receber_ar_e_gerar_caixa_tx,
    saldo_caixa_simples_tx,
)
from app.infra.repositories.logs_repo import log_tx


def listar_ar_uc_tx(cur, filial: str, status: str = "ABERTO"):
    return listar_ar_tx(cur, filial=filial, status=status)


def listar_ap_uc_tx(cur, usuario: str, filial: str, status: str = "ABERTO"):
    return listar_ap_tx(cur, filial=filial, status=status)


def receber_ar_uc_tx(cur, usuario: str, titulo_id: int, conta_id: int) -> dict:
    mov_id = receber_ar_e_gerar_caixa_tx(
        cur,
        titulo_id=int(titulo_id),
        conta_id=int(conta_id),
        usuario=usuario,
    )
    log_tx(cur, usuario, f"AR recebido id={titulo_id} se5={mov_id}")
    return {
        "titulo_id": int(titulo_id),
        "status": "BAIXADO",
        "se5_id": int(mov_id),
    }


def pagar_ap_uc_tx(cur: pyodbc.Cursor, usuario: str, titulo_id: int, conta_id: int) -> Dict[str, Any]:
    """
    Paga um título do AP (SF1) e gera movimento de caixa (SE5) na mesma transação.
    """

    mov_id = pagar_ap_e_gerar_caixa_tx(
        cur,
        titulo_id=int(titulo_id),
        conta_id=int(conta_id),
        usuario=usuario,
    )
    log_tx(cur, usuario, f"AP pago id={titulo_id} se5={mov_id}")
    return {
        "id": int(titulo_id),
        "status": "BAIXADO",
        "se5_id": int(mov_id),
        "conta_id": int(conta_id),
    }


def listar_contas_caixa_uc_tx(cur, filial: str):
    return listar_contas_caixa_tx(cur, filial=filial)


def listar_categorias_uc_tx(cur, filial: str, ativas: bool = True):
    return listar_categorias_tx(cur, filial=filial, ativas=ativas)


def criar_categoria_uc_tx(cur, usuario: str, filial: str, nome: str, tipo: str):
    tipo = (tipo or "").upper().strip()
    if tipo not in {"RECEITA", "DESPESA", "CUSTO", "TRANSFERENCIA", "OUTROS"}:
        raise BusinessError("Tipo de categoria inválido")
    cat_id = criar_categoria_tx(cur, filial=filial, nome=nome.strip(), tipo=tipo)
    log_tx(cur, usuario, f"FIN.SE5.CATEG.CRIAR id={cat_id} filial={filial} tipo={tipo} nome={nome}")
    return {"id": cat_id, "filial": filial, "tipo": tipo, "nome": nome}


def definir_categoria_mov_uc_tx(cur, usuario: str, mov_id: int, categ_id: int | None):
    definir_categoria_mov_tx(
        cur,
        mov_id=int(mov_id),
        categ_id=(int(categ_id) if categ_id is not None else None),
    )
    log_tx(cur, usuario, f"FIN.SE5.MOV.SETCATEG mov_id={mov_id} categ_id={categ_id}")
    return {"mov_id": int(mov_id), "categ_id": (int(categ_id) if categ_id is not None else None)}


def obter_movimento_uc_tx(cur, mov_id: int):
    mov = obter_movimento_tx(cur, mov_id=int(mov_id))
    if not mov:
        raise BusinessError("Movimento não encontrado")
    if "E5_VALOR" in mov and mov["E5_VALOR"] is not None:
        mov["E5_VALOR"] = float(mov["E5_VALOR"])
    return mov


def extrato_caixa_uc_tx(cur, filial: str, conta_id: int, de: date | None, ate: date | None):
    rows = extrato_caixa_tx(cur, filial=filial, conta_id=int(conta_id), de=de, ate=ate)
    for r in rows:
        if "E5_VALOR" in r:
            r["E5_VALOR"] = float(r["E5_VALOR"])
        if "E5_VALOR_ASSINADO" in r:
            r["E5_VALOR_ASSINADO"] = float(r["E5_VALOR_ASSINADO"])
        if "E5_SALDO_ACUMULADO" in r:
            r["E5_SALDO_ACUMULADO"] = float(r["E5_SALDO_ACUMULADO"])
    return rows


def saldo_caixa_uc_tx(cur, filial: str, conta_id: int, ate: date | None):
    s = saldo_caixa_simples_tx(cur, filial=filial, conta_id=int(conta_id), ate=ate)
    return {
        "filial": filial,
        "conta_id": int(conta_id),
        "ate": ate.isoformat() if ate else None,
        "entradas": float(s["entradas"]),
        "saidas": float(s["saidas"]),
        "saldo": float(s["saldo"]),
    }


def dre_simples_uc_tx(cur, filial: str, de: date | None, ate: date | None):
    res = dre_simples_tx(cur, filial=filial, de=de, ate=ate)
    for l in res["linhas"]:
        l["valor"] = float(l["valor"])
    res["total"] = float(res["total"])
    res["de"] = de.isoformat() if de else None
    res["ate"] = ate.isoformat() if ate else None
    return res
