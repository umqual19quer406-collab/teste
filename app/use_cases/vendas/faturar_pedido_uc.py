from app.core.exceptions import BusinessError
from app.use_cases.usuarios_uc import exigir_perfil_tx

from app.infra.repositories.faturamento_repo import sd2_item_criar_tx, sf2_criar_tx
from app.infra.repositories.fechamento_repo import fechamento_validar_periodo_tx
from app.infra.repositories.financeiro_repo import ar_criar_tx
from app.infra.repositories.fiscal_repo import fiscal_get_tes_tx, fiscal_resolver_item_tx
from app.infra.repositories.logs_repo import log_tx
from app.infra.repositories.sa1_repo import sa1_get_tx
from app.infra.repositories.sb1_repo import sb1_baixar_atomico_tx, sb1_get_tx
from app.infra.repositories.sd3_repo import sd3_mov_tx
from app.infra.repositories.sm0_repo import sm0_existe_tx
from app.infra.repositories.vendas.sc5_pedidos_repo import (
    sc5_pedido_atualizar_valor_total_tx,
    sc5_pedido_get_tx,
    sc5_pedido_marcar_faturado_tx,
)
from app.infra.repositories.vendas.sc6_itens_repo import sc6_itens_do_pedido_tx
from app.infra.repositories.vendas.sc6_totais_repo import sc6_totais_do_pedido_tx
from app.infra.repositories.vendas.sc9_liberacao_repo import sc9_qtd_liberada_por_pedido_tx


def _item_total(it: dict) -> float:
    total = it.get("C6_TOTAL")
    if total is None:
        total = it.get("C6_VALOR")
    if total is None:
        preco_unit = it.get("C6_PRECO_UNIT") or 0
        total = float(preco_unit) * int(it.get("C6_QTD") or 0)
    return float(total)


