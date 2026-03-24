from app.core.exceptions import BusinessError
from app.use_cases import reservas_uc


def test_criar_reserva_faz_fallback_para_preco_do_produto(monkeypatch):
    monkeypatch.setattr(reservas_uc, "exigir_perfil_tx", lambda *_: None)
    monkeypatch.setattr(
        reservas_uc,
        "sb1_get_tx",
        lambda *_: {
            "B1_COD": "CEL124",
            "B1_PRECO": 11325.45,
            "B1_ESTOQUE": 5,
            "B1_RESERVADO": 0,
            "B1_FILIAL": "01",
        },
    )
    monkeypatch.setattr(reservas_uc, "_tabela_padrao_id_tx", lambda *_args, **_kwargs: 1)
    monkeypatch.setattr(
        reservas_uc,
        "buscar_preco_vigente_tx",
        lambda *_args, **_kwargs: (_ for _ in ()).throw(BusinessError("Preco nao encontrado")),
    )
    monkeypatch.setattr(reservas_uc, "sb1_reservar_atomico_tx", lambda *_: None)
    monkeypatch.setattr(reservas_uc, "reserva_criar_tx", lambda *_args, **_kwargs: 123)
    monkeypatch.setattr(reservas_uc, "log_tx", lambda *_: None)
    monkeypatch.setattr(
        reservas_uc,
        "saldo_sd3_tx",
        lambda *_: 5,
    )

    payload = reservas_uc.criar_reserva_tx(
        object(),
        usuario="admin",
        produto="CEL124",
        qtd=1,
        filial="01",
        cliente_cod="CLI001",
        tabela_cod="0001",
    )

    assert payload["reserva_id"] == 123
    assert payload["preco_unit"] == 11325.45
    assert payload["total"] == 11325.45
    assert payload["preco_source"] == "PRODUTO"


def test_criar_reserva_sem_preco_em_tabela_nem_produto_continua_bloqueando(monkeypatch):
    monkeypatch.setattr(reservas_uc, "exigir_perfil_tx", lambda *_: None)
    monkeypatch.setattr(
        reservas_uc,
        "sb1_get_tx",
        lambda *_: {
            "B1_COD": "CEL124",
            "B1_PRECO": 0.0,
            "B1_ESTOQUE": 5,
            "B1_RESERVADO": 0,
            "B1_FILIAL": "01",
        },
    )
    monkeypatch.setattr(reservas_uc, "_tabela_padrao_id_tx", lambda *_args, **_kwargs: 1)
    monkeypatch.setattr(
        reservas_uc,
        "buscar_preco_vigente_tx",
        lambda *_args, **_kwargs: (_ for _ in ()).throw(BusinessError("Preco nao encontrado")),
    )

    try:
        reservas_uc.criar_reserva_tx(
            object(),
            usuario="admin",
            produto="CEL124",
            qtd=1,
            filial="01",
            cliente_cod="CLI001",
            tabela_cod="0001",
        )
        assert False, "Era esperado BusinessError quando nao ha preco disponivel"
    except BusinessError as exc:
        assert str(exc) == "Preco nao encontrado"
