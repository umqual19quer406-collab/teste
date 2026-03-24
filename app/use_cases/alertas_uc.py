from __future__ import annotations

from datetime import date, datetime

from app.infra.repositories.alertas_repo import (
    contar_ap_aberto_tx,
    contar_ap_vence_hoje_tx,
    contar_ap_vencendo_ate_tx,
    contar_ap_vencido_tx,
    contar_ar_aberto_tx,
    contar_ar_vence_hoje_tx,
    contar_ar_vencendo_ate_tx,
    contar_ar_vencido_tx,
    contar_contas_caixa_ativas_tx,
    contar_pedidos_abertos_com_itens_tx,
    contar_pedidos_abertos_sem_itens_tx,
    contar_reservas_abertas_tx,
)
from app.infra.repositories.app_setup_repo import app_setup_status_tx
from app.infra.repositories.fechamento_repo import fechamento_periodo_aberto_tx


def _append_alert(
    items: list[dict],
    *,
    code: str,
    severity: str,
    title: str,
    text: str,
    route: str | None = None,
    count: int | None = None,
    action_label: str | None = None,
    business_context: str | None = None,
) -> None:
    items.append(
        {
            "code": code,
            "severity": severity,
            "title": title,
            "text": text,
            "route": route,
            "count": count,
            "action_label": action_label,
            "business_context": business_context,
        }
    )