def faturar_pedido_venda_tx(
    cur,
    usuario: str,
    pedido_id: int,
    filial: str,
    cliente_cod: str | None,
    venc_dias: int = 30,
    tes_cod: str = "001",
) -> dict:
    exigir_perfil_tx(cur, usuario, {"admin", "operador"})

    filial = (filial or "").strip() or "01"
    if not sm0_existe_tx(cur, filial):
        raise BusinessError("Filial não cadastrada (SM0_EMPRESA)")
    pedido_id = int(pedido_id)

    p = sc5_pedido_get_tx(cur, pedido_id)
    if not p:
        raise BusinessError("Pedido não encontrado")
    fechamento_validar_periodo_tx(cur, filial, p["C5_DATA"])

    if str(p.get("C5_FILIAL") or "").strip() != filial:
        raise BusinessError(f"Pedido {pedido_id} não pertence à filial {filial}")

    status = str(p.get("C5_STATUS") or "").strip().upper()
    if status != "ABERTO":
        raise BusinessError("Apenas pedido ABERTO pode ser faturado")

    origem = str(p.get("C5_ORIGEM") or "VENDA").strip().upper()
    if origem != "VENDA":
        raise BusinessError("Este endpoint fatura apenas pedidos de origem VENDA")

    itens = sc6_itens_do_pedido_tx(cur, pedido_id)
    if not itens:
        raise BusinessError("Pedido sem itens (SC6)")
    for it in itens:
        if not it.get("C6_ITEM"):
            raise BusinessError("Item sem C6_ITEM (numeração) - recalcule ou gere C6_ITEM")

    # 0) valida liberações (SC9)
    liberados = sc9_qtd_liberada_por_pedido_tx(cur, pedido_id)
    for it in itens:
        prod = str(it["C6_PRODUTO"]).strip()
        qtd = int(it["C6_QTD"])
        item_no = int(it.get("C6_ITEM") or 0)
        qtd_lib = int(liberados.get(item_no, 0))
        if qtd_lib < qtd:
            raise BusinessError(
                f"Item {prod} não liberado (SC9). Liberado={qtd_lib} Pedido={qtd} (liberação parcial)"
            )

    # 1) recalcula total (fonte de verdade = SC6) e atualiza SC5
    tot = sc6_totais_do_pedido_tx(cur, pedido_id)
    valor_venda = float(tot["valor_itens"])
    if valor_venda <= 0:
        raise BusinessError("Valor do pedido deve ser > 0")

    sc5_pedido_atualizar_valor_total_tx(cur, pedido_id, valor_venda)

    # 2) snapshot cliente (opcional)
    cliente_nome = None
    if cliente_cod:
        c = sa1_get_tx(cur, filial=filial, cod=str(cliente_cod).strip())
        if not c:
            raise BusinessError("Cliente não encontrado (SA1)")
        cliente_nome = c["A1_NOME"]

    # 3) TES / fiscal
    f = fiscal_get_tes_tx(cur, filial, tes_cod=tes_cod)
    tes_cod = str(f.get("F4_COD") or tes_cod).strip()
    tes_tipo = str(f.get("F4_TIPO") or "").strip().upper()
    cfop_base = (f.get("F4_CFOP") or "").strip()

    if tes_tipo and tes_tipo != "S":
        raise BusinessError("TES incompatível para venda (F4_TIPO deve ser 'S')")
    if not cfop_base:
        raise BusinessError("TES sem CFOP configurado (F4_CFOP)")

    # 4) calcula impostos por item
    valor_icms = 0.0
    valor_ipi = 0.0
    valor_pis = 0.0
    valor_cofins = 0.0
    valor_icms_st = 0.0
    valor_difal = 0.0
    itens_calc = []
    gera_titulo = False
    for it in itens:
        item_total = _item_total(it)
        fiscal_item = fiscal_resolver_item_tx(
            cur,
            filial=filial,
            tes_cod=tes_cod,
            cliente_cod=cliente_cod,
            produto=str(it["C6_PRODUTO"]).strip(),
        )
        item_icms = round(item_total * float(fiscal_item["icms"]), 2)
        item_ipi = round(item_total * float(fiscal_item["ipi"]), 2)
        item_pis = round(item_total * float(fiscal_item["pis"]), 2)
        item_cofins = round(item_total * float(fiscal_item["cofins"]), 2)
        item_icms_st = round(item_total * float(fiscal_item["icms_st"]), 2)
        item_difal = round(item_total * float(fiscal_item["difal"]), 2)
        itens_calc.append(
            (
                it,
                item_total,
                item_icms,
                item_ipi,
                item_pis,
                item_cofins,
                item_icms_st,
                item_difal,
                fiscal_item["cfop"],
                bool(fiscal_item["gera_est"]),
                fiscal_item.get("cst_icms"),
                fiscal_item.get("csosn"),
                fiscal_item.get("cst_pis"),
                fiscal_item.get("cst_cofins"),
            )
        )
        if bool(fiscal_item["gera_tit"]):
            gera_titulo = True
        valor_icms += item_icms
        valor_ipi += item_ipi
        valor_pis += item_pis
        valor_cofins += item_cofins
        valor_icms_st += item_icms_st
        valor_difal += item_difal

    total_bruto = round(valor_venda + valor_ipi + valor_icms_st + valor_difal, 2)

    # 5) SF2 + SD2 (NF)
    nf = sf2_criar_tx(
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
        origem="VENDA",
        pis=valor_pis,
        cofins=valor_cofins,
        icms_st=valor_icms_st,
        difal=valor_difal,
    )

    for idx, (
        it,
        item_total,
        item_icms,
        item_ipi,
        item_pis,
        item_cofins,
        item_icms_st,
        item_difal,
        cfop_item,
        _,
        cst_icms,
        csosn,
        cst_pis,
        cst_cofins,
    ) in enumerate(itens_calc, start=1):
        item_no = int(it.get("C6_ITEM") or idx)
        sd2_item_criar_tx(
            cur,
            nf_id=nf["id"],
            doc=nf["doc"],
            serie=nf["serie"],
            item=item_no,
            filial=filial,
            pedido_id=pedido_id,
            produto=str(it["C6_PRODUTO"]).strip(),
            qtd=int(it["C6_QTD"]),
            preco_unit=(float(it["C6_PRECO_UNIT"]) if it.get("C6_PRECO_UNIT") is not None else None),
            total=float(item_total),
            icms=float(item_icms),
            ipi=float(item_ipi),
            tes_cod=tes_cod,
            cfop=cfop_item or cfop_base,
            pis=float(item_pis),
            cofins=float(item_cofins),
            icms_st=float(item_icms_st),
            difal=float(item_difal),
            cst_icms=cst_icms,
            csosn=csosn,
            cst_pis=cst_pis,
            cst_cofins=cst_cofins,
        )

    # 6) estoque + SD3 (saída), conforme TES
    valor_cmv_total = 0.0
    if itens_calc:
        for it, _, _, _, _, _, _, _, _, gera_est, _, _, _, _ in itens_calc:
            if not gera_est:
                continue
            prod = str(it["C6_PRODUTO"]).strip()
            qtd = int(it["C6_QTD"])

            sb1 = sb1_get_tx(cur, prod, filial)
            cmv_override = it.get("C6_CMV_UNIT")
            cm_unit = float(cmv_override) if cmv_override is not None else float(sb1["B1_CM"])
            valor_cmv = cm_unit * qtd
            valor_cmv_total += valor_cmv

            sb1_baixar_atomico_tx(cur, prod, filial, qtd)

            sd3_mov_tx(
                cur,
                filial=filial,
                produto=prod,
                tipo="S",
                qtd=qtd,
                custo_unit=cm_unit,
                valor=valor_cmv,
                origem="NF_EMITIDA",
                ref=str(nf["id"]),
                usuario=usuario,
            )

    # 7) marca pedido como FATURADO (com impostos)
    sc5_pedido_marcar_faturado_tx(cur, pedido_id, icms=valor_icms, ipi=valor_ipi, total_bruto=total_bruto)

    # 8) cria AR (SE1) vinculado à NF (SF2)
    if gera_titulo:
        ar_criar_tx(
            cur,
            filial=filial,
            cliente=cliente_nome,
            cliente_cod=cliente_cod,
            valor=valor_venda,
            ref_id=nf["id"],
            venc_dias=int(venc_dias),
            serie=nf["serie"],
        )

    log_tx(
        cur,
        usuario,
        f"Pedido {pedido_id} FATURADO origem=VENDA nf={nf['doc']}/{nf['serie']} valor={valor_venda} icms={valor_icms} ipi={valor_ipi} pis={valor_pis} cofins={valor_cofins} icms_st={valor_icms_st} difal={valor_difal} cmv={valor_cmv_total} cliente_cod={cliente_cod} tes={tes_cod} cfop={cfop_base}",
    )

    return {
        "pedido_id": pedido_id,
        "filial": filial,
        "status": "FATURADO",
        "origem": "VENDA",
        "nf_id": int(nf["id"]),
        "nf_doc": nf["doc"],
        "nf_serie": nf["serie"],
        "tes": tes_cod,
        "cfop": cfop_base,
        "valor_venda": float(valor_venda),
        "icms": float(valor_icms),
        "ipi": float(valor_ipi),
        "pis": float(valor_pis),
        "cofins": float(valor_cofins),
        "icms_st": float(valor_icms_st),
        "difal": float(valor_difal),
        "total_bruto": float(total_bruto),
        "valor_cmv": float(round(valor_cmv_total, 2)),
        "cliente_cod": cliente_cod,
        "cliente_nome": cliente_nome,
        "qtd_itens": int(tot["qtd_itens"]),
    }
