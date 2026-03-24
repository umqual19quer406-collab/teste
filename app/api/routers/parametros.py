from fastapi import APIRouter, Depends
from pydantic import BaseModel
from typing import Optional

from app.api.deps import get_current_user
from app.infra.db import db_transaction
from app.use_cases.sx5_uc import (
    sx5_listar_uc_tx,
    sx5_criar_uc_tx,
    sx5_atualizar_uc_tx,
    sx5_inativar_uc_tx,
)
from app.use_cases.fiscal_uc import sf4_salvar_uc_tx, sf4_listar_uc_tx, sf4_inativar_uc_tx
from app.use_cases.fiscal_regras_uc import (
    fiscal_regra_listar_uc_tx,
    fiscal_regra_salvar_uc_tx,
    fiscal_regra_inativar_uc_tx,
)
from app.use_cases.fiscal_ncm_uc import ncm_listar_uc_tx, ncm_salvar_uc_tx
from app.use_cases.series_uc import series_obter_uc_tx, series_definir_uc_tx, series_listar_sx5_uc_tx, series_reset_uc_tx
from app.use_cases.fechamento_uc import fechar_periodo_uc_tx, abrir_periodo_uc_tx
from app.use_cases.filiais_uc import filiais_listar_uc_tx, filiais_criar_uc_tx, filiais_inativar_uc_tx

router = APIRouter(prefix="/parametros", tags=["Parâmetros"])


class SX5CriarInput(BaseModel):
    filial: str = "01"
    tabela: str
    chave: str
    descr: str
    ativo: bool = True


class SX5AtualizarInput(BaseModel):
    filial: str = "01"
    tabela: str
    chave: str
    descr: Optional[str] = None
    ativo: Optional[bool] = None


class SF4SalvarInput(BaseModel):
    filial: str = "01"
    tes_cod: str
    cfop: str
    icms: float = 0.0
    ipi: float = 0.0
    pis: float = 0.0
    cofins: float = 0.0
    icms_st: float = 0.0
    difal: float = 0.0
    cst_icms: Optional[str] = None
    csosn: Optional[str] = None
    cst_pis: Optional[str] = None
    cst_cofins: Optional[str] = None
    tipo: str = "S"
    gera_tit: bool = True
    gera_est: bool = True
    descr: Optional[str] = None


class SeriesSalvarInput(BaseModel):
    filial: str = "01"
    serie_nf: Optional[str] = None
    serie_ar: Optional[str] = None
    serie_ap: Optional[str] = None


class FechamentoInput(BaseModel):
    filial: str = "01"
    ano: int
    mes: int


class NCMInput(BaseModel):
    filial: str = "01"
    ncm: str
    cfop: str
    icms: Optional[float] = None
    ipi: Optional[float] = None
    ativo: bool = True


class FilialInput(BaseModel):
    filial: str
    serie_nf: Optional[str] = None
    serie_ar: Optional[str] = None
    serie_ap: Optional[str] = None


class SF5RegraInput(BaseModel):
    filial: str = "01"
    tes_cod: str
    cliente_cod: Optional[str] = None
    produto: Optional[str] = None
    cfop: Optional[str] = None
    icms: Optional[float] = None
    ipi: Optional[float] = None
    pis: Optional[float] = None
    cofins: Optional[float] = None
    icms_st: Optional[float] = None
    difal: Optional[float] = None
    cst_icms: Optional[str] = None
    csosn: Optional[str] = None
    cst_pis: Optional[str] = None
    cst_cofins: Optional[str] = None
    gera_tit: Optional[bool] = None
    gera_est: Optional[bool] = None
    prioridade: int = 0
    ativo: bool = True
    regra_id: Optional[int] = None


@router.get("/sx5")
def listar_sx5(
    filial: str,
    tabela: str,
    ativos: bool = True,
    me: dict = Depends(get_current_user),
):
    with db_transaction() as (_, cur):
        return sx5_listar_uc_tx(cur, usuario=me["login"], filial=filial, tabela=tabela, ativos=ativos)


