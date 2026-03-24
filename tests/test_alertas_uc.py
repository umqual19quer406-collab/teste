from app.use_cases import alertas_uc


def test_alertas_admin_prioriza_setup_periodo_e_financeiro(monkeypatch):
    monkeypatch.setattr(alertas_uc, "contar_ar_aberto_tx", lambda *_: 5)
    monkeypatch.setattr(alertas_uc, "contar_ar_vencido_tx", lambda *_: 2)
    monkeypatch.setattr(alertas_uc, "contar_ar_vence_hoje_tx", lambda *_: 1)
    monkeypatch.setattr(alertas_uc, "contar_ar_vencendo_ate_tx", lambda *_: 3)
    monkeypatch.setattr(alertas_uc, "contar_ap_aberto_tx", lambda *_: 4)
    monkeypatch.setattr(alertas_uc, "contar_ap_vencido_tx", lambda *_: 1)
    monkeypatch.setattr(alertas_uc, "contar_ap_vence_hoje_tx", lambda *_: 0)
    monkeypatch.setattr(alertas_uc, "contar_ap_vencendo_ate_tx", lambda *_: 2)
    monkeypatch.setattr(alertas_uc, "contar_reservas_abertas_tx", lambda *_: 1)
    monkeypatch.setattr(alertas_uc, "contar_pedidos_abertos_sem_itens_tx", lambda *_: 2)
    monkeypatch.setattr(alertas_uc, "contar_pedidos_abertos_com_itens_tx", lambda *_: 3)
    monkeypatch.setattr(alertas_uc, "contar_contas_caixa_ativas_tx", lambda *_: 1)
    monkeypatch.setattr(alertas_uc, "fechamento_periodo_aberto_tx", lambda *_: False)
    monkeypatch.setattr(
        alertas_uc,
        "app_setup_status_tx",
        lambda *_: {"setup_completed": False, "completed_at": None, "completed_by": None},
    )

    payload = alertas_uc.listar_alertas_uc_tx(object(), login="admin", perfil="admin", filial="01")

    assert payload["summary"]["critical"] == 2
    assert payload["summary"]["warning"] >= 1
    assert payload["items"][0]["code"] == "AR_OVERDUE"
    assert payload["items"][0]["action_label"] == "Abrir recebiveis"
    assert payload["items"][0]["business_context"] == "financeiro.ar.overdue"
    assert payload["items"][1]["code"] == "AP_OVERDUE"
    warning_codes = [item["code"] for item in payload["items"] if item["severity"] == "warning"]
    assert "SETUP_PENDING" in warning_codes
    assert "PERIODO_FECHADO" in warning_codes


def test_alertas_operador_destaca_pedidos_e_reservas(monkeypatch):
    monkeypatch.setattr(alertas_uc, "contar_ar_aberto_tx", lambda *_: 0)
    monkeypatch.setattr(alertas_uc, "contar_ar_vencido_tx", lambda *_: 0)
    monkeypatch.setattr(alertas_uc, "contar_ar_vence_hoje_tx", lambda *_: 0)
    monkeypatch.setattr(alertas_uc, "contar_ar_vencendo_ate_tx", lambda *_: 0)
    monkeypatch.setattr(alertas_uc, "contar_ap_aberto_tx", lambda *_: 0)
    monkeypatch.setattr(alertas_uc, "contar_ap_vencido_tx", lambda *_: 0)
    monkeypatch.setattr(alertas_uc, "contar_ap_vence_hoje_tx", lambda *_: 0)
    monkeypatch.setattr(alertas_uc, "contar_ap_vencendo_ate_tx", lambda *_: 0)
    monkeypatch.setattr(alertas_uc, "contar_reservas_abertas_tx", lambda *_: 4)
    monkeypatch.setattr(alertas_uc, "contar_pedidos_abertos_sem_itens_tx", lambda *_: 2)
    monkeypatch.setattr(alertas_uc, "contar_pedidos_abertos_com_itens_tx", lambda *_: 3)
    monkeypatch.setattr(alertas_uc, "contar_contas_caixa_ativas_tx", lambda *_: 1)
    monkeypatch.setattr(alertas_uc, "fechamento_periodo_aberto_tx", lambda *_: True)
    monkeypatch.setattr(
        alertas_uc,
        "app_setup_status_tx",
        lambda *_: {"setup_completed": True, "completed_at": "2026-03-23T19:00:00", "completed_by": "admin"},
    )

    payload = alertas_uc.listar_alertas_uc_tx(object(), login="operador", perfil="operador", filial="01")

    codes = [item["code"] for item in payload["items"]]
    assert "PEDIDOS_NO_ITEMS" in codes
    assert "PEDIDOS_OPEN" in codes
    assert "RESERVAS_OPEN" in codes
    pedidos_sem_itens = next(item for item in payload["items"] if item["code"] == "PEDIDOS_NO_ITEMS")
    assert pedidos_sem_itens["action_label"] == "Revisar pedidos"
    assert pedidos_sem_itens["business_context"] == "vendas.pedidos.sem_itens"
    assert "OPERACAO_ESTAVEL" not in codes
