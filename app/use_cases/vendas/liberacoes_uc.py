from app.core.exceptions import BusinessError
from app.use_cases.usuarios_uc import exigir_perfil_tx

from app.infra.repositories.vendas.sc5_pedidos_repo import sc5_pedido_get_tx
from app.infra.repositories.vendas.sc9_liberacao_query_repo import sc9_resumo_por_pedido_tx


def resumo_liberacao_pedido_tx(cur, usuario: str, pedido_id: int) -> dict:
    exigir_perfil_tx(cur, usuario, {"admin", "operador"})

    p = sc5_pedido_get_tx(cur, int(pedido_id))
    if not p:
        raise BusinessError("Pedido não encontrado")

    resumo = sc9_resumo_por_pedido_tx(cur, int(pedido_id))
    return {"pedido_id": int(pedido_id), "itens": resumo}