@router.post("/sx5")
def criar_sx5(dados: SX5CriarInput, me: dict = Depends(get_current_user)):
    with db_transaction() as (_, cur):
        return sx5_criar_uc_tx(
            cur,
            usuario=me["login"],
            filial=dados.filial,
            tabela=dados.tabela,
            chave=dados.chave,
            descr=dados.descr,
            ativo=bool(dados.ativo),
        )


@router.put("/sx5")
def atualizar_sx5(dados: SX5AtualizarInput, me: dict = Depends(get_current_user)):
    with db_transaction() as (_, cur):
        return sx5_atualizar_uc_tx(
            cur,
            usuario=me["login"],
            filial=dados.filial,
            tabela=dados.tabela,
            chave=dados.chave,
            descr=dados.descr,
            ativo=dados.ativo,
        )


@router.delete("/sx5")
def inativar_sx5(filial: str, tabela: str, chave: str, me: dict = Depends(get_current_user)):
    with db_transaction() as (_, cur):
        return sx5_inativar_uc_tx(cur, usuario=me["login"], filial=filial, tabela=tabela, chave=chave)


@router.post("/sf4")
def salvar_sf4(dados: SF4SalvarInput, me: dict = Depends(get_current_user)):
    with db_transaction() as (_, cur):
        return sf4_salvar_uc_tx(
            cur,
            usuario=me["login"],
            filial=dados.filial,
            tes_cod=dados.tes_cod,
            cfop=dados.cfop,
            icms=float(dados.icms),
            ipi=float(dados.ipi),
            pis=float(dados.pis),
            cofins=float(dados.cofins),
            icms_st=float(dados.icms_st),
            difal=float(dados.difal),
            cst_icms=dados.cst_icms,
            csosn=dados.csosn,
            cst_pis=dados.cst_pis,
            cst_cofins=dados.cst_cofins,
            tipo=dados.tipo,
            gera_tit=bool(dados.gera_tit),
            gera_est=bool(dados.gera_est),
            descr=dados.descr,
        )


@router.get("/sf4")
def listar_sf4(
    filial: str,
    ativos: bool = True,
    me: dict = Depends(get_current_user),
):
    with db_transaction() as (_, cur):
        return sf4_listar_uc_tx(cur, usuario=me["login"], filial=filial, ativos=ativos)


@router.delete("/sf4")
def inativar_sf4(
    filial: str,
    tes_cod: str,
    me: dict = Depends(get_current_user),
):
    with db_transaction() as (_, cur):
        return sf4_inativar_uc_tx(cur, usuario=me["login"], filial=filial, tes_cod=tes_cod)


@router.get("/series")
def obter_series(filial: str, me: dict = Depends(get_current_user)):
    with db_transaction() as (_, cur):
        return series_obter_uc_tx(cur, usuario=me["login"], filial=filial)


@router.put("/series")
def definir_series(dados: SeriesSalvarInput, me: dict = Depends(get_current_user)):
    with db_transaction() as (_, cur):
        return series_definir_uc_tx(
            cur,
            usuario=me["login"],
            filial=dados.filial,
            serie_nf=dados.serie_nf,
            serie_ar=dados.serie_ar,
            serie_ap=dados.serie_ap,
        )


@router.get("/series/sx5")
def listar_series_sx5(filial: str, me: dict = Depends(get_current_user)):
    with db_transaction() as (_, cur):
        return series_listar_sx5_uc_tx(cur, usuario=me["login"], filial=filial)


@router.post("/series/reset")
def resetar_series(filial: str, me: dict = Depends(get_current_user)):
    with db_transaction() as (_, cur):
        return series_reset_uc_tx(cur, usuario=me["login"], filial=filial)


@router.post("/fechamento/fechar")
def fechar_periodo(dados: FechamentoInput, me: dict = Depends(get_current_user)):
    with db_transaction() as (_, cur):
        return fechar_periodo_uc_tx(
            cur,
            usuario=me["login"],
            filial=dados.filial,
            ano=int(dados.ano),
            mes=int(dados.mes),
        )


