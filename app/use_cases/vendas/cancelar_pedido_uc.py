from app.core.exceptions import BusinessError 
from app.use_cases.usuarios_uc import exigir_perfil_tx 
 
from app.infra.repositories.vendas.sc5_pedidos_repo import sc5_pedido_get_tx, sc5_pedido_status_tx 
from app.infra.repositories.vendas.sc6_itens_query_repo import sc6_itens_do_pedido_tx 
from app.infra.repositories.vendas.sc6_itens_repo import sc6_itens_cancelar_por_pedido_tx
from app.infra.repositories.vendas.sc9_liberacao_repo import sc9_cancelar_por_pedido_tx
from app.infra.repositories.vendas.origem_repo import venda_buscar_reserva_id_por_pedido_tx 
 
from app.infra.repositories.sd3_repo import sd3_mov_tx 
from app.infra.repositories.sb1_repo import sb1_get_tx, sb1_entrada_tx, sb1_reservar_atomico_tx 
from app.infra.repositories.reservas_repo import reserva_status_tx  # se quiser reabrir reserva 
from app.infra.repositories.financeiro_repo import cancelar_ar_por_ref_tx
from app.infra.repositories.faturamento_repo import (
    sf2_buscar_por_pedido_tx,
    sf2_cancelar_tx,
    sd2_cancelar_por_nf_tx,
)
from app.infra.repositories.logs_repo import log_tx 
 
