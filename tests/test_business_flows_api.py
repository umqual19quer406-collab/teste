from contextlib import contextmanager

from fastapi.testclient import TestClient

from app.api.deps import get_current_user
from app.api.routers import ap_lancamento as ap_router
from app.api.routers import financeiro as financeiro_router
from app.api.routers import reservas as reservas_router
from app.api.routers import vendas as vendas_router
from app.core.exceptions import BusinessError
from app.main import app


@contextmanager
def fake_db_transaction():
    yield None, object()


def _install_admin_override():
    app.dependency_overrides[get_current_user] = lambda: {"login": "admin", "perfil": "admin"}


def _clear_overrides():
    app.dependency_overrides.clear()


def _wire_fake_business_flow(monkeypatch):
    state = {
        "pedido_seq": 100,
        "item_seq": 1000,
        "nf_seq": 500,
        "ar_seq": 800,
        "ap_seq": 900,
        "reserva_seq": 300,
        "pedidos": {},
        "itens": {},
        "ar": {},
        "ap": {},
        "reservas": {},
        "caixa_saldo": {1: 0.0},
    }

    def patch_tx(module, name, fn):
        monkeypatch.setattr(module, "db_transaction", fake_db_transaction)
        monkeypatch.setattr(module, name, fn)

    def criar_pedido(_cur, usuario, filial, valor_total, status, icms=None, ipi=None, total_bruto=None):
        state["pedido_seq"] += 1
        pedido_id = state["pedido_seq"]
        pedido = {
            "pedido_id": pedido_id,
            "filial": filial,
            "valor_total": valor_total,
            "status": status,
            "usuario": usuario,
            "icms": icms,
            "ipi": ipi,
            "total_bruto": total_bruto,
            "itens": [],
        }
        state["pedidos"][pedido_id] = pedido
        return pedido

    def adicionar_item(_cur, usuario, pedido_id, filial, produto, qtd, total, preco_unit=None):
        state["item_seq"] += 1
        item_id = state["item_seq"]
        item = {
            "item_id": item_id,
            "pedido_id": pedido_id,
            "filial": filial,
            "produto": produto,
            "qtd": qtd,
            "total": total,
            "preco_unit": preco_unit,
            "usuario": usuario,
        }
        state["itens"][item_id] = item
        state["pedidos"][pedido_id]["itens"].append(item)
        return item

    def faturar_pedido(_cur, usuario, pedido_id, filial, cliente_cod, venc_dias, tes_cod):
        state["nf_seq"] += 1
        state["ar_seq"] += 1
        pedido = state["pedidos"][pedido_id]
        pedido["status"] = "FATURADO"
        pedido["nf_id"] = state["nf_seq"]

        titulo_id = state["ar_seq"]
        titulo = {
            "ID": titulo_id,
            "E1_FILIAL": filial,
            "E1_CLIENTE": cliente_cod or "CLIENTE",
            "E1_VALOR": pedido["valor_total"],
            "E1_STATUS": "ABERTO",
            "E1_REF": f"NF-{pedido['nf_id']}",
            "pedido_id": pedido_id,
            "usuario": usuario,
            "tes_cod": tes_cod,
            "venc_dias": venc_dias,
        }
        state["ar"][titulo_id] = titulo
        return {"pedido_id": pedido_id, "nf_id": pedido["nf_id"], "ar_titulo_id": titulo_id, "status": "FATURADO"}

    def listar_ar(_cur, filial, status):
        return [
            titulo
            for titulo in state["ar"].values()
            if titulo["E1_FILIAL"] == filial and titulo["E1_STATUS"] == status
        ]

    def receber_ar(_cur, usuario, titulo_id, conta_id):
        titulo = state["ar"][titulo_id]
        titulo["E1_STATUS"] = "BAIXADO"
        titulo["recebido_por"] = usuario
        titulo["conta_id"] = conta_id
        state["caixa_saldo"][conta_id] = state["caixa_saldo"].get(conta_id, 0.0) + float(titulo["E1_VALOR"])
        return {"titulo_id": titulo_id, "status": "BAIXADO", "conta_id": conta_id}

    def saldo_caixa(_cur, filial, conta_id, ate=None):
        return {"filial": filial, "conta_id": conta_id, "saldo": state["caixa_saldo"].get(conta_id, 0.0), "ate": ate}

    def lancar_ap(_cur, usuario, filial, forn_cod, valor, ref, venc_dias):
        state["ap_seq"] += 1
        titulo_id = state["ap_seq"]
        titulo = {
            "ID": titulo_id,
            "F1_FILIAL": filial,
            "F1_FORN": forn_cod,
            "F1_VALOR": valor,
            "F1_STATUS": "ABERTO",
            "F1_REF": ref,
            "venc_dias": venc_dias,
            "usuario": usuario,
        }
        state["ap"][titulo_id] = titulo
        return {"titulo_id": titulo_id, "status": "ABERTO", "forn_cod": forn_cod}

    def listar_ap(_cur, usuario, filial, status):
        return [
            titulo
            for titulo in state["ap"].values()
            if titulo["F1_FILIAL"] == filial and titulo["F1_STATUS"] == status
        ]

    def pagar_ap(_cur, usuario, titulo_id, conta_id):
        titulo = state["ap"][titulo_id]
        titulo["F1_STATUS"] = "BAIXADO"
        titulo["pago_por"] = usuario
        titulo["conta_id"] = conta_id
        state["caixa_saldo"][conta_id] = state["caixa_saldo"].get(conta_id, 0.0) - float(titulo["F1_VALOR"])
        return {"titulo_id": titulo_id, "status": "BAIXADO", "conta_id": conta_id}

    def criar_reserva(_cur, usuario, produto, qtd, filial, cliente_cod, tabela_cod):
        state["reserva_seq"] += 1
        reserva_id = state["reserva_seq"]
        reserva = {
            "reserva_id": reserva_id,
            "produto": produto,
            "qtd": qtd,
            "filial": filial,
            "cliente_cod": cliente_cod,
            "tabela_cod": tabela_cod,
            "status": "ABERTA",
            "usuario": usuario,
        }
        state["reservas"][reserva_id] = reserva
        return reserva

    def confirmar_reserva(_cur, usuario, reserva_id, cliente_cod, venc_dias, tes_cod):
        reserva = state["reservas"][reserva_id]
        reserva["status"] = "CONFIRMADA"
        reserva["confirmada_por"] = usuario
        reserva["cliente_cod"] = cliente_cod or reserva["cliente_cod"]
        reserva["venc_dias"] = venc_dias
        reserva["tes_cod"] = tes_cod
        return reserva

    def cancelar_reserva(_cur, usuario, reserva_id):
        reserva = state["reservas"][reserva_id]
        reserva["status"] = "CANCELADA"
        reserva["cancelada_por"] = usuario
        return reserva

    patch_tx(vendas_router, "criar_pedido_tx", criar_pedido)
    patch_tx(vendas_router, "adicionar_item_tx", adicionar_item)
    patch_tx(vendas_router, "faturar_pedido_venda_tx", faturar_pedido)
    patch_tx(financeiro_router, "listar_ar_uc_tx", listar_ar)
    patch_tx(financeiro_router, "receber_ar_uc_tx", receber_ar)
    patch_tx(financeiro_router, "saldo_caixa_uc_tx", saldo_caixa)
    patch_tx(financeiro_router, "listar_ap_uc_tx", listar_ap)
    patch_tx(financeiro_router, "pagar_ap_uc_tx", pagar_ap)
    patch_tx(ap_router, "lancar_ap_uc_tx", lancar_ap)
    patch_tx(reservas_router, "criar_reserva_tx", criar_reserva)
    patch_tx(reservas_router, "confirmar_reserva_tx", confirmar_reserva)
    patch_tx(reservas_router, "cancelar_reserva_tx", cancelar_reserva)

    return state


