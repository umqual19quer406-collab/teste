from app.domain.errors import BusinessError
from app.infra.repositories.logs_repo import log_tx
from app.infra.repositories.parceiros_repo import (
    sa1_criar_tx,
    sa1_inativar_tx,
    sa1_listar_tx,
    sa1_obter_tx,
    sa1_set_tabela_tx,
    sa2_criar_tx,
    sa2_inativar_tx,
    sa2_listar_tx,
    sa2_obter_tx,
)


def criar_cliente_uc_tx(
    cur,
    usuario: str,
    filial: str,
    cod: str,
    nome: str,
    doc: str | None,
    email: str | None,
    tel: str | None,
    end: str | None,
    mun: str | None,
    uf: str | None,
    cep: str | None,
    tabela_id: int | None,
):
    cod = cod.strip()
    nome = nome.strip()
    if not cod or not nome:
        raise BusinessError("Código e nome são obrigatórios")

    cliente_id = sa1_criar_tx(cur, filial, cod, nome, doc, email, tel, end, mun, uf, cep, tabela_id)
    log_tx(cur, usuario, f"SA1.CRIAR id={cliente_id} cod={cod} filial={filial} tabela_id={tabela_id}")
    return {"id": cliente_id, "cod": cod, "nome": nome, "filial": filial, "tabela_id": tabela_id}


def listar_clientes_uc_tx(cur, filial: str, ativo: bool = True, q: str | None = None):
    return sa1_listar_tx(cur, filial=filial, ativo=ativo, q=q)


def obter_cliente_uc_tx(cur, filial: str, cod: str):
    cliente = sa1_obter_tx(cur, filial=filial, cod=cod)
    if not cliente:
        raise BusinessError("Cliente não encontrado")
    return cliente


def set_tabela_cliente_uc_tx(cur, usuario: str, filial: str, cod: str, tabela_id: int | None):
    sa1_set_tabela_tx(cur, filial=filial, cod=cod, tabela_id=tabela_id)
    log_tx(cur, usuario, f"SA1.SET_TABELA cod={cod} filial={filial} tabela_id={tabela_id}")
    return {"cod": cod, "filial": filial, "tabela_id": tabela_id}


def inativar_cliente_uc_tx(cur, usuario: str, filial: str, cod: str):
    sa1_inativar_tx(cur, filial=filial, cod=cod)
    log_tx(cur, usuario, f"SA1.INATIVAR cod={cod} filial={filial}")
    return {"cod": cod, "filial": filial, "ativo": False}


def criar_fornecedor_uc_tx(
    cur,
    usuario: str,
    filial: str,
    cod: str,
    nome: str,
    doc: str | None,
    email: str | None,
    tel: str | None,
    end: str | None,
    mun: str | None,
    uf: str | None,
    cep: str | None,
):
    cod = cod.strip()
    nome = nome.strip()
    if not cod or not nome:
        raise BusinessError("Código e nome são obrigatórios")

    fornecedor_id = sa2_criar_tx(cur, filial, cod, nome, doc, email, tel, end, mun, uf, cep)
    log_tx(cur, usuario, f"SA2.CRIAR id={fornecedor_id} cod={cod} filial={filial}")
    return {"id": fornecedor_id, "cod": cod, "nome": nome, "filial": filial}


def listar_fornecedores_uc_tx(cur, filial: str, ativo: bool = True, q: str | None = None):
    return sa2_listar_tx(cur, filial=filial, ativo=ativo, q=q)


def obter_fornecedor_uc_tx(cur, filial: str, cod: str):
    fornecedor = sa2_obter_tx(cur, filial=filial, cod=cod)
    if not fornecedor:
        raise BusinessError("Fornecedor não encontrado")
    return fornecedor


def inativar_fornecedor_uc_tx(cur, usuario: str, filial: str, cod: str):
    sa2_inativar_tx(cur, filial=filial, cod=cod)
    log_tx(cur, usuario, f"SA2.INATIVAR cod={cod} filial={filial}")
    return {"cod": cod, "filial": filial, "ativo": False}
