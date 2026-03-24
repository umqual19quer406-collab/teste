from datetime import date 
from app.core.exceptions import BusinessError 
from app.use_cases.usuarios_uc import exigir_perfil_tx 
 
from app.infra.repositories.vendas.sc5_pedidos_enriq_repo import ( 
    sc5_pedidos_enriq_listar_tx, 
    sc5_pedidos_enriq_contar_tx, 
) 
 
def listar_pedidos_enriq_tx( 
    cur, 
    usuario: str, 
    filial: str | None, 
    status: str | None, 
    origem: str | None, 
    de: date | None, 
    ate: date | None, 
    limit: int, 
    offset: int, 
) -> dict: 
    exigir_perfil_tx(cur, usuario, {"admin", "operador"}) 
 
    filial = (filial or "").strip() or None 
    status = (status or "").strip().upper() or None 
    origem = (origem or "").strip().upper() or None 
 
    if status and status not in {"ABERTO", "FATURADO", "CANCELADO"}: 
        raise BusinessError("status inválido (ABERTO/FATURADO/CANCELADO)") 
 
    if origem and origem not in {"VENDA", "RESERVA"}: 
        raise BusinessError("origem inválida (VENDA/RESERVA)") 
 
    limit = int(limit) 
    offset = int(offset) 
    if limit <= 0 or limit > 200: 
        raise BusinessError("limit deve estar entre 1 e 200") 
    if offset < 0: 
        raise BusinessError("offset deve ser >= 0") 
 
    if de is not None and ate is not None and de > ate: 
        raise BusinessError("de não pode ser maior que ate") 
 
    total = sc5_pedidos_enriq_contar_tx(cur, filial, status, origem, de, ate) 
    items = sc5_pedidos_enriq_listar_tx(cur, filial, status, origem, de, ate, limit, offset) 
 
    return {"total": total, "limit": limit, "offset": offset, "items": items} 