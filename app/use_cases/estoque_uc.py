from app.core.exceptions import BusinessError 
from app.use_cases.usuarios_uc import exigir_perfil_tx 
from app.infra.repositories.sb1_repo import ( 
    sb1_get_tx, sb1_atualizar_cm_tx, sb1_entrada_tx, sb1_baixar_atomico_tx 
) 
from app.infra.repositories.sd3_repo import sd3_mov_tx, saldo_sd3_tx, extrato_sd3_tx 
from app.infra.repositories.financeiro_repo import ap_criar_tx 
from app.infra.repositories.logs_repo import log_tx 
 
def recalcular_cm(cm_atual: float, saldo: int, qtd_entrada: int, custo_unit: float) -> float: 
    novo = saldo + qtd_entrada 
    if novo <= 0: 
        return 0.0 
    return ((saldo * cm_atual) + (qtd_entrada * custo_unit)) / novo 
 
def entrada_estoque_tx(cur, usuario: str, produto: str, qtd: int, filial: str, 
                      custo_unit: float, forn: str | None, venc_dias: int) -> dict: 
    exigir_perfil_tx(cur, usuario, {"admin", "operador"}) 
    if qtd <= 0: 
        raise BusinessError("qtd deve ser > 0") 
    if custo_unit < 0: 
        raise BusinessError("custo_unit não pode ser negativo") 
 
    s = sb1_get_tx(cur, produto, filial) 
    cm_novo = recalcular_cm(float(s["B1_CM"]), int(s["B1_ESTOQUE"]), int(qtd), float(custo_unit)) 
    sb1_atualizar_cm_tx(cur, produto, filial, cm_novo) 
 
    valor = float(qtd) * float(custo_unit) 
    sd3_mov_tx(cur, filial, produto, "E", qtd, float(custo_unit), valor, "ENTRADA_ESTOQUE", None, 
usuario) 
    sb1_entrada_tx(cur, produto, filial, qtd) 
 
    if forn: 
        ap_criar_tx(cur, filial, forn, valor, ref=f"ENTRADA:{produto}", venc_dias=venc_dias) 
 
    log_tx(cur, usuario, f"Entrada {produto}/{filial} +{qtd} custo={custo_unit} cm={cm_novo}") 
 
    snap = sb1_get_tx(cur, produto, filial) 
    snap["saldo_sd3"] = saldo_sd3_tx(cur, produto, filial) 
    return snap 
 
def consultar_estoque_tx(cur, produto: str, filial: str) -> dict: 
    s = sb1_get_tx(cur, produto, filial) 
    s["DISPONIVEL"] = int(s["B1_ESTOQUE"]) - int(s["B1_RESERVADO"]) 
    s["saldo_sd3"] = saldo_sd3_tx(cur, produto, filial) 
    return s 
 
def extrato_sd3_uc_tx(cur, produto: str, filial: str, limite: int) -> list[dict]: 
    return extrato_sd3_tx(cur, produto, filial, limite) 