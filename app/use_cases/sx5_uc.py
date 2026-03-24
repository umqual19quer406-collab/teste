from app.core.exceptions import BusinessError
from app.use_cases.usuarios_uc import exigir_perfil_tx

from app.infra.repositories.sx5_repo import (
    sx5_listar_tx,
    sx5_obter_tx,
    sx5_criar_tx,
    sx5_atualizar_tx,
    sx5_inativar_tx,
)


def sx5_listar_uc_tx(cur, usuario: str, filial: str, tabela: str, ativos: bool = True):
    exigir_perfil_tx(cur, usuario, {"admin", "operador"})
    return sx5_listar_tx(cur, filial=filial, tabela=tabela, ativos=ativos)


def sx5_criar_uc_tx(cur, usuario: str, filial: str, tabela: str, chave: str, descr: str, ativo: bool = True):
    exigir_perfil_tx(cur, usuario, {"admin"})
    sx5_criar_tx(cur, filial=filial, tabela=tabela, chave=chave, descr=descr, ativo=ativo)
    return {"filial": filial, "tabela": tabela, "chave": chave, "descr": descr, "ativo": ativo}


def sx5_atualizar_uc_tx(cur, usuario: str, filial: str, tabela: str, chave: str, descr: str | None, ativo: bool | None):
    exigir_perfil_tx(cur, usuario, {"admin"})
    sx5_atualizar_tx(cur, filial=filial, tabela=tabela, chave=chave, descr=descr, ativo=ativo)
    return sx5_obter_tx(cur, filial=filial, tabela=tabela, chave=chave)


def sx5_inativar_uc_tx(cur, usuario: str, filial: str, tabela: str, chave: str):
    exigir_perfil_tx(cur, usuario, {"admin"})
    sx5_inativar_tx(cur, filial=filial, tabela=tabela, chave=chave)
    return {"filial": filial, "tabela": tabela, "chave": chave, "ativo": False}
