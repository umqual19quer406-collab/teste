from app.core.exceptions import BusinessError
from app.use_cases.usuarios_uc import exigir_perfil_tx
from app.infra.repositories.faturamento_repo import (
    sf2_get_tx,
    sf2_cancelar_tx,
    sd2_cancelar_por_nf_tx,
    sd2_itens_por_nf_tx,
    sd2_count_por_nf_tx,
)
from app.infra.repositories.financeiro_repo import cancelar_ar_por_nf_tx
from app.infra.repositories.fiscal_repo import fiscal_get_tes_tx
from app.infra.repositories.sb1_repo import sb1_get_tx, sb1_entrada_tx
from app.infra.repositories.sd3_repo import sd3_mov_tx
from app.infra.repositories.logs_repo import log_tx
from app.infra.repositories.fechamento_repo import fechamento_validar_periodo_tx


def estornar_nf_tx(
    cur,
    usuario: str,
    nf_id: int,
    filial: str,
    motivo: str | None = None,
) -> dict:
    exigir_perfil_tx(cur, usuario, {"admin", "operador"})

    nf_id = int(nf_id)
    filial = (filial or "").strip() or "01"

    nf = sf2_get_tx(cur, nf_id)
    if not nf:
        raise BusinessError("NF não encontrada")

    nf_filial = str(nf.get("F2_FILIAL") or "").strip()
    if nf_filial and nf_filial != filial:
        raise BusinessError("NF não pertence à filial informada")

    status = str(nf.get("F2_STATUS") or "").strip().upper()
    if status == "CANCELADA":
        raise BusinessError("NF já está CANCELADA")

    tes_cod = str(nf.get("F2_TES") or "").strip()
    gera_estoque = True
    if tes_cod:
        tes = fiscal_get_tes_tx(cur, filial=filial, tes_cod=tes_cod)
        gera_estoque = bool(tes.get("F4_GERA_EST"))

    fechamento_validar_periodo_tx(cur, filial, nf["F2_EMISSAO"])

    # 1) Cancela AR vinculado (se existir). Bloqueia se BAIXADO.
    ar_cancelados = cancelar_ar_por_nf_tx(cur, filial=filial, nf_id=nf_id)

    # 2) valida SD2
    if sd2_count_por_nf_tx(cur, nf_id) == 0:
        raise BusinessError("NF sem itens SD2 (consistência)")

    # 3) Estorno de estoque/SD3 (somente itens não cancelados)
    sd2_itens = sd2_itens_por_nf_tx(cur, nf_id=nf_id, somente_ativos=True)
    valor_cmv_total = 0.0
    if gera_estoque and sd2_itens:
        for it in sd2_itens:
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
                origem="NF_ESTORNO",
                ref=str(nf_id),
                usuario=usuario,
            )

    # 4) Cancela SD2 e SF2
    sd2_canceladas = sd2_cancelar_por_nf_tx(cur, nf_id=nf_id, usuario=usuario, motivo=motivo)
    sf2_cancelar_tx(cur, nf_id=nf_id, usuario=usuario, motivo=motivo)

    log_tx(
        cur,
        usuario,
        f"NF {nf_id} ESTORNADA filial={filial} ar_cancelados={ar_cancelados} sd2_canceladas={sd2_canceladas} cmv={valor_cmv_total} motivo={motivo}",
    )

    return {
        "nf_id": int(nf_id),
        "filial": filial,
        "status": "CANCELADA",
        "ar_cancelados": int(ar_cancelados),
        "sd2_canceladas": int(sd2_canceladas),
        "valor_cmv_estornado": float(round(valor_cmv_total, 2)),
    }
