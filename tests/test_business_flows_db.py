from __future__ import annotations

from datetime import date
from uuid import uuid4

import pytest

from app.core.exceptions import BusinessError
from app.core.security import hash_password
from app.infra.repositories.fechamento_repo import fechamento_periodo_aberto_tx
from app.infra.repositories.financeiro_repo import listar_ar_tx
from app.infra.repositories.fiscal_repo import fiscal_upsert_tx
from app.infra.repositories.relatorios_repo import consistencia_fiscal_tx
from app.infra.repositories.sa1_repo import sa1_criar_tx
from app.infra.repositories.sa2_repo import sa2_criar_tx
from app.infra.repositories.sb1_repo import sb1_atualizar_cm_tx, sb1_entrada_tx, sb1_upsert_tx
from app.infra.repositories.serie_repo import seed_series_basicas_tx
from app.infra.repositories.sm0_repo import sm0_criar_tx
from app.infra.repositories.relatorios_repo import conciliacao_nf_financeiro_tx, dre_simples_tx, margem_por_produto_tx
from app.use_cases.ap_lancamento_uc import lancar_ap_uc_tx
from app.use_cases.fechamento_uc import abrir_periodo_uc_tx, fechar_periodo_uc_tx
from app.use_cases.financeiro_uc import listar_ap_uc_tx, pagar_ap_uc_tx, receber_ar_uc_tx, saldo_caixa_uc_tx
from app.use_cases.reservas_uc import cancelar_reserva_tx, confirmar_reserva_tx, criar_reserva_tx
from app.use_cases.vendas.faturar_pedido_uc import faturar_pedido_venda_tx
from app.use_cases.vendas.pedidos_uc import adicionar_item_tx, criar_pedido_tx
from tests.conftest import integration_db_cursor


def _seed_admin(cur, login: str) -> None:
    cur.execute(
        """
        INSERT INTO dbo.USUARIOS (U_LOGIN, U_SENHA_HASH, U_PERFIL)
        VALUES (?, ?, 'admin')
        """,
        (login, hash_password("SenhaForte123!")),
    )


def _seed_caixa(cur, filial: str, nome: str = "CAIXA TESTE") -> int:
    cur.execute(
        """
        INSERT INTO dbo.SE5_CONTAS (E5_FILIAL, E5_NOME, E5_TIPO, E5_ATIVA)
        VALUES (?, ?, 'CAIXA', 1);
        SELECT CAST(SCOPE_IDENTITY() AS INT) AS id;
        """,
        (filial, nome),
    )
    row = cur.fetchone()
    return int(row[0])


def _seed_fornecedor(cur, filial: str, forn_cod: str) -> None:
    sa2_criar_tx(cur, filial=filial, cod=forn_cod, nome="Fornecedor Integracao")


def _seed_price_table(cur, filial: str, produto_cod: str, tabela_cod: str = "0001", preco: float = 55.0) -> int:
    cur.execute(
        """
        INSERT INTO dbo.PR0_TABELA (P0_FILIAL, P0_COD, P0_DESC, P0_ATIVA)
        VALUES (?, ?, ?, 1);
        SELECT CAST(SCOPE_IDENTITY() AS INT) AS id;
        """,
        (filial, tabela_cod, f"TABELA {tabela_cod}"),
    )
    row = cur.fetchone()
    tabela_id = int(row[0])
    cur.execute(
        """
        INSERT INTO dbo.PR1_PRECO (P1_FILIAL, P1_TABELA_ID, P1_PRODUTO, P1_PRECO, P1_DTINI, P1_DTFIM)
        VALUES (?, ?, ?, ?, CAST(GETDATE() AS DATE), NULL)
        """,
        (filial, tabela_id, produto_cod, float(preco)),
    )
    return tabela_id


