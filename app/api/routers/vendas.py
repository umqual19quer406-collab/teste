from datetime import date
from typing import Optional

from fastapi import APIRouter, Depends, Query
from pydantic import BaseModel, ConfigDict

from app.api.deps import get_current_user
from app.api.schemas.errors import common_error_responses
from app.infra.db import db_transaction
from app.use_cases.vendas.buscar_nf_uc import buscar_nf_por_doc_serie_tx
from app.use_cases.vendas.cancelar_nf_uc import cancelar_nf_tx
from app.use_cases.vendas.cancelar_pedido_uc import cancelar_pedido_tx
from app.use_cases.vendas.consultar_pedido_uc import consultar_pedido_tx
from app.use_cases.vendas.devolver_nf_uc import devolver_nf_tx
from app.use_cases.vendas.estornar_nf_uc import estornar_nf_tx
from app.use_cases.vendas.estornar_pedido_uc import estornar_pedido_faturado_venda_tx
from app.use_cases.vendas.faturar_pedido_uc import faturar_pedido_venda_tx
from app.use_cases.vendas.itens_uc import editar_item_tx, excluir_item_tx
from app.use_cases.vendas.liberacoes_uc import resumo_liberacao_pedido_tx
from app.use_cases.vendas.liberar_pedido_uc import liberar_item_pedido_tx, liberar_pedido_total_tx
from app.use_cases.vendas.listar_pedidos_enriq_uc import listar_pedidos_enriq_tx
from app.use_cases.vendas.listar_pedidos_uc import listar_pedidos_tx
from app.use_cases.vendas.pedidos_uc import adicionar_item_tx, criar_pedido_tx
from app.use_cases.vendas.recalcular_pedido_uc import pedido_recalcular_totais_tx
from app.use_cases.vendas.relatorios_nf_id_uc import relatorio_nf_rastreio_tx
from app.use_cases.vendas.relatorios_nf_uc import relatorio_nf_financeiro_tx

router = APIRouter(prefix="/vendas", tags=["Vendas"])


class PedidoCriarInput(BaseModel):
    model_config = ConfigDict(json_schema_extra={"example": {"filial": "01", "valor_total": 150.0, "status": "ABERTO"}})

    filial: str = "01"
    valor_total: float
    status: str = "ABERTO"
    icms: Optional[float] = None
    ipi: Optional[float] = None
    total_bruto: Optional[float] = None


class ItemCriarInput(BaseModel):
    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "filial": "01",
                "produto": "PROD001",
                "qtd": 3,
                "total": 150.0,
                "preco_unit": 50.0,
                "cmv_unit": 32.5,
            }
        }
    )

    filial: str = "01"
    produto: str
    qtd: int
    total: float
    preco_unit: Optional[float] = None
    cmv_unit: Optional[float] = None


class FaturarPedidoInput(BaseModel):
    model_config = ConfigDict(
        json_schema_extra={"example": {"filial": "01", "cliente_cod": "C0001", "venc_dias": 30, "tes_cod": "001"}}
    )

    filial: str = "01"
    cliente_cod: Optional[str] = None
    venc_dias: int = 30
    tes_cod: Optional[str] = "001"


class CancelarPedidoInput(BaseModel):
    filial: str = "01"
    modo: str = "AUTO"
    reativar_reserva: bool = True


class RecalcularPedidoInput(BaseModel):
    forcar: bool = False


class EditarItemInput(BaseModel):
    filial: Optional[str] = "01"
    qtd: int
    total: float
    preco_unit: float | None = None
    cmv_unit: float | None = None


class ExcluirItemInput(BaseModel):
    filial: Optional[str] = "01"


class EstornarPedidoInput(BaseModel):
    filial: str = "01"
    motivo: Optional[str] = None


class CancelarNFInput(BaseModel):
    filial: str = "01"
    motivo: Optional[str] = None


class EstornarNFInput(BaseModel):
    filial: str = "01"
    motivo: Optional[str] = None


class DevolverNFInput(BaseModel):
    filial: str = "01"
    tes_cod: str
    venc_dias: int = 30


class LiberarItemInput(BaseModel):
    filial: str = "01"
    produto: str
    qtd: int


class LiberarTudoInput(BaseModel):
    filial: str = "01"
    usar_estoque: bool = True


@router.post("/pedidos", responses=common_error_responses(400, 401, 403, 422, 500))
def criar_pedido(dados: PedidoCriarInput, me: dict = Depends(get_current_user)):
    with db_transaction() as (_, cur):
        filial = (dados.filial or "").strip() or "01"
        return criar_pedido_tx(
            cur,
            usuario=me["login"],
            filial=filial,
            valor_total=float(dados.valor_total),
            status=(dados.status or "ABERTO").strip(),
            icms=dados.icms,
            ipi=dados.ipi,
            total_bruto=dados.total_bruto,
        )


