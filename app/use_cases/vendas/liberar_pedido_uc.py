from app.core.exceptions import BusinessError
from app.use_cases.usuarios_uc import exigir_perfil_tx

from app.infra.repositories.vendas.sc5_pedidos_repo import sc5_pedido_get_tx
from app.infra.repositories.vendas.sc6_itens_repo import sc6_itens_do_pedido_tx
from app.infra.repositories.sb1_repo import sb1_get_tx
from app.infra.repositories.vendas.sc9_liberacao_repo import (
    sc9_liberar_tx,
    sc9_qtd_liberada_por_pedido_tx,
)


def liberar_item_pedido_tx(
    cur,
    usuario: str,
    pedido_id: int,
    filial: str,
    produto: str,
    qtd: int,
) -> dict:
    exigir_perfil_tx(cur, usuario, {"admin", "operador"})

    p = sc5_pedido_get_tx(cur, int(pedido_id))
    if not p:
        raise BusinessError("Pedido não encontrado")

    if str(p.get("C5_FILIAL") or "").strip() != str(filial).strip():
        raise BusinessError(f"Pedido {pedido_id} não pertence à filial {filial}")

    status = str(p.get("C5_STATUS") or "").strip().upper()
    if status != "ABERTO":
        raise BusinessError("Apenas pedido ABERTO pode ser liberado")

    itens = sc6_itens_do_pedido_tx(cur, int(pedido_id))
    if not itens:
        raise BusinessError("Pedido sem itens")

    produto = (produto or "").strip()
    if not produto:
        raise BusinessError("produto é obrigatório")

    qtd = int(qtd)
    if qtd <= 0:
        raise BusinessError("qtd deve ser > 0")

    item = next((it for it in itens if str(it["C6_PRODUTO"]).strip() == produto), None)
    if not item:
        raise BusinessError("Produto não encontrado no pedido")

    qtd_pedido = int(item["C6_QTD"])
    liberados = sc9_qtd_liberada_por_pedido_tx(cur, int(pedido_id))
    item_no = int(item.get("C6_ITEM") or 0)
    qtd_ja = int(liberados.get(item_no, 0))
    if qtd > (qtd_pedido - qtd_ja):
        raise BusinessError("qtd liberada maior que saldo do pedido")

    lib_id = sc9_liberar_tx(
        cur,
        pedido_id=int(pedido_id),
        filial=str(filial).strip(),
        produto=produto,
        qtd=qtd,
        usuario=usuario,
        item=int(item["C6_ITEM"]) if item.get("C6_ITEM") is not None else None,
    )

    return {
        "pedido_id": int(pedido_id),
        "filial": str(filial).strip(),
        "produto": produto,
        "qtd": int(qtd),
        "liberacao_id": int(lib_id),
    }


def liberar_pedido_total_tx(
    cur,
    usuario: str,
    pedido_id: int,
    filial: str,
    usar_estoque: bool = True,
) -> dict:
    exigir_perfil_tx(cur, usuario, {"admin", "operador"})

    p = sc5_pedido_get_tx(cur, int(pedido_id))
    if not p:
        raise BusinessError("Pedido não encontrado")

    if str(p.get("C5_FILIAL") or "").strip() != str(filial).strip():
        raise BusinessError(f"Pedido {pedido_id} não pertence à filial {filial}")

    status = str(p.get("C5_STATUS") or "").strip().upper()
    if status != "ABERTO":
        raise BusinessError("Apenas pedido ABERTO pode ser liberado")

    itens = sc6_itens_do_pedido_tx(cur, int(pedido_id))
    if not itens:
        raise BusinessError("Pedido sem itens")

    liberados = sc9_qtd_liberada_por_pedido_tx(cur, int(pedido_id))
    liberacoes = []

    for it in itens:
        produto = str(it["C6_PRODUTO"]).strip()
        qtd_pedido = int(it["C6_QTD"])
        item_no = int(it.get("C6_ITEM") or 0)
        qtd_ja = int(liberados.get(item_no, 0))
        saldo = qtd_pedido - qtd_ja
        if saldo <= 0:
            continue
        if usar_estoque:
            sb1 = sb1_get_tx(cur, produto, str(filial).strip())
            disponivel = int(sb1["B1_ESTOQUE"]) - int(sb1["B1_RESERVADO"])
            if disponivel <= 0:
                continue
            saldo = min(saldo, disponivel)
        lib_id = sc9_liberar_tx(
            cur,
            pedido_id=int(pedido_id),
            filial=str(filial).strip(),
            produto=produto,
            qtd=saldo,
            usuario=usuario,
            item=int(it["C6_ITEM"]) if it.get("C6_ITEM") is not None else None,
        )
        liberacoes.append({"produto": produto, "qtd": saldo, "liberacao_id": int(lib_id)})

    return {
        "pedido_id": int(pedido_id),
        "filial": str(filial).strip(),
        "liberacoes": liberacoes,
        "usar_estoque": bool(usar_estoque),
    }
