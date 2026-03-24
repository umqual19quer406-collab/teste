from __future__ import annotations

from app.infra.repositories.sm0_repo import sm0_obter_series_tx
from app.infra.repositories.sx5_repo import sx5_obter_tx, sx5_criar_tx
from app.core.exceptions import BusinessError


def resolve_serie_tx(cur, filial: str, tabela: str) -> str:
    tabela = (tabela or "").strip().upper()
    filial = (filial or "01").strip()

    sm0 = sm0_obter_series_tx(cur, filial)
    if sm0:
        if tabela == "NF" and sm0.get("M0_SERIE_NF"):
            return str(sm0["M0_SERIE_NF"]).strip()
        if tabela == "AR" and sm0.get("M0_SERIE_AR"):
            return str(sm0["M0_SERIE_AR"]).strip()
        if tabela == "AP" and sm0.get("M0_SERIE_AP"):
            return str(sm0["M0_SERIE_AP"]).strip()

    sx5 = sx5_obter_tx(cur, filial=filial, tabela="SERIE", chave=tabela)
    if sx5 and sx5.get("X5_DESCR"):
        return str(sx5["X5_DESCR"]).strip()

    return "1"


def validar_serie_tx(cur, filial: str, tabela: str, serie: str) -> None:
    tabela = (tabela or "").strip().upper()
    serie = (serie or "").strip()
    if not serie:
        raise BusinessError("Série inválida")

    sx5 = sx5_obter_tx(cur, filial=filial, tabela="SERIE", chave=tabela)
    if sx5 is None:
        raise BusinessError("Série não cadastrada no SX5 (tabela SERIE)")
    if str(sx5.get("X5_DESCR") or "").strip() != serie:
        raise BusinessError("Série informada não confere com SX5 (SERIE)")


def seed_series_basicas_tx(cur, filial: str) -> None:
    for chave in ("NF", "AR", "AP"):
        if sx5_obter_tx(cur, filial=filial, tabela="SERIE", chave=chave) is None:
            sx5_criar_tx(cur, filial=filial, tabela="SERIE", chave=chave, descr="1", ativo=True)
