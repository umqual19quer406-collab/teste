from datetime import date

from app.domain.errors import BusinessError
from app.infra.repositories.logs_repo import log_tx
from app.infra.repositories.preco_repo import (
    buscar_preco_vigente_tx,
    criar_tabela_tx,
    definir_preco_tx,
    listar_precos_tabela_tx,
    listar_tabelas_tx,
)


def listar_tabelas_uc_tx(cur, filial: str):
    rows = listar_tabelas_tx(cur, filial)
    return [
        {
            "id": int(row["ID"]),
            "filial": row["P0_FILIAL"],
            "codigo": row["P0_COD"],
            "descricao": row["P0_DESC"],
            "ativa": bool(row["P0_ATIVA"]),
        }
        for row in rows
    ]


def criar_tabela_uc_tx(cur, usuario: str, filial: str, cod: str, desc: str):
    tabela_id = criar_tabela_tx(cur, filial, cod, desc)
    log_tx(cur, usuario, f"PRECO.TABELA.CRIAR id={tabela_id} filial={filial}")
    return {"id": tabela_id, "codigo": cod, "descricao": desc}


def listar_precos_tabela_uc_tx(cur, filial: str, tabela_id: int):
    rows = listar_precos_tabela_tx(cur, filial, tabela_id)
    return [
        {
            "id": int(row["ID"]),
            "filial": row["P1_FILIAL"],
            "tabela_id": int(row["P1_TABELA_ID"]),
            "produto": row["P1_PRODUTO"],
            "preco": float(row["P1_PRECO"]),
            "dt_ini": row["P1_DTINI"].isoformat() if row["P1_DTINI"] else None,
            "dt_fim": row["P1_DTFIM"].isoformat() if row["P1_DTFIM"] else None,
            "vigente": row["P1_DTFIM"] is None,
        }
        for row in rows
    ]


def definir_preco_uc_tx(
    cur,
    usuario: str,
    filial: str,
    tabela_id: int,
    produto: str,
    preco: float,
    dt_ini: date,
):
    if preco <= 0:
        raise BusinessError("Preço inválido")

    definir_preco_tx(cur, filial, tabela_id, produto, preco, dt_ini)
    log_tx(cur, usuario, f"PRECO.DEF produto={produto} tabela={tabela_id} preco={preco}")
    return {"produto": produto, "preco": preco, "dt_ini": dt_ini.isoformat()}


def buscar_preco_uc_tx(cur, filial: str, tabela_id: int, produto: str, data: date):
    return {
        "produto": produto,
        "preco": buscar_preco_vigente_tx(cur, filial, tabela_id, produto, data),
    }