def listar_alertas_uc_tx(cur, login: str, perfil: str, filial: str) -> dict:
    hoje = date.today()
    horizonte = date.fromordinal(hoje.toordinal() + 3)
    items: list[dict] = []

    ar_aberto = contar_ar_aberto_tx(cur, filial)
    ar_vencido = contar_ar_vencido_tx(cur, filial, hoje)
    ar_vence_hoje = contar_ar_vence_hoje_tx(cur, filial, hoje)
    ar_vencendo = contar_ar_vencendo_ate_tx(cur, filial, date.fromordinal(hoje.toordinal() + 1), horizonte)
    ap_aberto = contar_ap_aberto_tx(cur, filial)
    ap_vencido = contar_ap_vencido_tx(cur, filial, hoje)
    ap_vence_hoje = contar_ap_vence_hoje_tx(cur, filial, hoje)
    ap_vencendo = contar_ap_vencendo_ate_tx(cur, filial, date.fromordinal(hoje.toordinal() + 1), horizonte)
    reservas_abertas = contar_reservas_abertas_tx(cur, filial)
    pedidos_abertos_sem_itens = contar_pedidos_abertos_sem_itens_tx(cur, filial)
    pedidos_abertos_com_itens = contar_pedidos_abertos_com_itens_tx(cur, filial)
    contas_ativas = contar_contas_caixa_ativas_tx(cur, filial)
    periodo_aberto = fechamento_periodo_aberto_tx(cur, filial, hoje)

    if ar_vencido > 0:
        _append_alert(
            items,
            code="AR_OVERDUE",
            severity="critical",
            title="Recebiveis vencidos",
            text=f"{ar_vencido} titulo(s) de contas a receber estao vencidos e seguem em aberto na filial {filial}.",
            route="/financeiro/ar",
            count=ar_vencido,
            action_label="Abrir recebiveis",
            business_context="financeiro.ar.overdue",
        )

    if ap_vencido > 0:
        _append_alert(
            items,
            code="AP_OVERDUE",
            severity="critical",
            title="Pagamentos vencidos",
            text=f"{ap_vencido} titulo(s) de contas a pagar estao vencidos e seguem em aberto na filial {filial}.",
            route="/financeiro/ap",
            count=ap_vencido,
            action_label="Abrir pagamentos",
            business_context="financeiro.ap.overdue",
        )

    if perfil in {"admin", "operador"} and pedidos_abertos_sem_itens > 0:
        _append_alert(
            items,
            code="PEDIDOS_NO_ITEMS",
            severity="warning",
            title="Pedidos abertos sem itens",
            text=f"{pedidos_abertos_sem_itens} pedido(s) seguem abertos sem item lancado.",
            route="/vendas/pedidos",
            count=pedidos_abertos_sem_itens,
            action_label="Revisar pedidos",
            business_context="vendas.pedidos.sem_itens",
        )

    if perfil in {"admin", "operador"} and pedidos_abertos_com_itens > 0:
        _append_alert(
            items,
            code="PEDIDOS_OPEN",
            severity="info",
            title="Pedidos aguardando faturamento",
            text=f"{pedidos_abertos_com_itens} pedido(s) abertos possuem itens e ainda aguardam faturamento.",
            route="/vendas/pedidos",
            count=pedidos_abertos_com_itens,
            action_label="Ir para faturamento",
            business_context="vendas.pedidos.abertos",
        )

    if reservas_abertas > 0:
        _append_alert(
            items,
            code="RESERVAS_OPEN",
            severity="warning",
            title="Reservas pendentes",
            text=f"{reservas_abertas} reserva(s) ainda estao abertas aguardando confirmacao ou cancelamento.",
            route="/reservas",
            count=reservas_abertas,
            action_label="Abrir reservas",
            business_context="vendas.reservas.abertas",
        )

    if ar_vence_hoje > 0:
        _append_alert(
            items,
            code="AR_DUE_TODAY",
            severity="warning",
            title="Recebiveis vencem hoje",
            text=f"{ar_vence_hoje} titulo(s) de AR vencem hoje na filial {filial}.",
            route="/financeiro/ar",
            count=ar_vence_hoje,
            action_label="Priorizar recebimento",
            business_context="financeiro.ar.due_today",
        )

    if ap_vence_hoje > 0:
        _append_alert(
            items,
            code="AP_DUE_TODAY",
            severity="warning",
            title="Pagamentos vencem hoje",
            text=f"{ap_vence_hoje} titulo(s) de AP vencem hoje na filial {filial}.",
            route="/financeiro/ap",
            count=ap_vence_hoje,
            action_label="Priorizar pagamento",
            business_context="financeiro.ap.due_today",
        )

    if ar_vencendo > 0:
        _append_alert(
            items,
            code="AR_DUE_SOON",
            severity="info",
            title="Recebiveis a vencer",
            text=f"{ar_vencendo} titulo(s) de AR vencem nos proximos 3 dias.",
            route="/financeiro/ar",
            count=ar_vencendo,
            action_label="Planejar cobranca",
            business_context="financeiro.ar.due_soon",
        )

    if ap_vencendo > 0:
        _append_alert(
            items,
            code="AP_DUE_SOON",
            severity="info",
            title="Pagamentos a vencer",
            text=f"{ap_vencendo} titulo(s) de AP vencem nos proximos 3 dias.",
            route="/financeiro/ap",
            count=ap_vencendo,
            action_label="Planejar pagamento",
            business_context="financeiro.ap.due_soon",
        )

    if not periodo_aberto:
        _append_alert(
            items,
            code="PERIODO_FECHADO",
            severity="warning",
            title="Periodo fechado",
            text=f"O periodo corrente da filial {filial} esta fechado para lancamentos operacionais.",
            route="/dashboard",
            action_label="Revisar fechamento",
            business_context="parametros.fechamento.closed",
        )

    if contas_ativas == 0:
        _append_alert(
            items,
            code="CAIXA_SEM_CONTA",
            severity="warning",
            title="Caixa sem conta ativa",
            text=f"Nao existe conta de caixa ativa cadastrada para a filial {filial}.",
            route="/financeiro/caixa",
            action_label="Configurar caixa",
            business_context="financeiro.caixa.sem_conta",
        )

    if ar_aberto == 0 and ap_aberto == 0 and reservas_abertas == 0:
        _append_alert(
            items,
            code="OPERACAO_ESTAVEL",
            severity="info",
            title="Operacao sem pendencias abertas",
            text=f"Nao ha AR/AP em aberto nem reservas pendentes na filial {filial}.",
            route="/dashboard",
            action_label="Ver painel",
            business_context="operacao.estavel",
        )

    if perfil == "admin":
        setup = app_setup_status_tx(cur)
        if not setup["setup_completed"]:
            _append_alert(
                items,
                code="SETUP_PENDING",
                severity="warning",
                title="Setup inicial pendente",
                text="O estado persistido de setup ainda nao foi marcado como concluido.",
                route="/usuarios",
                action_label="Revisar setup",
                business_context="administracao.setup.pending",
            )

    severity_order = {"critical": 0, "warning": 1, "info": 2}
    profile_order = {
        "admin": {
            "SETUP_PENDING": 0,
            "PERIODO_FECHADO": 1,
            "AR_OVERDUE": 2,
            "AP_OVERDUE": 3,
        },
        "operador": {
            "PEDIDOS_NO_ITEMS": 0,
            "PEDIDOS_OPEN": 1,
            "RESERVAS_OPEN": 2,
            "AR_DUE_TODAY": 3,
            "AP_DUE_TODAY": 4,
        },
        "user": {
            "AR_OVERDUE": 0,
            "AP_OVERDUE": 1,
            "AR_DUE_TODAY": 2,
            "AP_DUE_TODAY": 3,
        },
    }
    code_priority = profile_order.get(perfil, {})
    items.sort(
        key=lambda item: (
            severity_order.get(item["severity"], 9),
            code_priority.get(item["code"], 99),
            item["title"],
        )
    )

    summary = {
        "critical": sum(1 for item in items if item["severity"] == "critical"),
        "warning": sum(1 for item in items if item["severity"] == "warning"),
        "info": sum(1 for item in items if item["severity"] == "info"),
        "total": len(items),
    }

    return {
        "filial": filial,
        "usuario": login,
        "generated_at": datetime.now().isoformat(timespec="seconds"),
        "summary": summary,
        "items": items,
    }
