from app.use_cases.usuarios_uc import exigir_perfil_tx
from app.infra.repositories.fechamento_repo import (
    fechamento_fechar_tx,
    fechamento_abrir_tx,
)


def fechar_periodo_uc_tx(cur, usuario: str, filial: str, ano: int, mes: int):
    exigir_perfil_tx(cur, usuario, {"admin"})
    fechamento_fechar_tx(cur, filial=filial, ano=int(ano), mes=int(mes), usuario=usuario)
    return {"filial": filial, "ano": int(ano), "mes": int(mes), "fechado": True}


def abrir_periodo_uc_tx(cur, usuario: str, filial: str, ano: int, mes: int):
    exigir_perfil_tx(cur, usuario, {"admin"})
    fechamento_abrir_tx(cur, filial=filial, ano=int(ano), mes=int(mes), usuario=usuario)
    return {"filial": filial, "ano": int(ano), "mes": int(mes), "fechado": False}
