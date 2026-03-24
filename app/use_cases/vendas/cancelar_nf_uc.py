from app.core.exceptions import BusinessError
from app.use_cases.usuarios_uc import exigir_perfil_tx
from app.infra.repositories.faturamento_repo import sf2_get_tx, sf2_cancelar_tx, sd2_cancelar_por_nf_tx, sd2_count_por_nf_tx
from app.infra.repositories.financeiro_repo import cancelar_ar_por_nf_tx
from app.infra.repositories.logs_repo import log_tx
from app.infra.repositories.fechamento_repo import fechamento_validar_periodo_tx


def cancelar_nf_tx(
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

    fechamento_validar_periodo_tx(cur, filial, nf["F2_EMISSAO"])

    # 1) Cancela AR vinculado (se existir). Bloqueia se BAIXADO.
    ar_cancelados = cancelar_ar_por_nf_tx(cur, filial=filial, nf_id=nf_id)

    # 2) valida SD2
    if sd2_count_por_nf_tx(cur, nf_id) == 0:
        raise BusinessError("NF sem itens SD2 (consistência)")

    # 3) Cancela SD2 da NF
    sd2_canceladas = sd2_cancelar_por_nf_tx(cur, nf_id=nf_id, usuario=usuario, motivo=motivo)

    # 4) Cancela SF2
    sf2_cancelar_tx(cur, nf_id=nf_id, usuario=usuario, motivo=motivo)

    log_tx(
        cur,
        usuario,
        f"NF {nf_id} cancelada filial={filial} ar_cancelados={ar_cancelados} sd2_canceladas={sd2_canceladas} motivo={motivo}",
    )

    return {
        "nf_id": int(nf_id),
        "filial": filial,
        "status": "CANCELADA",
        "ar_cancelados": int(ar_cancelados),
        "sd2_canceladas": int(sd2_canceladas),
    }
