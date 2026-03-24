from app.core.exceptions import BusinessError 
from app.use_cases.usuarios_uc import exigir_perfil_tx 
 
from app.infra.repositories.vendas.sc5_pedidos_repo import sc5_pedido_get_tx 
from app.infra.repositories.vendas.sc6_itens_query_repo import sc6_itens_do_pedido_tx 
from app.infra.repositories.financeiro_repo import ar_listar_por_pedido_tx 
 
def consultar_pedido_tx(cur, usuario: str, pedido_id: int) -> dict: 
    exigir_perfil_tx(cur, usuario, {"admin", "operador"}) 
 
    p = sc5_pedido_get_tx(cur, int(pedido_id)) 
    if not p: 
        raise BusinessError("Pedido não encontrado") 
 
    itens = sc6_itens_do_pedido_tx(cur, int(pedido_id)) 
    ar = ar_listar_por_pedido_tx(cur, int(pedido_id)) 
 
    # resumo simples do AR (último título, se existir) 
    ar_resumo = None 
    if ar: 
        t = ar[0] 
        ar_resumo = { 
            "ar_id": int(t["ID"]), 
            "status": t.get("E1_STATUS"), 
            "valor": float(t.get("E1_VALOR") or 0), 
            "venc": t.get("E1_VENC"), 
            "se5_id": t.get("E1_SE5_ID"), 
        } 
 
    return { 
        "pedido": p, 
        "itens": itens, 
        "ar": ar,               # lista completa (auditoria) 
        "ar_resumo": ar_resumo, # fácil pro front 
    } 