@router.post("/fechamento/abrir")
def abrir_periodo(dados: FechamentoInput, me: dict = Depends(get_current_user)):
    with db_transaction() as (_, cur):
        return abrir_periodo_uc_tx(
            cur,
            usuario=me["login"],
            filial=dados.filial,
            ano=int(dados.ano),
            mes=int(dados.mes),
        )


@router.get("/sf5")
def listar_sf5(
    filial: str,
    tes_cod: Optional[str] = None,
    cliente_cod: Optional[str] = None,
    produto: Optional[str] = None,
    ativos: bool = True,
    me: dict = Depends(get_current_user),
):
    with db_transaction() as (_, cur):
        return fiscal_regra_listar_uc_tx(
            cur,
            usuario=me["login"],
            filial=filial,
            tes_cod=tes_cod,
            cliente_cod=cliente_cod,
            produto=produto,
            ativos=ativos,
        )


@router.post("/sf5")
def salvar_sf5(dados: SF5RegraInput, me: dict = Depends(get_current_user)):
    with db_transaction() as (_, cur):
        return fiscal_regra_salvar_uc_tx(
            cur,
            usuario=me["login"],
            filial=dados.filial,
            tes_cod=dados.tes_cod,
            cliente_cod=dados.cliente_cod,
            produto=dados.produto,
            cfop=dados.cfop,
            icms=(float(dados.icms) if dados.icms is not None else None),
            ipi=(float(dados.ipi) if dados.ipi is not None else None),
            pis=(float(dados.pis) if dados.pis is not None else None),
            cofins=(float(dados.cofins) if dados.cofins is not None else None),
            icms_st=(float(dados.icms_st) if dados.icms_st is not None else None),
            difal=(float(dados.difal) if dados.difal is not None else None),
            cst_icms=dados.cst_icms,
            csosn=dados.csosn,
            cst_pis=dados.cst_pis,
            cst_cofins=dados.cst_cofins,
            gera_tit=dados.gera_tit,
            gera_est=dados.gera_est,
            prioridade=int(dados.prioridade),
            ativo=bool(dados.ativo),
            regra_id=(int(dados.regra_id) if dados.regra_id is not None else None),
        )


@router.delete("/sf5")
def inativar_sf5(regra_id: int, me: dict = Depends(get_current_user)):
    with db_transaction() as (_, cur):
        return fiscal_regra_inativar_uc_tx(cur, usuario=me["login"], regra_id=int(regra_id))


@router.get("/ncm")
def listar_ncm(
    filial: str,
    ativos: bool = True,
    me: dict = Depends(get_current_user),
):
    with db_transaction() as (_, cur):
        return ncm_listar_uc_tx(cur, usuario=me["login"], filial=filial, ativos=ativos)


@router.post("/ncm")
def salvar_ncm(dados: NCMInput, me: dict = Depends(get_current_user)):
    with db_transaction() as (_, cur):
        return ncm_salvar_uc_tx(
            cur,
            usuario=me["login"],
            filial=dados.filial,
            ncm=dados.ncm,
            cfop=dados.cfop,
            icms=(float(dados.icms) if dados.icms is not None else None),
            ipi=(float(dados.ipi) if dados.ipi is not None else None),
            ativo=bool(dados.ativo),
        )


@router.get("/filiais")
def listar_filiais(me: dict = Depends(get_current_user)):
    with db_transaction() as (_, cur):
        return filiais_listar_uc_tx(cur, usuario=me["login"])


@router.post("/filiais")
def criar_filial(dados: FilialInput, me: dict = Depends(get_current_user)):
    with db_transaction() as (_, cur):
        return filiais_criar_uc_tx(
            cur,
            usuario=me["login"],
            filial=dados.filial,
            serie_nf=dados.serie_nf,
            serie_ar=dados.serie_ar,
            serie_ap=dados.serie_ap,
        )


@router.delete("/filiais")
def inativar_filial(filial: str, me: dict = Depends(get_current_user)):
    with db_transaction() as (_, cur):
        return filiais_inativar_uc_tx(cur, usuario=me["login"], filial=filial)
