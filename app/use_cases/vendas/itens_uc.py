from app.core.exceptions import BusinessError 
from app.use_cases.usuarios_uc import exigir_perfil_tx 
from app.infra.repositories.vendas.sc5_pedidos_repo import sc5_pedido_get_tx, sc5_pedido_atualizar_valor_total_tx 
from app.infra.repositories.vendas.sc6_totais_repo import sc6_totais_do_pedido_tx 
from app.infra.repositories.vendas.sc6_itens_repo import sc6_item_get_tx, sc6_item_atualizar_tx, sc6_item_excluir_logico_tx 
from app.infra.repositories.logs_repo import log_tx 
 
def _exigir_pedido_aberto_tx(cur, pedido_id: int, filial: str | None): 
    p = sc5_pedido_get_tx(cur, int(pedido_id)) 
    if not p: 
        raise BusinessError("Pedido não encontrado") 
    if filial and str(p.get("C5_FILIAL") or "").strip() != str(filial).strip(): 
        raise BusinessError("Pedido não pertence à filial informada") 
 
    st = str(p.get("C5_STATUS") or "").strip().upper() 
    if st != "ABERTO": 
        raise BusinessError("Operação permitida apenas para pedido ABERTO") 
    return p 
 
def editar_item_tx( 
    cur, 
    usuario: str, 
    item_id: int, 
    filial: str | None, 
    qtd: int, 
    total: float, 
    preco_unit: float | None = None, 
    cmv_unit: float | None = None,
) -> dict: 
    exigir_perfil_tx(cur, usuario, {"admin", "operador"}) 
 
    it = sc6_item_get_tx(cur, int(item_id)) 
    if not it or int(it.get("C6_ATIVO") or 1) != 1:
        raise BusinessError("Item não encontrado/INATIVO") 
 
    pedido_id = int(it["C6_PEDIDO_ID"]) 
    _exigir_pedido_aberto_tx(cur, pedido_id, filial) 
 
    qtd = int(qtd) 
    if qtd <= 0: 
        raise BusinessError("qtd deve ser > 0") 
 
    total = float(total) 
    if total < 0: 
        raise BusinessError("total deve ser >= 0") 
 
    if preco_unit is None: 
        preco_unit = (total / qtd) if qtd > 0 else total 
 
    sc6_item_atualizar_tx(cur, int(item_id), qtd, float(preco_unit), float(total), usuario, cmv_unit=cmv_unit) 
 
    tot = sc6_totais_do_pedido_tx(cur, pedido_id) 
    sc5_pedido_atualizar_valor_total_tx(cur, pedido_id, float(tot["valor_itens"])) 
 
    log_tx(cur, usuario, f"Item {item_id} editado pedido={pedido_id} qtd={qtd} total={total} novo_total={tot['valor_itens']}") 
 
    return { 
        "pedido_id": pedido_id, 
        "item_id": int(item_id), 
        "cmv_unit": (float(cmv_unit) if cmv_unit is not None else None),
        "novo_total": float(tot["valor_itens"]), 
        "qtd_itens": int(tot["qtd_itens"]), 
    } 
 
def excluir_item_tx(cur, usuario: str, item_id: int, filial: str | None) -> dict: 
    exigir_perfil_tx(cur, usuario, {"admin", "operador"}) 
 
    it = sc6_item_get_tx(cur, int(item_id)) 
    ativo = it.get("C6_ATIVO") if it else None
    if not it: 
        raise BusinessError("Item não encontrado") 
    if ativo in (0, False):  # já deletado lógico 
        raise BusinessError("Item INATIVO") 
        # se ativo vier None por migração antiga, trate como ativo e deixe o delete funciona 
 
    pedido_id = int(it["C6_PEDIDO_ID"]) 
    _exigir_pedido_aberto_tx(cur, pedido_id, filial) 
 
    sc6_item_excluir_logico_tx(cur, int(item_id), usuario) 
 
    tot = sc6_totais_do_pedido_tx(cur, pedido_id) 
    sc5_pedido_atualizar_valor_total_tx(cur, pedido_id, float(tot["valor_itens"])) 
 
    log_tx(cur, usuario, f"Item {item_id} excluído pedido={pedido_id} novo_total={tot['valor_itens']}") 
 
    return { 
        "pedido_id": pedido_id, 
        "item_id": int(item_id), 
        "novo_total": float(tot["valor_itens"]), 
        "qtd_itens": int(tot["qtd_itens"]), 
    } 