def cancelar_pedido_tx( 
    cur, 
    usuario: str, 
    pedido_id: int, 
    filial: str, 
    modo: str = "AUTO",   # AUTO | SIMPLES | ESTORNAR 
    reativar_reserva: bool = True, 
) -> dict: 
    """ 
    Cancela pedido SC5. 
 
    modo: 
      - SIMPLES: apenas muda status do SC5 -> CANCELADO (sem mexer em estoque/financeiro) 
      - ESTORNAR: faz estorno completo (SD3 entrada + devolve estoque + cancela AR) 
      - AUTO: se status FATURADO => ESTORNAR; senão => SIMPLES 
    """ 
    exigir_perfil_tx(cur, usuario, {"admin", "operador"}) 
 
    p = sc5_pedido_get_tx(cur, int(pedido_id)) 
    if not p: 
        raise BusinessError("Pedido não encontrado") 
 
    if str(p.get("C5_FILIAL", "")).strip() != str(filial).strip(): 
        raise BusinessError(f"Pedido {pedido_id} não pertence à filial {filial}") 
 
    status_atual = str(p.get("C5_STATUS", "")).strip().upper() 
    if status_atual == "CANCELADO": 
        raise BusinessError("Pedido já está CANCELADO") 
 
    modo2 = (modo or "AUTO").strip().upper() 
    if modo2 not in {"AUTO", "SIMPLES", "ESTORNAR"}: 
        raise BusinessError("modo inválido (AUTO/SIMPLES/ESTORNAR)") 
 
    if modo2 == "AUTO": 
        modo2 = "ESTORNAR" if status_atual == "FATURADO" else "SIMPLES" 
 
    # --- SIMPLES: só cancela SC5 --- 
    if modo2 == "SIMPLES": 
        sc5_pedido_status_tx(cur, int(pedido_id), "CANCELADO", usuario=usuario, motivo=None) 
        itens_cancelados = sc6_itens_cancelar_por_pedido_tx(cur, int(pedido_id), usuario=usuario)
        sc9_canceladas = sc9_cancelar_por_pedido_tx(cur, int(pedido_id), usuario=usuario)
        log_tx(cur, usuario, f"Pedido {pedido_id} cancelado (SIMPLES) filial={filial} status_ant={status_atual} sc6_cancelados={itens_cancelados}") 
        return {
            "pedido_id": int(pedido_id),
            "filial": filial,
            "status": "CANCELADO",
            "modo": "SIMPLES",
            "sc6_cancelados": int(itens_cancelados),
            "sc9_canceladas": int(sc9_canceladas),
        } 
 
    # --- ESTORNAR: reverte estoque + SD3 + financeiro --- 
    itens = sc6_itens_do_pedido_tx(cur, int(pedido_id)) 
    if not itens: 
        raise BusinessError("Pedido sem itens (SC6)") 
 
    # 1) cancelar AR (se existir). Se AR já baixado, bloqueia (ERP real). 
    ar_cancelados = cancelar_ar_por_ref_tx(cur, filial=filial, pedido_id=int(pedido_id)) 

    # 1b) cancelar NF (SF2) associada ao pedido 
    nfs = sf2_buscar_por_pedido_tx(cur, filial=filial, pedido_id=int(pedido_id))
    if not nfs:
        raise BusinessError("Pedido FATURADO sem NF (consistência)")
    sd2_canceladas = 0
    for nf in nfs: 
        nf_id = int(nf["ID"])
        sf2_cancelar_tx(cur, nf_id, usuario=usuario, motivo=f"Cancelamento pedido {pedido_id}") 
        sd2_canceladas += sd2_cancelar_por_nf_tx(
            cur,
            nf_id=nf_id,
            usuario=usuario,
            motivo=f"Cancelamento pedido {pedido_id}",
        )
 
    # 2) estornar SD3 e devolver estoque por item 
    valor_cmv_estornado = 0.0 
    qtd_total_itens = 0 
 
    for it in itens: 
        produto = str(it.get("C6_PRODUTO") or "").strip() 
        qtd = int(it.get("C6_QTD") or 0) 
        if not produto or qtd <= 0: 
            raise BusinessError("Item SC6 inválido para estorno") 
 
        sb1 = sb1_get_tx(cur, produto, filial) 
        cm = float(sb1["B1_CM"]) 
        cmv_item = cm * qtd 
        valor_cmv_estornado += cmv_item 
        qtd_total_itens += qtd 
 
        # SD3 entrada (estorno do custo) 
        sd3_mov_tx( 
            cur, 
            filial=filial, 
            produto=produto, 
            tipo="E", 
            qtd=qtd, 
            custo_unit=cm, 
            valor=cmv_item, 
            origem="PEDIDO_CANCELADO", 
            ref=str(pedido_id), 
            usuario=usuario, 
        ) 
 
        # devolve estoque físico 
        sb1_entrada_tx(cur, produto, filial, qtd) 
 
    # 3) Se o pedido veio de reserva, opcionalmente reabre e reserva de volta 
    reserva_id = venda_buscar_reserva_id_por_pedido_tx(cur, int(pedido_id)) 
    if reserva_id is not None and reativar_reserva: 
        # reabrir reserva (regra: volta para ABERTA) 
        reserva_status_tx(cur, int(reserva_id), "ABERTA") 
 
        # re-reservar exatamente as quantidades do pedido 
        for it in itens: 
            produto = str(it.get("C6_PRODUTO") or "").strip() 
            qtd = int(it.get("C6_QTD") or 0) 
            if produto and qtd > 0: 
                sb1_reservar_atomico_tx(cur, produto, filial, qtd) 
 
    # 4) cancelar SC5 + itens 
    sc5_pedido_status_tx(cur, int(pedido_id), "CANCELADO", usuario=usuario, motivo=None) 
    itens_cancelados = sc6_itens_cancelar_por_pedido_tx(cur, int(pedido_id), usuario=usuario)
    sc9_canceladas = sc9_cancelar_por_pedido_tx(cur, int(pedido_id), usuario=usuario)
 
    log_tx( 
        cur, 
        usuario, 
        f"Pedido {pedido_id} cancelado (ESTORNAR) filial={filial} ar_cancelados={ar_cancelados} nf_canceladas={len(nfs)} sd2_canceladas={sd2_canceladas} sc6_cancelados={itens_cancelados} sc9_canceladas={sc9_canceladas} cmv_estornado={valor_cmv_estornado} reserva={reserva_id}", 
    ) 
 
    return { 
        "pedido_id": int(pedido_id), 
        "filial": filial, 
        "status": "CANCELADO", 
        "modo": "ESTORNAR", 
        "status_anterior": status_atual, 
        "ar_cancelados": int(ar_cancelados), 
        "nf_canceladas": int(len(nfs)), 
        "sd2_canceladas": int(sd2_canceladas),
        "sc6_cancelados": int(itens_cancelados),
        "sc9_canceladas": int(sc9_canceladas),
        "cmv_estornado": float(valor_cmv_estornado), 
        "reserva_id": int(reserva_id) if reserva_id is not None else None, 
        "reserva_reativada": bool(reserva_id is not None and reativar_reserva), 
    } 
