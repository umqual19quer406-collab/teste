from app.core.exceptions import BusinessError 
from app.use_cases.usuarios_uc import exigir_perfil_tx 
 
from app.infra.repositories.vendas.sc5_pedidos_repo import ( 
    sc5_pedido_criar_tx, 
    sc5_pedido_get_tx, 
    sc5_pedido_atualizar_valor_total_tx, 
) 
from app.infra.repositories.vendas.sc6_pedidos_repo import sc6_item_criar_tx 
from app.infra.repositories.vendas.sc6_totais_repo import sc6_totais_do_pedido_tx 
 
from app.infra.repositories.sb1_repo import sb1_get_tx 
from app.infra.repositories.logs_repo import log_tx 
from app.infra.repositories.vendas.sc9_liberacao_repo import sc9_liberar_tx
from app.infra.repositories.sm0_repo import sm0_existe_tx
 
def criar_pedido_tx( 
    cur, 
    usuario: str, 
    filial: str, 
    valor_total: float, 
    status: str = "ABERTO", 
    icms: float | None = None, 
    ipi: float | None = None, 
    total_bruto: float | None = None, 
) -> dict: 
    exigir_perfil_tx(cur, usuario, {"admin", "operador"}) 
 
    filial = (filial or "").strip() or "01" 
    status = (status or "ABERTO").strip().upper() 

    if not sm0_existe_tx(cur, filial):
        raise BusinessError("Filial não cadastrada (SM0_EMPRESA)")
 
    # rigor ERP: pedido nasce ABERTO 
    if status != "ABERTO": 
        raise BusinessError("Pedido só pode ser criado com status ABERTO") 
 
    # valor_total no create vira placeholder (fonte de verdade = SC6) 
    if float(valor_total) < 0: 
        raise BusinessError("valor_total deve ser >= 0") 
 
    pedido_id = sc5_pedido_criar_tx( 
        cur, 
        filial=filial, 
        valor_total=float(valor_total), 
        usuario=usuario, 
        status="ABERTO", 
        icms=icms, 
        ipi=ipi, 
        total_bruto=total_bruto, 
        origem="VENDA",  # Protheus-like 
    ) 
 
    log_tx(cur, usuario, f"Pedido {pedido_id} criado filial={filial} origem=VENDA status=ABERTO total={valor_total}") 
 
    return { 
        "pedido_id": int(pedido_id), 
        "filial": filial, 
        "status": "ABERTO", 
        "valor_total": float(valor_total), 
    } 
 
def adicionar_item_tx( 
    cur, 
    usuario: str, 
    pedido_id: int, 
    filial: str, 
    produto: str, 
    qtd: int, 
    total: float, 
    preco_unit: float | None = None, 
    cmv_unit: float | None = None,
) -> dict: 
    exigir_perfil_tx(cur, usuario, {"admin", "operador"}) 
 
    filial = (filial or "").strip() or "01" 
    produto = (produto or "").strip() 
    if not produto: 
        raise BusinessError("produto é obrigatório") 
 
    pedido_id = int(pedido_id) 
 
    # pedido existe + filial 
    p = sc5_pedido_get_tx(cur, pedido_id) 
    if not p: 
        raise BusinessError("Pedido não encontrado") 
 
    if str(p.get("C5_FILIAL") or "").strip() != filial: 
        raise BusinessError(f"Pedido {pedido_id} não pertence à filial {filial}") 
 
    # status bloqueios 
    status = str(p.get("C5_STATUS") or "").strip().upper() 
    if status == "CANCELADO": 
        raise BusinessError("Não é permitido incluir item: pedido CANCELADO") 
    if status == "FATURADO": 
        raise BusinessError("Não é permitido incluir item: pedido FATURADO") 
    if status != "ABERTO": 
        raise BusinessError("Status inválido para inclusão de item") 
 
    # validações do item 
    qtd = int(qtd) 
    if qtd <= 0: 
        raise BusinessError("qtd deve ser > 0") 
 
    total = float(total) 
    if total < 0: 
        raise BusinessError("total deve ser >= 0") 
 
    # garante produto existe 
    sb1_get_tx(cur, produto, filial) 
 
    # cria item (SC6) 
    item = sc6_item_criar_tx( 
        cur, 
        pedido_id=pedido_id, 
        produto=produto, 
        qtd=qtd, 
        total=total, 
        preco_unit=preco_unit, 
        cmv_unit=cmv_unit,
    ) 

    # liberação automática do item (SC9)
    sc9_liberar_tx(
        cur,
        pedido_id=pedido_id,
        filial=filial,
        produto=produto,
        qtd=qtd,
        usuario=usuario,
        item=int(item["item"]) if item else None,
    )
 
    # recalcula SC5 a partir da soma do SC6 (fonte de verdade) 
    tot = sc6_totais_do_pedido_tx(cur, pedido_id) 
    sc5_pedido_atualizar_valor_total_tx(cur, pedido_id, float(tot["valor_itens"])) 
 
    log_tx( 
        cur, 
        usuario, 
        f"Item adicionado pedido={pedido_id} produto={produto} qtd={qtd} total={total} novo_total={tot['valor_itens']} lib=SC9", 
    ) 
 
    return { 
        "pedido_id": int(pedido_id), 
        "produto": produto, 
        "qtd": int(qtd), 
        "total": float(total), 
        "cmv_unit": (float(cmv_unit) if cmv_unit is not None else None),
        "novo_total": float(tot["valor_itens"]), 
        "qtd_itens": int(tot["qtd_itens"]), 
    } 