@router.post("/pedidos/{pedido_id}/itens", responses=common_error_responses(400, 401, 403, 422, 500))
def adicionar_item(pedido_id: int, dados: ItemCriarInput, me: dict = Depends(get_current_user)):
    with db_transaction() as (_, cur):
        filial = (dados.filial or "").strip() or "01"
        produto = (dados.produto or "").strip()
        preco_unit = (float(dados.preco_unit) if dados.preco_unit is not None else None)
        if dados.cmv_unit is not None:
            return adicionar_item_tx(
                cur,
                usuario=me["login"],
                pedido_id=int(pedido_id),
                filial=filial,
                produto=produto,
                qtd=int(dados.qtd),
                total=float(dados.total),
                preco_unit=preco_unit,
                cmv_unit=float(dados.cmv_unit),
            )
        return adicionar_item_tx(
            cur,
            usuario=me["login"],
            pedido_id=int(pedido_id),
            filial=filial,
            produto=produto,
            qtd=int(dados.qtd),
            total=float(dados.total),
            preco_unit=preco_unit,
        )


@router.post("/pedidos/{pedido_id}/faturar", responses=common_error_responses(400, 401, 403, 422, 500))
def faturar_pedido(pedido_id: int, dados: FaturarPedidoInput, me: dict = Depends(get_current_user)):
    with db_transaction() as (_, cur):
        return faturar_pedido_venda_tx(
            cur,
            usuario=me["login"],
            pedido_id=int(pedido_id),
            filial=dados.filial,
            cliente_cod=dados.cliente_cod,
            venc_dias=int(dados.venc_dias),
            tes_cod=(dados.tes_cod or "001"),
        )


@router.post("/pedidos/{pedido_id}/cancelar")
def cancelar_pedido(pedido_id: int, dados: CancelarPedidoInput, me: dict = Depends(get_current_user)):
    with db_transaction() as (_, cur):
        filial = (dados.filial or "").strip() or "01"
        return cancelar_pedido_tx(
            cur,
            usuario=me["login"],
            pedido_id=int(pedido_id),
            filial=filial,
            modo=(dados.modo or "AUTO"),
            reativar_reserva=bool(dados.reativar_reserva),
        )


@router.get("/pedidos/enriquecido")
def listar_pedidos_enriquecido(
    filial: Optional[str] = None,
    status: Optional[str] = None,
    origem: Optional[str] = None,
    de: Optional[date] = None,
    ate: Optional[date] = None,
    limit: int = Query(50, ge=1, le=200),
    offset: int = Query(0, ge=0),
    me: dict = Depends(get_current_user),
):
    with db_transaction() as (_, cur):
        return listar_pedidos_enriq_tx(
            cur,
            usuario=me["login"],
            filial=filial,
            status=status,
            origem=origem,
            de=de,
            ate=ate,
            limit=limit,
            offset=offset,
        )


@router.get("/pedidos/{pedido_id}")
def obter_pedido(pedido_id: int, me: dict = Depends(get_current_user)):
    with db_transaction() as (_, cur):
        return consultar_pedido_tx(cur, usuario=me["login"], pedido_id=int(pedido_id))


@router.get("/pedidos")
def listar_pedidos(
    filial: Optional[str] = None,
    status: Optional[str] = None,
    origem: Optional[str] = None,
    de: Optional[date] = None,
    ate: Optional[date] = None,
    limit: int = Query(50, ge=1, le=200),
    offset: int = Query(0, ge=0),
    me: dict = Depends(get_current_user),
):
    with db_transaction() as (_, cur):
        return listar_pedidos_tx(
            cur,
            usuario=me["login"],
            filial=filial,
            status=status,
            origem=origem,
            de=de,
            ate=ate,
            limit=limit,
            offset=offset,
        )


@router.post("/pedidos/{pedido_id}/recalcular")
def recalcular_pedido(pedido_id: int, dados: RecalcularPedidoInput, me: dict = Depends(get_current_user)):
    with db_transaction() as (_, cur):
        return pedido_recalcular_totais_tx(
            cur,
            usuario=me["login"],
            pedido_id=int(pedido_id),
            forcar=bool(dados.forcar),
        )


@router.put("/itens/{item_id}")
def editar_item(item_id: int, dados: EditarItemInput, me: dict = Depends(get_current_user)):
    with db_transaction() as (_, cur):
        if dados.cmv_unit is not None:
            return editar_item_tx(
                cur,
                usuario=me["login"],
                item_id=int(item_id),
                filial=dados.filial,
                qtd=dados.qtd,
                total=dados.total,
                preco_unit=dados.preco_unit,
                cmv_unit=dados.cmv_unit,
            )
        return editar_item_tx(
            cur,
            usuario=me["login"],
            item_id=int(item_id),
            filial=dados.filial,
            qtd=dados.qtd,
            total=dados.total,
            preco_unit=dados.preco_unit,
        )