def _seed_sales_minimum(cur, filial: str, admin_login: str, cliente_cod: str, produto_cod: str) -> int:
    sm0_criar_tx(cur, filial=filial, serie_nf="1", serie_ar="1", serie_ap="1")
    seed_series_basicas_tx(cur, filial=filial)
    fiscal_upsert_tx(
        cur,
        filial=filial,
        tes_cod="001",
        cfop="5102",
        icms=0.18,
        ipi=0.05,
        tipo="S",
        gera_tit=True,
        gera_est=True,
        descr="TES VENDA TESTE",
    )
    sa1_criar_tx(cur, filial=filial, cod=cliente_cod, nome="Cliente Integracao")
    sb1_upsert_tx(cur, cod=produto_cod, desc="Produto Integracao", preco=50.0, filial=filial)
    sb1_entrada_tx(cur, produto=produto_cod, filial=filial, qtd=20)
    sb1_atualizar_cm_tx(cur, produto=produto_cod, filial=filial, cm_novo=20.0)
    return _seed_caixa(cur, filial=filial, nome=f"CAIXA {admin_login}")


def test_fluxo_real_venda_ar_caixa_db():
    run_id = uuid4().hex[:8].upper()
    filial = f"T{run_id[:1]}"
    admin_login = f"admin_it_{run_id}"
    cliente_cod = f"C{run_id[:6]}"
    produto_cod = f"P{run_id[:6]}"

    with integration_db_cursor() as (_, cur):
        _seed_admin(cur, admin_login)
        conta_id = _seed_sales_minimum(
            cur,
            filial=filial,
            admin_login=admin_login,
            cliente_cod=cliente_cod,
            produto_cod=produto_cod,
        )

        pedido = criar_pedido_tx(
            cur,
            usuario=admin_login,
            filial=filial,
            valor_total=0.0,
            status="ABERTO",
        )
        pedido_id = int(pedido["pedido_id"])

        item = adicionar_item_tx(
            cur,
            usuario=admin_login,
            pedido_id=pedido_id,
            filial=filial,
            produto=produto_cod,
            qtd=2,
            total=100.0,
            preco_unit=50.0,
        )
        assert item["novo_total"] == 100.0

        faturamento = faturar_pedido_venda_tx(
            cur,
            usuario=admin_login,
            pedido_id=pedido_id,
            filial=filial,
            cliente_cod=cliente_cod,
            venc_dias=30,
            tes_cod="001",
        )
        assert faturamento["status"] == "FATURADO"
        assert faturamento["valor_venda"] == 100.0

        ar_list = listar_ar_tx(cur, filial=filial, status="ABERTO")
        assert len(ar_list) == 1
        titulo_id = int(ar_list[0]["ID"])
        assert float(ar_list[0]["E1_VALOR"]) == 100.0

        recebimento = receber_ar_uc_tx(
            cur,
            usuario=admin_login,
            titulo_id=titulo_id,
            conta_id=conta_id,
        )
        assert recebimento["status"] == "BAIXADO"

        saldo = saldo_caixa_uc_tx(cur, filial=filial, conta_id=conta_id, ate=None)
        assert saldo["saldo"] == 100.0


def test_fluxo_real_ap_pagamento_caixa_db():
    run_id = uuid4().hex[:8].upper()
    filial = f"U{run_id[:1]}"
    admin_login = f"admin_it_{run_id}"
    forn_cod = f"F{run_id[:6]}"

    with integration_db_cursor() as (_, cur):
        _seed_admin(cur, admin_login)
        sm0_criar_tx(cur, filial=filial, serie_nf="1", serie_ar="1", serie_ap="1")
        seed_series_basicas_tx(cur, filial=filial)
        _seed_fornecedor(cur, filial=filial, forn_cod=forn_cod)
        conta_id = _seed_caixa(cur, filial=filial, nome=f"CAIXA AP {admin_login}")

        lancamento = lancar_ap_uc_tx(
            cur,
            usuario=admin_login,
            filial=filial,
            forn_cod=forn_cod,
            valor=80.0,
            ref="MANUAL-IT",
            venc_dias=15,
        )
        assert lancamento["ok"] is True

        ap_list = listar_ap_uc_tx(cur, usuario=admin_login, filial=filial, status="ABERTO")
        assert len(ap_list) == 1
        titulo_id = int(ap_list[0]["ID"])
        assert float(ap_list[0]["F1_VALOR"]) == 80.0

        pagamento = pagar_ap_uc_tx(cur, usuario=admin_login, titulo_id=titulo_id, conta_id=conta_id)
        assert pagamento["status"] == "BAIXADO"

        saldo = saldo_caixa_uc_tx(cur, filial=filial, conta_id=conta_id, ate=None)
        assert saldo["saldo"] == -80.0


