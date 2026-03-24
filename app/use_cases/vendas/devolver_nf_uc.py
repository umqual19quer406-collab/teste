from app.core.exceptions import BusinessError
from app.use_cases.usuarios_uc import exigir_perfil_tx
from app.infra.repositories.faturamento_repo import (
    sf2_get_tx,
    sf2_criar_tx,
    sd2_item_criar_tx,
    sd2_itens_por_nf_tx,
)
from app.infra.repositories.fiscal_repo import fiscal_get_tes_tx
from app.infra.repositories.sb1_repo import sb1_get_tx, sb1_entrada_tx
from app.infra.repositories.sd3_repo import sd3_mov_tx
from app.infra.repositories.logs_repo import log_tx
from app.infra.repositories.fechamento_repo import fechamento_validar_periodo_tx
from app.infra.repositories.financeiro_repo import ar_criar_tx, ap_criar_tx


def devolver_nf_tx(
    cur,
    usuario: str,
    nf_origem_id: int,
    filial: str,
    tes_cod: str,
    venc_dias: int = 30,
    titulo_tipo: str = "AP",  # compat: ignorado (Protheus-like)
) -> dict:
    """
    Gera NF de devolução (entrada) a partir de uma NF de venda.
    - TES deve ser tipo 'E'.
    - Gera SD2 e, se configurado, entrada de estoque + SD3.
    """
    exigir_perfil_tx(cur, usuario, {"admin", "operador"})

    filial = (filial or "").strip() or "01"
    nf_origem_id = int(nf_origem_id)
    tes_cod = (tes_cod or "").strip()
    if not tes_cod:
        raise BusinessError("TES é obrigatório para devolução")

    nf_origem = sf2_get_tx(cur, nf_origem_id)
    if not nf_origem:
        raise BusinessError("NF origem não encontrada")

    nf_filial = str(nf_origem.get("F2_FILIAL") or "").strip()
    if nf_filial and nf_filial != filial:
        raise BusinessError("NF origem não pertence à filial informada")

    if str(nf_origem.get("F2_STATUS") or "").strip().upper() == "CANCELADA":
        raise BusinessError("NF origem está CANCELADA")

    fechamento_validar_periodo_tx(cur, filial, nf_origem["F2_EMISSAO"])

    itens_origem = sd2_itens_por_nf_tx(cur, nf_origem_id, somente_ativos=True)
    if not itens_origem:
        raise BusinessError("NF origem sem itens ativos")

    # TES para devolução (entrada)
    tes = fiscal_get_tes_tx(cur, filial=filial, tes_cod=tes_cod)
    tes_tipo = str(tes.get("F4_TIPO") or "").strip().upper()
    if tes_tipo != "E":
        raise BusinessError("TES incompatível para devolução (F4_TIPO deve ser 'E')")
    cfop = (tes.get("F4_CFOP") or "").strip()
    if not cfop:
        raise BusinessError("TES sem CFOP configurado (F4_CFOP)")

    gera_estoque = bool(tes.get("F4_GERA_EST"))
    gera_titulo = bool(tes.get("F4_GERA_TIT"))

    # Totais a partir da NF origem
    valor_total = float(nf_origem.get("F2_VALOR") or 0)
    valor_icms = float(nf_origem.get("F2_ICMS") or 0)
    valor_ipi = float(nf_origem.get("F2_IPI") or 0)
    total_bruto = float(nf_origem.get("F2_TOTAL_BRUTO") or 0)

    nf_dev = sf2_criar_tx(
        cur,
        filial=filial,
        pedido_id=nf_origem.get("F2_PEDIDO_ID"),
        cliente=nf_origem.get("F2_CLIENTE"),
        cliente_cod=nf_origem.get("F2_CLIENTE_COD"),
        valor_total=valor_total,
        icms=valor_icms,
        ipi=valor_ipi,
        total_bruto=total_bruto,
        tes_cod=tes_cod,
        cfop=cfop,
        origem="DEVOLUCAO",
    )

    # Itens SD2 da devolução
    for it in itens_origem:
        item_no = int(it.get("D2_ITEM") or 1)
        sd2_item_criar_tx(
            cur,
            nf_id=nf_dev["id"],
            doc=nf_dev["doc"],
            serie=nf_dev["serie"],
            item=item_no,
            filial=filial,
            pedido_id=nf_origem.get("F2_PEDIDO_ID"),
            produto=str(it["D2_PRODUTO"]).strip(),
            qtd=int(it["D2_QTD"]),
            preco_unit=(float(it["D2_PRECO_UNIT"]) if it.get("D2_PRECO_UNIT") is not None else None),
            total=float(it["D2_TOTAL"]),
            icms=float(it["D2_ICMS"]),
            ipi=float(it["D2_IPI"]),
            tes_cod=tes_cod,
            cfop=cfop,
        )

    # Entrada de estoque + SD3 (se configurado)
    valor_cmv_total = 0.0
    if gera_estoque:
        for it in itens_origem:
            produto = str(it["D2_PRODUTO"]).strip()
            qtd = int(it["D2_QTD"])
            if qtd <= 0:
                continue
            sb1 = sb1_get_tx(cur, produto, filial)
            cm_unit = float(sb1["B1_CM"])
            valor_cmv = cm_unit * qtd
            valor_cmv_total += valor_cmv

            sb1_entrada_tx(cur, produto, filial, qtd)
            sd3_mov_tx(
                cur,
                filial=filial,
                produto=produto,
                tipo="E",
                qtd=qtd,
                custo_unit=cm_unit,
                valor=valor_cmv,
                origem="NF_DEVOLUCAO",
                ref=str(nf_dev["id"]),
                usuario=usuario,
            )

    # Geração financeira (devolução)
    titulo_gerado = False
    # Protheus-like: devolução (TES tipo E) gera AP quando configurado
    if gera_titulo:
        ap_criar_tx(
            cur,
            filial=filial,
            forn=nf_origem.get("F2_CLIENTE"),
            forn_cod=nf_origem.get("F2_CLIENTE_COD"),
            valor=float(valor_total),
            ref=str(nf_dev["id"]),
            venc_dias=int(venc_dias),
        )
        titulo_gerado = True

    log_tx(
        cur,
        usuario,
        f"NF devolução gerada nf_origem={nf_origem_id} nf_dev={nf_dev['doc']}/{nf_dev['serie']} tes={tes_cod} cfop={cfop} cmv={valor_cmv_total}",
    )

    return {
        "nf_origem_id": int(nf_origem_id),
        "nf_dev_id": int(nf_dev["id"]),
        "nf_dev_doc": nf_dev["doc"],
        "nf_dev_serie": nf_dev["serie"],
        "tes": tes_cod,
        "cfop": cfop,
        "valor_total": float(valor_total),
        "icms": float(valor_icms),
        "ipi": float(valor_ipi),
        "total_bruto": float(total_bruto),
        "valor_cmv_entrada": float(round(valor_cmv_total, 2)),
        "titulo_gerado": bool(titulo_gerado),
        "titulo_tipo": "AP" if gera_titulo else None,
    }
