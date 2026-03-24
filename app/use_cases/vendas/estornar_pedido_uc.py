from app.core.exceptions import BusinessError 
from app.use_cases.usuarios_uc import exigir_perfil_tx 
 
from app.infra.repositories.vendas.sc5_pedidos_repo import sc5_pedido_get_tx, sc5_pedido_cancelar_faturado_tx 
from app.infra.repositories.vendas.sc6_itens_repo import sc6_itens_do_pedido_tx 
 
from app.infra.repositories.sb1_repo import sb1_get_tx, sb1_entrada_tx 
from app.infra.repositories.sd3_repo import sd3_mov_tx 
 
from app.infra.repositories.financeiro_repo import ar_ultimo_por_pedido_tx, ar_cancelar_atomico_tx
from app.infra.repositories.faturamento_repo import (
    sf2_buscar_por_pedido_tx,
    sf2_cancelar_tx,
    sd2_cancelar_por_nf_tx,
)
from app.infra.repositories.vendas.sc9_liberacao_repo import sc9_cancelar_por_pedido_tx
from app.infra.repositories.logs_repo import log_tx 
 
def estornar_pedido_faturado_venda_tx( 
    cur, 
    usuario: str, 
    pedido_id: int, 
    filial: str, 
    motivo: str | None = None, 
) -> dict: 
    exigir_perfil_tx(cur, usuario, {"admin", "operador"}) 
 
    filial = (filial or "").strip() or "01" 
    pedido_id = int(pedido_id) 
 
    p = sc5_pedido_get_tx(cur, pedido_id) 
    if not p: 
        raise BusinessError("Pedido não encontrado") 
 
    if str(p.get("C5_FILIAL") or "").strip() != filial: 
        raise BusinessError(f"Pedido {pedido_id} não pertence à filial {filial}") 
 
    status = str(p.get("C5_STATUS") or "").strip().upper() 
    if status != "FATURADO": 
        raise BusinessError("Apenas pedido FATURADO pode ser estornado") 
 
    origem = str(p.get("C5_ORIGEM") or "VENDA").strip().upper() 
    if origem != "VENDA": 
        raise BusinessError("Este estorno é apenas para pedidos de origem VENDA") 
 
    # 1) AR: precisa existir e estar ABERTO 
    ar = ar_ultimo_por_pedido_tx(cur, pedido_id) 
    if not ar: 
        raise BusinessError("Não existe título AR para este pedido (SE1)") 
    ar_status = str(ar.get("E1_STATUS") or "").strip().upper() 
 
    if ar_status == "BAIXADO": 
        raise BusinessError("Não é permitido estornar: AR já BAIXADO (exige contra-lançamento)") 
    if ar_status != "ABERTO": 
        raise BusinessError(f"Não é permitido estornar: AR status={ar_status}") 
 
    # 2) Itens (ativos) 
    itens = sc6_itens_do_pedido_tx(cur, pedido_id) 
    if not itens: 
        raise BusinessError("Pedido sem itens ativos (SC6)") 
 
    # 3) Devolver estoque + SD3 entrada (inverso do faturamento) 
    valor_cmv_total = 0.0 
    for it in itens: 
        prod = str(it["C6_PRODUTO"]).strip() 
        qtd = int(it["C6_QTD"]) 
 
        sb1 = sb1_get_tx(cur, prod, filial) 
        cm_unit = float(sb1["B1_CM"]) 
        valor_cmv = cm_unit * qtd 
        valor_cmv_total += valor_cmv 
 
        # devolve estoque (entrada) 
        sb1_entrada_tx(cur, prod, filial, qtd) 
 
        # SD3 entrada 
        sd3_mov_tx( 
            cur, 
            filial=filial, 
            produto=prod, 
            tipo="E", 
            qtd=qtd, 
            custo_unit=cm_unit, 
            valor=valor_cmv, 
            origem="ESTORNO_PEDIDO", 
            ref=str(pedido_id), 
            usuario=usuario, 
        ) 
 
    # 4) Cancela AR 
    ar_cancelar_atomico_tx(cur, int(ar["ID"])) 
 
    # 4b) Cancela NF(s) 
    nfs = sf2_buscar_por_pedido_tx(cur, filial=filial, pedido_id=int(pedido_id)) 
    sd2_canceladas = 0
    for nf in nfs: 
        nf_id = int(nf["ID"])
        sf2_cancelar_tx(cur, nf_id, usuario=usuario, motivo=motivo or f"Estorno pedido {pedido_id}") 
        sd2_canceladas += sd2_cancelar_por_nf_tx(
            cur,
            nf_id=nf_id,
            usuario=usuario,
            motivo=motivo or f"Estorno pedido {pedido_id}",
        )

    sc9_canceladas = sc9_cancelar_por_pedido_tx(cur, int(pedido_id), usuario=usuario)
 
    # 5) Cancela pedido FATURADO (vira CANCELADO) 
    sc5_pedido_cancelar_faturado_tx(cur, pedido_id, usuario=usuario, motivo=motivo) 
 
    log_tx(cur, usuario, f"Pedido {pedido_id} ESTORNADO (VENDA) motivo={motivo} ar_id={ar['ID']} nf_canceladas={len(nfs)} sd2_canceladas={sd2_canceladas} sc9_canceladas={sc9_canceladas} cmv={valor_cmv_total}") 
 
    return { 
        "pedido_id": pedido_id, 
        "filial": filial, 
        "status_novo": "CANCELADO", 
        "ar_id": int(ar["ID"]), 
        "ar_status_novo": "CANCELADO", 
        "nf_canceladas": int(len(nfs)), 
        "sd2_canceladas": int(sd2_canceladas),
        "sc9_canceladas": int(sc9_canceladas),
        "valor_cmv_estornado": float(round(valor_cmv_total, 2)), 
        "motivo": motivo, 
    } 