def test_fluxo_real_reserva_confirmacao_cancelamento_db():
    run_id = uuid4().hex[:8].upper()
    filial = f"R{run_id[:1]}"
    admin_login = f"admin_it_{run_id}"
    cliente_cod = f"C{run_id[:6]}"
    produto_cod = f"P{run_id[:6]}"

    with integration_db_cursor() as (_, cur):
        _seed_admin(cur, admin_login)
        _seed_sales_minimum(
            cur,
            filial=filial,
            admin_login=admin_login,
            cliente_cod=cliente_cod,
            produto_cod=produto_cod,
        )
        _seed_price_table(cur, filial=filial, produto_cod=produto_cod, preco=60.0)

        reserva = criar_reserva_tx(
            cur,
            usuario=admin_login,
            produto=produto_cod,
            qtd=2,
            filial=filial,
            cliente_cod=cliente_cod,
            tabela_cod="0001",
        )
        reserva_id = int(reserva["reserva_id"])
        assert reserva["status"] == "ABERTA"

        confirmacao = confirmar_reserva_tx(
            cur,
            usuario=admin_login,
            reserva_id=reserva_id,
            cliente_cod=cliente_cod,
            venc_dias=30,
            tes_cod="001",
        )
        assert confirmacao["reserva_id"] == reserva_id
        assert confirmacao["pedido_id"] > 0
        assert confirmacao["nf_id"] > 0
        assert confirmacao["valor_venda"] == 120.0

        ar_list = listar_ar_tx(cur, filial=filial, status="ABERTO")
        assert len(ar_list) == 1
        assert float(ar_list[0]["E1_VALOR"]) == 120.0

        with pytest.raises(BusinessError):
            cancelar_reserva_tx(cur, usuario=admin_login, reserva_id=reserva_id)


def test_relatorios_e_fechamento_db():
    run_id = uuid4().hex[:8].upper()
    filial = f"D{run_id[:1]}"
    admin_login = f"admin_it_{run_id}"
    cliente_cod = f"C{run_id[:6]}"
    produto_cod = f"P{run_id[:6]}"

    with integration_db_cursor() as (_, cur):
        _seed_admin(cur, admin_login)
        conta_id = _seed_sales_minimum(
            cur,
            filial=filial,
            admin_login=admin_login,
            cliente_cod=cliente_cod,
            produto_cod=produto_cod,
        )

        pedido = criar_pedido_tx(cur, usuario=admin_login, filial=filial, valor_total=0.0, status="ABERTO")
        pedido_id = int(pedido["pedido_id"])
        adicionar_item_tx(
            cur,
            usuario=admin_login,
            pedido_id=pedido_id,
            filial=filial,
            produto=produto_cod,
            qtd=2,
            total=100.0,
            preco_unit=50.0,
        )
        fat = faturar_pedido_venda_tx(
            cur,
            usuario=admin_login,
            pedido_id=pedido_id,
            filial=filial,
            cliente_cod=cliente_cod,
            venc_dias=30,
            tes_cod="001",
        )
        titulo_id = int(listar_ar_tx(cur, filial=filial, status="ABERTO")[0]["ID"])
        receber_ar_uc_tx(cur, usuario=admin_login, titulo_id=titulo_id, conta_id=conta_id)

        cur.execute(
            """
            INSERT INTO dbo.SD3_MOV
              (D3_DATA, D3_FILIAL, D3_PRODUTO, D3_TIPO, D3_QTD, D3_CUSTO_UNIT, D3_VALOR, D3_ORIGEM, D3_REF, D3_USUARIO)
            VALUES (SYSDATETIME(), ?, ?, 'S', ?, ?, ?, 'RESERVA_FATURADA', ?, ?)
            """,
            (filial, produto_cod, 2, 20.0, 40.0, str(fat["nf_id"]), admin_login),
        )

        dre = dre_simples_tx(cur, filial=filial, de=None, ate=None)
        assert dre["receita"] == 100.0
        assert dre["cmv"] == 40.0
        assert dre["margem_bruta"] == 60.0

        margem = margem_por_produto_tx(cur, filial=filial, de=None, ate=None)
        assert len(margem) == 1
        assert margem[0]["produto"] == produto_cod
        assert margem[0]["receita"] == 100.0
        assert margem[0]["cmv"] == 40.0

        conciliacao = conciliacao_nf_financeiro_tx(cur, filial=filial, de=None, ate=None, tolerancia=0.01, limit=50)
        assert conciliacao["nf_sem_ar"] == []
        assert conciliacao["ar_sem_nf"] == []
        assert conciliacao["valor_divergente"] == []
        assert conciliacao["nf_cancelada_ar"] == []

        cur.execute(
            """
            UPDATE dbo.SF2_NOTAS
            SET F2_STATUS='CANCELADA'
            WHERE ID=?
            """,
            (int(fat["nf_id"]),),
        )
        consistencia = consistencia_fiscal_tx(cur, filial=filial, de=None, ate=None, limit=50)
        assert len(consistencia["nf_cancelada_sd2"]) >= 1

        fechar_periodo_uc_tx(cur, usuario=admin_login, filial=filial, ano=2099, mes=1)
        assert fechamento_periodo_aberto_tx(cur, filial=filial, data_ref=date(2099, 1, 1)) is False
        abrir_periodo_uc_tx(cur, usuario=admin_login, filial=filial, ano=2099, mes=1)
        assert fechamento_periodo_aberto_tx(cur, filial=filial, data_ref=date(2099, 1, 1)) is True


