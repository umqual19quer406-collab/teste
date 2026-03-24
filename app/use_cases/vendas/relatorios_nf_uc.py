from app.core.exceptions import BusinessError
from app.use_cases.usuarios_uc import exigir_perfil_tx

from app.infra.repositories.vendas.sc5_pedidos_repo import sc5_pedido_get_tx
from app.infra.repositories.vendas.relatorios_nf_repo import nf_pedido_financeiro_resumo_tx


def relatorio_nf_financeiro_tx(
    cur,
    usuario: str,
    pedido_id: int,
    nf_status: str | None = None,
    ar_status: str | None = None,
    sc9_status: str | None = None,
) -> dict:
    exigir_perfil_tx(cur, usuario, {"admin", "operador"})

    p = sc5_pedido_get_tx(cur, int(pedido_id))
    if not p:
        raise BusinessError("Pedido não encontrado")

    rows = nf_pedido_financeiro_resumo_tx(
        cur,
        int(pedido_id),
        nf_status=nf_status,
        ar_status=ar_status,
        sc9_status=sc9_status,
    )
    return {"pedido_id": int(pedido_id), "rows": rows}
