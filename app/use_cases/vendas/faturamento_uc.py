from datetime import date

from app.core.exceptions import BusinessError
from app.infra.repositories.faturamento_repo import sd2_item_criar_tx, sf2_criar_tx
from app.infra.repositories.fechamento_repo import fechamento_validar_periodo_tx
from app.infra.repositories.financeiro_repo import ar_criar_tx
from app.infra.repositories.fiscal_repo import fiscal_get_tes_tx, fiscal_resolver_item_tx
from app.infra.repositories.logs_repo import log_tx
from app.infra.repositories.preco_repo import buscar_preco_vigente_tx
from app.infra.repositories.reservas_repo import (
    reserva_get_tx,
    reserva_set_cliente_preco_tx,
    reserva_status_tx,
)
from app.infra.repositories.sa1_repo import sa1_get_tx
from app.infra.repositories.sb1_repo import (
    sb1_baixar_e_desreservar_atomico_tx,
    sb1_get_tx,
)
from app.infra.repositories.sd3_repo import saldo_sd3_tx, sd3_mov_tx
from app.infra.repositories.sm0_repo import sm0_existe_tx
from app.infra.repositories.vendas.sc5_pedidos_repo import sc5_pedido_criar_tx
from app.infra.repositories.vendas.sc6_pedidos_repo import sc6_item_criar_tx
from app.infra.repositories.vendas.sc9_liberacao_repo import sc9_liberar_tx
from app.use_cases.usuarios_uc import exigir_perfil_tx