def test_faturar_pedido_em_periodo_fechado_db():
    run_id = uuid4().hex[:8].upper()
    filial = f"F{run_id[:1]}"
    admin_login = f"admin_it_{run_id}"
    cliente_cod = f"C{run_id[:6]}"
    produto_cod = f"P{run_id[:6]}"
    hoje = date.today()

    with integration_db_cursor() as (_, cur):
        _seed_admin(cur, admin_login)
        _seed_sales_minimum(
            cur,
            filial=filial,
            admin_login=admin_login,
            cliente_cod=cliente_cod,
            produto_cod=produto_cod,
        )

        pedido = criar_pedido_tx(cur, usuario=admin_login, filial=filial, valor_total=0.0, status="ABERTO")
        pedido_id = int(pedido["pedido_id"])
        adicionar_item_tx(
            cur,
            usuario=admin_login,
            pedido_id=pedido_id,
            filial=filial,
            produto=produto_cod,
            qtd=2,
            total=100.0,
            preco_unit=50.0,
        )

        fechar_periodo_uc_tx(cur, usuario=admin_login, filial=filial, ano=hoje.year, mes=hoje.month)

        with pytest.raises(BusinessError, match="Per"):
            faturar_pedido_venda_tx(
                cur,
                usuario=admin_login,
                pedido_id=pedido_id,
                filial=filial,
                cliente_cod=cliente_cod,
                venc_dias=30,
                tes_cod="001",
            )


def test_pagar_ap_ja_baixado_nao_duplica_caixa_db():
    run_id = uuid4().hex[:8].upper()
    filial = f"A{run_id[:1]}"
    admin_login = f"admin_it_{run_id}"
    forn_cod = f"F{run_id[:6]}"

    with integration_db_cursor() as (_, cur):
        _seed_admin(cur, admin_login)
        sm0_criar_tx(cur, filial=filial, serie_nf="1", serie_ar="1", serie_ap="1")
        seed_series_basicas_tx(cur, filial=filial)
        _seed_fornecedor(cur, filial=filial, forn_cod=forn_cod)
        conta_id = _seed_caixa(cur, filial=filial, nome=f"CAIXA AP DUP {admin_login}")

        lancar_ap_uc_tx(
            cur,
            usuario=admin_login,
            filial=filial,
            forn_cod=forn_cod,
            valor=80.0,
            ref="MANUAL-DUP",
            venc_dias=15,
        )
        titulo_id = int(listar_ap_uc_tx(cur, usuario=admin_login, filial=filial, status="ABERTO")[0]["ID"])

        primeiro = pagar_ap_uc_tx(cur, usuario=admin_login, titulo_id=titulo_id, conta_id=conta_id)
        assert primeiro["status"] == "BAIXADO"

        with pytest.raises(BusinessError, match="T.tulo AP n.o est. em aberto"):
            pagar_ap_uc_tx(cur, usuario=admin_login, titulo_id=titulo_id, conta_id=conta_id)

        saldo = saldo_caixa_uc_tx(cur, filial=filial, conta_id=conta_id, ate=None)
        assert saldo["saldo"] == -80.0


