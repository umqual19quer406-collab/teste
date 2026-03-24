from app.core.exceptions import BusinessError
from app.use_cases.usuarios_uc import exigir_perfil_tx 
 
from app.infra.repositories.vendas.sc5_pedidos_repo import sc5_pedido_get_tx, sc5_pedido_atualizar_valor_total_tx 
from app.infra.repositories.vendas.sc6_totais_repo import sc6_totais_do_pedido_tx 
from app.infra.repositories.logs_repo import log_tx 
 
def pedido_recalcular_totais_tx( 
    cur, 
    usuario: str, 
    pedido_id: int, 
    forcar: bool = False,  # permite recalcular até FATURADO (admin), se você quiser 
) -> dict: 
    exigir_perfil_tx(cur, usuario, {"admin", "operador"}) 
 
    p = sc5_pedido_get_tx(cur, int(pedido_id)) 
    if not p: 
        raise BusinessError("Pedido não encontrado") 
 
    status = str(p.get("C5_STATUS") or "").strip().upper() 
    if status == "CANCELADO": 
        raise BusinessError("Não é permitido recalcular: pedido CANCELADO") 
 
    if status == "FATURADO" and not forcar: 
        raise BusinessError("Não é permitido recalcular: pedido FATURADO (use forcar=true se necessário)") 
 
    # totais calculados 
    tot = sc6_totais_do_pedido_tx(cur, int(pedido_id)) 
    novo_total = float(tot["valor_itens"]) 
 
    antigo_total = float(p.get("C5_VALOR_TOTAL") or 0.0) 
    if abs(antigo_total - novo_total) < 0.0001: 
        return { 
            "pedido_id": int(pedido_id), 
            "status": status, 
            "alterado": False, 
            "valor_total_antigo": antigo_total, 
            "valor_total_novo": novo_total, 
            "qtd_itens": int(tot["qtd_itens"]), 
            "valor_itens": float(tot["valor_itens"]), 
        } 
 
    sc5_pedido_atualizar_valor_total_tx(cur, int(pedido_id), novo_total) 
 
    log_tx( 
        cur, 
        usuario, 
        f"Pedido {pedido_id} recalculado status={status} total:{antigo_total}->{novo_total} qtd_itens={tot['qtd_itens']}", 
    ) 
 
    return { 
        "pedido_id": int(pedido_id), 
        "status": status, 
        "alterado": True, 
        "valor_total_antigo": antigo_total, 
        "valor_total_novo": novo_total, 
        "qtd_itens": int(tot["qtd_itens"]), 
        "valor_itens": float(tot["valor_itens"]), 
    }