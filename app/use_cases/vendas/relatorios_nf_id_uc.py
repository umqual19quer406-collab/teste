from app.core.exceptions import BusinessError
from app.use_cases.usuarios_uc import exigir_perfil_tx

from app.infra.repositories.vendas.relatorios_nf_id_repo import nf_rastreio_tx


def relatorio_nf_rastreio_tx(cur, usuario: str, nf_id: int) -> dict:
    exigir_perfil_tx(cur, usuario, {"admin", "operador"})

    rows = nf_rastreio_tx(cur, int(nf_id))
    if not rows:
        raise BusinessError("NF não encontrada")

    return {"nf_id": int(nf_id), "rows": rows}
