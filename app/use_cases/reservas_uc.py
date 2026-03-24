from datetime import date

from app.core.exceptions import BusinessError
from app.infra.db import fetchone_dict
from app.infra.repositories.logs_repo import log_tx
from app.infra.repositories.preco_repo import buscar_preco_vigente_tx
from app.infra.repositories.reservas_repo import (
    reserva_criar_tx,
    reserva_get_tx,
    reserva_set_cliente_preco_tx,
    reserva_status_tx,
)
from app.infra.repositories.sa1_repo import sa1_get_tx
from app.infra.repositories.sb1_repo import (
    sb1_baixar_e_desreservar_atomico_tx,
    sb1_cancelar_reserva_atomico_tx,
    sb1_get_tx,
    sb1_reservar_atomico_tx,
)
from app.infra.repositories.sd3_repo import saldo_sd3_tx, sd3_mov_tx
from app.use_cases.usuarios_uc import exigir_perfil_tx
from app.use_cases.vendas.faturamento_uc import faturar_reserva_tx


def _tabela_padrao_id_tx(cur, filial: str, cod: str = "0001") -> int:
    cur.execute("SELECT COL_LENGTH('dbo.PR0_TABELA','D_E_L_E_T_') AS col")
    has_deleted_column = cur.fetchone()
    has_deleted_column = bool(has_deleted_column and has_deleted_column[0] is not None)

    sql = """
        SELECT TOP 1 ID
        FROM dbo.PR0_TABELA
        WHERE P0_FILIAL=? AND P0_COD=? AND P0_ATIVA=1
    """
    if has_deleted_column:
        sql += " AND (D_E_L_E_T_ IS NULL OR D_E_L_E_T_ <> '*')"
    sql += " ORDER BY ID"

    cur.execute(sql, (filial, cod))
    row = fetchone_dict(cur)
    if not row:
        raise BusinessError(f"Não existe tabela de preço ativa (PR0) filial={filial} cod={cod}")
    return int(row["ID"])


def criar_reserva_tx(
    cur,
    usuario: str,
    produto: str,
    qtd: int,
    filial: str,
    cliente_cod: str | None = None,
    tabela_cod: str = "0001",
) -> dict:
    exigir_perfil_tx(cur, usuario, {"admin", "operador"})
    if int(qtd) <= 0:
        raise BusinessError("qtd deve ser > 0")

    produto_row = sb1_get_tx(cur, produto, filial)

    tabela_id = _tabela_padrao_id_tx(cur, filial, cod=tabela_cod)
    preco_source = "TABELA"
    try:
        preco_unit = buscar_preco_vigente_tx(
            cur,
            filial=filial,
            tabela_id=tabela_id,
            produto=produto,
            data=date.today(),
        )
    except BusinessError as exc:
        if str(exc) != "Preco nao encontrado":
            raise
        preco_unit = float(produto_row.get("B1_PRECO") or 0.0)
        if preco_unit <= 0:
            raise
        preco_source = "PRODUTO"
    total = float(preco_unit) * int(qtd)

    sb1_reservar_atomico_tx(cur, produto, filial, int(qtd))

    reserva_id = reserva_criar_tx(
        cur,
        filial=filial,
        produto=produto,
        qtd=int(qtd),
        usuario=usuario,
        cliente_cod=cliente_cod,
        tabela_id=tabela_id,
        preco_unit=float(preco_unit),
        total=float(total),
    )

    log_tx(
        cur,
        usuario,
        f"Reserva {reserva_id} criada {produto}/{filial} qtd={qtd} cliente_cod={cliente_cod} tab_id={tabela_id} preco_unit={preco_unit} fonte_preco={preco_source}",
    )

    saldo_snapshot = sb1_get_tx(cur, produto, filial)
    saldo_snapshot["saldo_sd3"] = saldo_sd3_tx(cur, produto, filial)

    return {
        "reserva_id": int(reserva_id),
        "status": "ABERTA",
        "cliente_cod": cliente_cod,
        "tabela_id": int(tabela_id),
        "preco_unit": float(preco_unit),
        "preco_source": preco_source,
        "total": float(total),
        "sb1": saldo_snapshot,
    }


def cancelar_reserva_tx(cur, usuario: str, reserva_id: int) -> dict:
    exigir_perfil_tx(cur, usuario, {"admin", "operador"})
    reserva = reserva_get_tx(cur, int(reserva_id))
    if not reserva:
        raise BusinessError("Reserva não encontrada")
    if reserva["Z0_STATUS"] != "ABERTA":
        raise BusinessError("Apenas reserva ABERTA pode ser cancelada")

    produto = reserva["Z0_PRODUTO"]
    filial = reserva["Z0_FILIAL"]
    qtd = int(reserva["Z0_QTD"])

    sb1_cancelar_reserva_atomico_tx(cur, produto, filial, qtd)
    reserva_status_tx(cur, int(reserva_id), "CANCELADA")
    log_tx(cur, usuario, f"Reserva {reserva_id} cancelada")

    saldo_snapshot = sb1_get_tx(cur, produto, filial)
    saldo_snapshot["saldo_sd3"] = saldo_sd3_tx(cur, produto, filial)
    return {"reserva_id": int(reserva_id), "status": "CANCELADA", "sb1": saldo_snapshot}


def confirmar_reserva_tx(
    cur,
    usuario: str,
    reserva_id: int,
    cliente_cod: str | None,
    venc_dias: int,
    tes_cod: str | None = None,
) -> dict:
    return faturar_reserva_tx(
        cur=cur,
        usuario=usuario,
        reserva_id=int(reserva_id),
        cliente_cod=cliente_cod,
        venc_dias=int(venc_dias),
        tes_cod=(tes_cod or "001"),
    )