def test_fluxo_vendas_financeiro_e_caixa(monkeypatch):
    state = _wire_fake_business_flow(monkeypatch)
    _install_admin_override()
    try:
        client = TestClient(app)

        pedido_resp = client.post(
            "/vendas/pedidos",
            json={"filial": "01", "valor_total": 150.0, "status": "ABERTO"},
        )
        assert pedido_resp.status_code == 200
        pedido_id = pedido_resp.json()["pedido_id"]

        item_resp = client.post(
            f"/vendas/pedidos/{pedido_id}/itens",
            json={"filial": "01", "produto": "PROD001", "qtd": 3, "total": 150.0, "preco_unit": 50.0},
        )
        assert item_resp.status_code == 200
        assert item_resp.json()["pedido_id"] == pedido_id

        faturar_resp = client.post(
            f"/vendas/pedidos/{pedido_id}/faturar",
            json={"filial": "01", "cliente_cod": "C0001", "venc_dias": 30, "tes_cod": "001"},
        )
        assert faturar_resp.status_code == 200
        ar_titulo_id = faturar_resp.json()["ar_titulo_id"]
        assert state["pedidos"][pedido_id]["status"] == "FATURADO"

        listar_ar_resp = client.get("/financeiro/ar", params={"filial": "01", "status": "ABERTO"})
        assert listar_ar_resp.status_code == 200
        ar_payload = listar_ar_resp.json()
        assert len(ar_payload) == 1
        assert ar_payload[0]["ID"] == ar_titulo_id
        assert ar_payload[0]["E1_VALOR"] == 150.0

        receber_resp = client.post("/financeiro/ar/receber", json={"titulo_id": ar_titulo_id, "conta_id": 1})
        assert receber_resp.status_code == 200
        assert state["ar"][ar_titulo_id]["E1_STATUS"] == "BAIXADO"

        saldo_resp = client.get("/financeiro/caixa/saldo", params={"filial": "01", "conta_id": 1})
        assert saldo_resp.status_code == 200
        assert saldo_resp.json()["saldo"] == 150.0
    finally:
        _clear_overrides()