def test_confirmar_reserva_sem_saldo_efetivo_db():
    run_id = uuid4().hex[:8].upper()
    filial = f"S{run_id[:1]}"
    admin_login = f"admin_it_{run_id}"
    cliente_cod = f"C{run_id[:6]}"
    produto_cod = f"P{run_id[:6]}"

    with integration_db_cursor() as (_, cur):
        _seed_admin(cur, admin_login)
        _seed_sales_minimum(
            cur,
            filial=filial,
            admin_login=admin_login,
            cliente_cod=cliente_cod,
            produto_cod=produto_cod,
        )
        _seed_price_table(cur, filial=filial, produto_cod=produto_cod, preco=60.0)

        reserva = criar_reserva_tx(
            cur,
            usuario=admin_login,
            produto=produto_cod,
            qtd=2,
            filial=filial,
            cliente_cod=cliente_cod,
            tabela_cod="0001",
        )
        reserva_id = int(reserva["reserva_id"])

        cur.execute(
            """
            UPDATE dbo.SB1_PRODUTOS
            SET B1_ESTOQUE = 1
            WHERE B1_COD=? AND B1_FILIAL=?
            """,
            (produto_cod, filial),
        )

        with pytest.raises(BusinessError, match="Estoque/reservado insuficiente para confirmar"):
            confirmar_reserva_tx(
                cur,
                usuario=admin_login,
                reserva_id=reserva_id,
                cliente_cod=cliente_cod,
                venc_dias=30,
                tes_cod="001",
            )


def test_conciliacao_detecta_divergencia_nf_financeiro_db():
    run_id = uuid4().hex[:8].upper()
    filial = f"C{run_id[:1]}"
    admin_login = f"admin_it_{run_id}"
    cliente_cod = f"C{run_id[:6]}"
    produto_cod = f"P{run_id[:6]}"

    with integration_db_cursor() as (_, cur):
        _seed_admin(cur, admin_login)
        _seed_sales_minimum(
            cur,
            filial=filial,
            admin_login=admin_login,
            cliente_cod=cliente_cod,
            produto_cod=produto_cod,
        )

        pedido = criar_pedido_tx(cur, usuario=admin_login, filial=filial, valor_total=0.0, status="ABERTO")
        pedido_id = int(pedido["pedido_id"])
        adicionar_item_tx(
            cur,
            usuario=admin_login,
            pedido_id=pedido_id,
            filial=filial,
            produto=produto_cod,
            qtd=2,
            total=100.0,
            preco_unit=50.0,
        )
        fat = faturar_pedido_venda_tx(
            cur,
            usuario=admin_login,
            pedido_id=pedido_id,
            filial=filial,
            cliente_cod=cliente_cod,
            venc_dias=30,
            tes_cod="001",
        )

        titulo_id = int(listar_ar_tx(cur, filial=filial, status="ABERTO")[0]["ID"])
        cur.execute(
            """
            UPDATE dbo.SE1_AR
            SET E1_VALOR = 130.0
            WHERE ID = ?
            """,
            (titulo_id,),
        )

        conciliacao = conciliacao_nf_financeiro_tx(cur, filial=filial, de=None, ate=None, tolerancia=0.01, limit=50)
        assert conciliacao["nf_sem_ar"] == []
        assert conciliacao["ar_sem_nf"] == []
        assert len(conciliacao["valor_divergente"]) >= 1
        assert any(int(row["nf_id"]) == int(fat["nf_id"]) for row in conciliacao["valor_divergente"])