def faturar_reserva_tx(
    cur,
    usuario: str,
    reserva_id: int,
    cliente_cod: str | None,
    venc_dias: int,
    tes_cod: str = "001",
) -> dict:
    exigir_perfil_tx(cur, usuario, {"admin", "operador"})

    reserva = reserva_get_tx(cur, int(reserva_id))
    if not reserva:
        raise BusinessError("Reserva não encontrada")
    if reserva["Z0_STATUS"] != "ABERTA":
        raise BusinessError("Apenas reserva ABERTA pode ser confirmada")

    produto = reserva["Z0_PRODUTO"]
    filial = reserva["Z0_FILIAL"]
    qtd = int(reserva["Z0_QTD"])
    if not sm0_existe_tx(cur, filial):
        raise BusinessError("Filial não cadastrada (SM0_EMPRESA)")
    fechamento_validar_periodo_tx(cur, filial, date.today())
    produto_snapshot = sb1_get_tx(cur, produto, filial)

    cliente_nome = None
    if cliente_cod:
        cliente = sa1_get_tx(cur, filial=filial, cod=cliente_cod)
        if not cliente:
            raise BusinessError("Cliente não encontrado (SA1)")
        cliente_nome = cliente["A1_NOME"]

    preco_unit = reserva.get("Z0_PRECO_UNIT")
    total = reserva.get("Z0_TOTAL")
    tabela_id = reserva.get("Z0_TABELA_ID")

    if preco_unit is not None and total is not None:
        preco = float(preco_unit)
        valor_venda = float(total)
    else:
        preco = float(produto_snapshot["B1_PRECO"])
        if tabela_id is not None:
            try:
                preco = float(
                    buscar_preco_vigente_tx(
                        cur,
                        filial=filial,
                        tabela_id=int(tabela_id),
                        produto=produto,
                        data=date.today(),
                    )
                )
            except BusinessError:
                pass

        valor_venda = preco * qtd

        reserva_set_cliente_preco_tx(
            cur,
            reserva_id=int(reserva_id),
            cliente_cod=cliente_cod,
            tabela_id=(int(tabela_id) if tabela_id is not None else None),
            preco_unit=float(preco),
            total=float(valor_venda),
        )

    cm_unit = float(produto_snapshot["B1_CM"])
    valor_cmv = cm_unit * qtd

    tes = fiscal_get_tes_tx(cur, filial, tes_cod=tes_cod)
    tes_cod = str(tes.get("F4_COD") or tes_cod).strip()
    tes_tipo = str(tes.get("F4_TIPO") or "").strip().upper()
    cfop_base = (tes.get("F4_CFOP") or "").strip()

    if tes_tipo and tes_tipo != "S":
        raise BusinessError("TES incompatível para venda (F4_TIPO deve ser 'S')")
    if not cfop_base:
        raise BusinessError("TES sem CFOP configurado (F4_CFOP)")

    fiscal_item = fiscal_resolver_item_tx(
        cur,
        filial=filial,
        tes_cod=tes_cod,
        cliente_cod=cliente_cod,
        produto=produto,
    )
    valor_icms = round(valor_venda * float(fiscal_item["icms"]), 2)
    valor_ipi = round(valor_venda * float(fiscal_item["ipi"]), 2)
    valor_pis = round(valor_venda * float(fiscal_item["pis"]), 2)
    valor_cofins = round(valor_venda * float(fiscal_item["cofins"]), 2)
    valor_icms_st = round(valor_venda * float(fiscal_item["icms_st"]), 2)
    valor_difal = round(valor_venda * float(fiscal_item["difal"]), 2)
    total_bruto = round(valor_venda + valor_ipi + valor_icms_st + valor_difal, 2)
    gera_titulo = bool(fiscal_item["gera_tit"])
    gera_estoque = bool(fiscal_item["gera_est"])
    cfop_item = str(fiscal_item["cfop"] or cfop_base).strip()

    pedido_id = sc5_pedido_criar_tx(
        cur,
        filial,
        valor_venda,
        usuario,
        status="ABERTO",
        icms=valor_icms,
        ipi=valor_ipi,
        total_bruto=total_bruto,
    )

    cur.execute(
        "UPDATE dbo.SZ0_RESERVA SET Z0_PEDIDO_ID=? WHERE ID=?",
        (int(pedido_id), int(reserva_id)),
    )

    item = sc6_item_criar_tx(cur, pedido_id, produto, qtd, total=valor_venda, preco_unit=preco)

    sc9_liberar_tx(
        cur,
        pedido_id=pedido_id,
        filial=filial,
        produto=produto,
        qtd=qtd,
        usuario=usuario,
        item=int(item["item"]) if item else None,
    )

    nota = sf2_criar_tx(
        cur,
        filial=filial,
        pedido_id=pedido_id,
        cliente=cliente_nome,
        cliente_cod=cliente_cod,
        valor_total=valor_venda,
        icms=valor_icms,
        ipi=valor_ipi,
        total_bruto=total_bruto,
        tes_cod=tes_cod,
        cfop=cfop_base,
        origem="RESERVA",
        pis=valor_pis,
        cofins=valor_cofins,
        icms_st=valor_icms_st,
        difal=valor_difal,
    )

    sd2_item_criar_tx(
        cur,
        nf_id=nota["id"],
        doc=nota["doc"],
        serie=nota["serie"],
        item=int(item["item"]) if item else 1,
        filial=filial,
        pedido_id=pedido_id,
        produto=produto,
        qtd=qtd,
        preco_unit=preco,
        total=valor_venda,
        icms=valor_icms,
        ipi=valor_ipi,
        tes_cod=tes_cod,
        cfop=cfop_item,
        pis=valor_pis,
        cofins=valor_cofins,
        icms_st=valor_icms_st,
        difal=valor_difal,
        cst_icms=fiscal_item.get("cst_icms"),
        csosn=fiscal_item.get("csosn"),
        cst_pis=fiscal_item.get("cst_pis"),
        cst_cofins=fiscal_item.get("cst_cofins"),
    )

    if gera_estoque:
        sd3_mov_tx(
            cur,
            filial,
            produto,
            "S",
            qtd,
            cm_unit,
            valor_cmv,
            "NF_EMITIDA",
            str(nota["id"]),
            usuario,
        )
        sb1_baixar_e_desreservar_atomico_tx(cur, produto, filial, qtd)

    reserva_status_tx(cur, int(reserva_id), "CONFIRMADA")

    if gera_titulo:
        ar_criar_tx(
            cur,
            filial=filial,
            cliente=cliente_nome,
            cliente_cod=cliente_cod,
            valor=valor_venda,
            ref_id=nota["id"],
            venc_dias=int(venc_dias),
            serie=nota["serie"],
        )

    log_tx(
        cur,
        usuario,
        f"Reserva {reserva_id} confirmada -> pedido {pedido_id} nf={nota['doc']}/{nota['serie']} tes={tes_cod} cfop={cfop_item}",
    )

    saldo_snapshot = sb1_get_tx(cur, produto, filial)
    saldo_snapshot["saldo_sd3"] = saldo_sd3_tx(cur, produto, filial)

    return {
        "reserva_id": int(reserva_id),
        "pedido_id": int(pedido_id),
        "nf_id": int(nota["id"]),
        "nf_doc": nota["doc"],
        "nf_serie": nota["serie"],
        "tes": tes_cod,
        "cfop": cfop_item,
        "cliente_cod": cliente_cod,
        "cliente_nome": cliente_nome,
        "preco_unit": float(preco),
        "valor_venda": float(valor_venda),
        "valor_cmv": float(valor_cmv),
        "icms": float(valor_icms),
        "ipi": float(valor_ipi),
        "pis": float(valor_pis),
        "cofins": float(valor_cofins),
        "icms_st": float(valor_icms_st),
        "difal": float(valor_difal),
        "total_bruto": float(total_bruto),
        "sb1": saldo_snapshot,
    }