def test_fluxo_ap_e_reservas(monkeypatch):
    state = _wire_fake_business_flow(monkeypatch)
    _install_admin_override()
    try:
        client = TestClient(app)

        ap_resp = client.post(
            "/ap/lancar",
            json={"forn_cod": "F0001", "valor": 80.0, "ref": "MANUAL-1", "venc_dias": 15, "filial": "01"},
        )
        assert ap_resp.status_code == 200
        ap_titulo_id = ap_resp.json()["titulo_id"]

        listar_ap_resp = client.get("/financeiro/ap", params={"filial": "01", "status": "ABERTO"})
        assert listar_ap_resp.status_code == 200
        ap_payload = listar_ap_resp.json()
        assert len(ap_payload) == 1
        assert ap_payload[0]["ID"] == ap_titulo_id
        assert ap_payload[0]["F1_VALOR"] == 80.0

        pagar_resp = client.post("/financeiro/ap/pagar", json={"titulo_id": ap_titulo_id, "conta_id": 1})
        assert pagar_resp.status_code == 200
        assert state["ap"][ap_titulo_id]["F1_STATUS"] == "BAIXADO"

        saldo_resp = client.get("/financeiro/caixa/saldo", params={"filial": "01", "conta_id": 1})
        assert saldo_resp.status_code == 200
        assert saldo_resp.json()["saldo"] == -80.0

        criar_reserva_resp = client.post(
            "/reserva",
            json={"cod": "PROD002", "qtd": 2, "filial": "01", "cliente_cod": "C0002", "tabela_cod": "0001"},
        )
        assert criar_reserva_resp.status_code == 200
        reserva_id = criar_reserva_resp.json()["reserva_id"]
        assert state["reservas"][reserva_id]["status"] == "ABERTA"

        confirmar_resp = client.post(
            "/reserva/confirmar",
            json={"reserva_id": reserva_id, "cliente_cod": "C0002", "venc_dias": 20, "tes_cod": "001"},
        )
        assert confirmar_resp.status_code == 200
        assert state["reservas"][reserva_id]["status"] == "CONFIRMADA"

        cancelar_resp = client.post("/reserva/cancelar", json={"reserva_id": reserva_id})
        assert cancelar_resp.status_code == 200
        assert state["reservas"][reserva_id]["status"] == "CANCELADA"
    finally:
        _clear_overrides()