@router.delete("/itens/{item_id}")
def excluir_item(item_id: int, dados: ExcluirItemInput, me: dict = Depends(get_current_user)):
    with db_transaction() as (_, cur):
        return excluir_item_tx(
            cur,
            usuario=me["login"],
            item_id=int(item_id),
            filial=dados.filial,
        )


@router.post("/pedidos/{pedido_id}/estornar")
def estornar_pedido(pedido_id: int, dados: EstornarPedidoInput, me: dict = Depends(get_current_user)):
    with db_transaction() as (_, cur):
        return estornar_pedido_faturado_venda_tx(
            cur,
            usuario=me["login"],
            pedido_id=int(pedido_id),
            filial=dados.filial,
            motivo=dados.motivo,
        )


@router.post("/nf/{nf_id}/cancelar")
def cancelar_nf(nf_id: int, dados: CancelarNFInput, me: dict = Depends(get_current_user)):
    with db_transaction() as (_, cur):
        return cancelar_nf_tx(
            cur,
            usuario=me["login"],
            nf_id=int(nf_id),
            filial=dados.filial,
            motivo=dados.motivo,
        )


@router.post("/nf/{nf_id}/estornar")
def estornar_nf(nf_id: int, dados: EstornarNFInput, me: dict = Depends(get_current_user)):
    with db_transaction() as (_, cur):
        return estornar_nf_tx(
            cur,
            usuario=me["login"],
            nf_id=int(nf_id),
            filial=dados.filial,
            motivo=dados.motivo,
        )


@router.post("/nf/{nf_id}/devolver")
def devolver_nf(nf_id: int, dados: DevolverNFInput, me: dict = Depends(get_current_user)):
    with db_transaction() as (_, cur):
        return devolver_nf_tx(
            cur,
            usuario=me["login"],
            nf_origem_id=int(nf_id),
            filial=dados.filial,
            tes_cod=dados.tes_cod,
            venc_dias=int(dados.venc_dias),
        )


@router.post("/pedidos/{pedido_id}/liberar")
def liberar_pedido_item(pedido_id: int, dados: LiberarItemInput, me: dict = Depends(get_current_user)):
    with db_transaction() as (_, cur):
        return liberar_item_pedido_tx(
            cur,
            usuario=me["login"],
            pedido_id=int(pedido_id),
            filial=dados.filial,
            produto=dados.produto,
            qtd=int(dados.qtd),
        )


@router.post("/pedidos/{pedido_id}/liberar-tudo")
def liberar_pedido_total(pedido_id: int, dados: LiberarTudoInput, me: dict = Depends(get_current_user)):
    with db_transaction() as (_, cur):
        return liberar_pedido_total_tx(
            cur,
            usuario=me["login"],
            pedido_id=int(pedido_id),
            filial=dados.filial,
            usar_estoque=bool(dados.usar_estoque),
        )


@router.get("/pedidos/{pedido_id}/liberacoes")
def resumo_liberacao_pedido(pedido_id: int, me: dict = Depends(get_current_user)):
    with db_transaction() as (_, cur):
        return resumo_liberacao_pedido_tx(cur, usuario=me["login"], pedido_id=int(pedido_id))


@router.get("/pedidos/{pedido_id}/nf-financeiro")
def relatorio_nf_financeiro(
    pedido_id: int,
    nf_status: Optional[str] = None,
    ar_status: Optional[str] = None,
    sc9_status: Optional[str] = None,
    me: dict = Depends(get_current_user),
):
    with db_transaction() as (_, cur):
        return relatorio_nf_financeiro_tx(
            cur,
            usuario=me["login"],
            pedido_id=int(pedido_id),
            nf_status=nf_status,
            ar_status=ar_status,
            sc9_status=sc9_status,
        )


@router.get("/nf/{nf_id}/rastreio")
def relatorio_nf_rastreio(nf_id: int, me: dict = Depends(get_current_user)):
    with db_transaction() as (_, cur):
        return relatorio_nf_rastreio_tx(cur, usuario=me["login"], nf_id=int(nf_id))


@router.get("/nf/buscar")
def buscar_nf(
    filial: str,
    doc: str,
    serie: str,
    me: dict = Depends(get_current_user),
):
    with db_transaction() as (_, cur):
        return buscar_nf_por_doc_serie_tx(
            cur,
            usuario=me["login"],
            filial=filial,
            doc=doc,
            serie=serie,
        )