def test_faturar_pedido_sem_itens_retorna_erro_de_negocio(monkeypatch):
    state = _wire_fake_business_flow(monkeypatch)

    def faturar_sem_itens(_cur, usuario, pedido_id, filial, cliente_cod, venc_dias, tes_cod):
        pedido = state["pedidos"][pedido_id]
        if not pedido["itens"]:
            raise BusinessError("Pedido sem itens")
        return {"pedido_id": pedido_id}

    monkeypatch.setattr(vendas_router, "faturar_pedido_venda_tx", faturar_sem_itens)
    _install_admin_override()
    try:
        client = TestClient(app, raise_server_exceptions=False)
        pedido_resp = client.post(
            "/vendas/pedidos",
            json={"filial": "01", "valor_total": 150.0, "status": "ABERTO"},
        )
        pedido_id = pedido_resp.json()["pedido_id"]
        response = client.post(
            f"/vendas/pedidos/{pedido_id}/faturar",
            json={"filial": "01", "cliente_cod": "C0001", "venc_dias": 30, "tes_cod": "001"},
        )
    finally:
        _clear_overrides()

    assert response.status_code == 400
    assert response.json()["detail"] == "Pedido sem itens"


def test_receber_ar_ja_baixado_nao_duplica_caixa(monkeypatch):
    state = _wire_fake_business_flow(monkeypatch)

    def receber_ar_unico(_cur, usuario, titulo_id, conta_id):
        titulo = state["ar"][titulo_id]
        if titulo["E1_STATUS"] != "ABERTO":
            raise BusinessError("Titulo AR nao esta em aberto")
        titulo["E1_STATUS"] = "BAIXADO"
        state["caixa_saldo"][conta_id] = state["caixa_saldo"].get(conta_id, 0.0) + float(titulo["E1_VALOR"])
        return {"titulo_id": titulo_id, "status": "BAIXADO", "conta_id": conta_id}

    monkeypatch.setattr(financeiro_router, "receber_ar_uc_tx", receber_ar_unico)
    _install_admin_override()
    try:
        client = TestClient(app, raise_server_exceptions=False)
        pedido_resp = client.post("/vendas/pedidos", json={"filial": "01", "valor_total": 100.0, "status": "ABERTO"})
        pedido_id = pedido_resp.json()["pedido_id"]
        client.post(
            f"/vendas/pedidos/{pedido_id}/itens",
            json={"filial": "01", "produto": "PROD001", "qtd": 2, "total": 100.0, "preco_unit": 50.0},
        )
        faturar_resp = client.post(
            f"/vendas/pedidos/{pedido_id}/faturar",
            json={"filial": "01", "cliente_cod": "C0001", "venc_dias": 30, "tes_cod": "001"},
        )
        titulo_id = faturar_resp.json()["ar_titulo_id"]
        first = client.post("/financeiro/ar/receber", json={"titulo_id": titulo_id, "conta_id": 1})
        second = client.post("/financeiro/ar/receber", json={"titulo_id": titulo_id, "conta_id": 1})
    finally:
        _clear_overrides()

    assert first.status_code == 200
    assert second.status_code == 400
    assert second.json()["detail"] == "Titulo AR nao esta em aberto"
    assert state["caixa_saldo"][1] == 100.0
