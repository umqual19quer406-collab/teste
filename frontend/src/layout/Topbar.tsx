import { useEffect, useState } from "react";
import { useLocation, useNavigate } from "react-router-dom";
import { useAuth } from "../auth/AuthContext";
import { listarAlertas, type BackendAlertItem } from "../api/alertas";
import { getFilial, onFilialChange, setFilial } from "../state/filial";
import { Modal } from "../components/Modal";
import {
  AVAILABLE_AREAS,
  getArea,
  getFavorites,
  onAreaChange,
  onFavoritesChange,
  setArea,
  toggleFavorite,
  type UiArea,
} from "../state/uiPrefs";

const titles: Record<string, string> = {
  "/dashboard": "Centro de Operacoes",
  "/clientes": "Gestao de Clientes",
  "/fornecedores": "Gestao de Fornecedores",
  "/produtos": "Cadastro de Produtos",
  "/parceiros": "Painel de Parceiros",
  "/pedidos": "Pedidos de Venda",
  "/vendas/pedidos": "Pedidos de Venda",
  "/financeiro/ar": "Contas a Receber",
  "/financeiro/ap": "Contas a Pagar",
  "/financeiro/caixa": "Caixa e Extrato",
  "/financeiro/categorias": "Categorias Financeiras",
  "/relatorios/dre": "Demonstrativo DRE",
  "/relatorios/margem-produto": "Margem por Produto",
  "/reservas": "Reservas de Estoque",
  "/auditoria": "Auditoria Operacional",
  "/usuarios": "Usuarios e Bootstrap",
};

const routeCatalog = [
  { path: "/dashboard", label: "Dashboard", category: "Painel" },
  { path: "/clientes", label: "Clientes", category: "Cadastros" },
  { path: "/fornecedores", label: "Fornecedores", category: "Cadastros" },
  { path: "/produtos", label: "Produtos", category: "Cadastros" },
  { path: "/parceiros", label: "Parceiros", category: "Cadastros" },
  { path: "/vendas/pedidos", label: "Pedidos", category: "Vendas" },
  { path: "/reservas", label: "Reservas", category: "Vendas" },
  { path: "/financeiro/ar", label: "Contas a Receber", category: "Financeiro" },
  { path: "/financeiro/ap", label: "Contas a Pagar", category: "Financeiro" },
  { path: "/financeiro/caixa", label: "Caixa", category: "Financeiro" },
  { path: "/financeiro/categorias", label: "Categorias", category: "Financeiro" },
  { path: "/relatorios/dre", label: "DRE", category: "Relatorios" },
  { path: "/relatorios/margem-produto", label: "Margem por Produto", category: "Relatorios" },
  { path: "/auditoria", label: "Auditoria", category: "Administracao" },
  { path: "/usuarios", label: "Usuarios", category: "Administracao" },
];

type PanelKey = "favorites" | "alerts" | "help" | "area" | null;

function resolveAlertRoute(alert: BackendAlertItem) {
  const contextToRoute: Record<string, string> = {
    "financeiro.ar.overdue": "/financeiro/ar?alert=ar_overdue",
    "financeiro.ar.due_today": "/financeiro/ar?alert=ar_due_today",
    "financeiro.ar.due_soon": "/financeiro/ar?alert=ar_due_soon",
    "financeiro.ap.overdue": "/financeiro/ap?alert=ap_overdue",
    "financeiro.ap.due_today": "/financeiro/ap?alert=ap_due_today",
    "financeiro.ap.due_soon": "/financeiro/ap?alert=ap_due_soon",
    "vendas.pedidos.sem_itens": "/vendas/pedidos?alert=pedidos_no_items",
    "vendas.pedidos.abertos": "/vendas/pedidos?alert=pedidos_open",
  };

  if (alert.business_context && contextToRoute[alert.business_context]) {
    return contextToRoute[alert.business_context];
  }
  return alert.route || "/dashboard";
}

export function Topbar() {
  const location = useLocation();
  const navigate = useNavigate();
  const { logout } = useAuth();

  const [filial, setFilialState] = useState(getFilial());
  const [shortcut, setShortcut] = useState("");
  const [area, setAreaState] = useState<UiArea>(getArea());
  const [favorites, setFavorites] = useState<string[]>(getFavorites());
  const [panel, setPanel] = useState<PanelKey>(null);
  const [alertsLoading, setAlertsLoading] = useState(false);
  const [alertsError, setAlertsError] = useState<string | null>(null);
  const [alertsData, setAlertsData] = useState<BackendAlertItem[]>([]);

  useEffect(() => onFilialChange(setFilialState), []);
  useEffect(() => onAreaChange(setAreaState), []);
  useEffect(() => onFavoritesChange(setFavorites), []);

  const title = titles[location.pathname] ?? "Centro de Operacoes";
  const currentRoute = routeCatalog.find((item) => item.path === location.pathname);
  const isFavorite = favorites.includes(location.pathname);

  const favoriteRoutes = routeCatalog.filter((item) => favorites.includes(item.path));

  async function refreshAlerts(targetFilial: string) {
    setAlertsLoading(true);
    setAlertsError(null);
    try {
      const response = await listarAlertas({ filial: targetFilial });
      setAlertsData(response.items);
    } catch (error: unknown) {
      const message = error instanceof Error ? error.message : "Erro ao carregar alertas";
      setAlertsError(message);
      setAlertsData([]);
    } finally {
      setAlertsLoading(false);
    }
  }

  function openRoute(path: string) {
    navigate(path);
    setPanel(null);
  }

  function onShortcutSubmit() {
    const query = shortcut.trim().toLowerCase();
    if (!query) return;
    const match = routeCatalog.find(
      (item) =>
        item.label.toLowerCase().includes(query) ||
        item.category.toLowerCase().includes(query) ||
        item.path.toLowerCase().includes(query)
    );
    if (match) {
      navigate(match.path);
      setShortcut("");
    }
  }

  return (
    <>
      <header className="topbar-shell">
        <div className="topbar-title-block">
          <div className="topbar-eyebrow">Mini Protheus ERP</div>
          <div className="topbar-title">{title}</div>
        </div>

        <div className="topbar-search">
          <input
            className="shell-input"
            value={shortcut}
            onChange={(event) => setShortcut(event.target.value)}
            onKeyDown={(event) => {
              if (event.key === "Enter") onShortcutSubmit();
            }}
            placeholder="Buscar modulo, fluxo ou acao rapida"
            aria-label="Atalho rapido"
          />
        </div>

        <div className="topbar-actions">
          <button type="button" className="icon-action" aria-label="Favoritos" onClick={() => setPanel("favorites")}>
            Favoritos
          </button>
          <button
            type="button"
            className="icon-action"
            aria-label="Alertas"
            onClick={() => {
              setPanel("alerts");
              void refreshAlerts(filial);
            }}
          >
            Alertas
          </button>
          <button type="button" className="icon-action" aria-label="Ajuda" onClick={() => setPanel("help")}>
            Ajuda
          </button>

          <button type="button" className="topbar-pill topbar-pill-button" onClick={() => setPanel("area")}>
            {area}
          </button>

          <label className="filial-picker">
            <span>Filial</span>
            <select
              className="shell-select"
              value={filial}
              onChange={(event) => {
                const nextFilial = event.target.value;
                setFilial(nextFilial);
                if (panel === "alerts") {
                  void refreshAlerts(nextFilial);
                }
              }}
              aria-label="Selecionar filial"
            >
              <option value="01">01</option>
              <option value="02">02</option>
              <option value="03">03</option>
            </select>
          </label>

          <button
            type="button"
            className="btn shell-logout"
            onClick={() => {
              logout();
              navigate("/login");
            }}
          >
            Sair
          </button>
        </div>
      </header>

      {panel === "favorites" && (
        <Modal title="Favoritos" onClose={() => setPanel(null)}>
          <div className="panel-stack">
            <div className="topbar-panel-box">
              <div className="topbar-panel-title">Pagina atual</div>
              <div className="topbar-panel-text">
                {currentRoute ? `${currentRoute.label} (${currentRoute.category})` : location.pathname}
              </div>
              <div className="panel-actions">
                <button type="button" className="btn primary" onClick={() => toggleFavorite(location.pathname)}>
                  {isFavorite ? "Remover dos favoritos" : "Adicionar aos favoritos"}
                </button>
              </div>
            </div>

            <div className="topbar-panel-box">
              <div className="topbar-panel-title">Rotas favoritas</div>
              {favoriteRoutes.length === 0 ? (
                <div className="topbar-panel-empty">Nenhum favorito salvo no navegador.</div>
              ) : (
                <div className="panel-route-list">
                  {favoriteRoutes.map((item) => (
                    <button key={item.path} type="button" className="route-chip" onClick={() => openRoute(item.path)}>
                      <span>{item.label}</span>
                      <small>{item.category}</small>
                    </button>
                  ))}
                </div>
              )}
            </div>
          </div>
        </Modal>
      )}

      {panel === "alerts" && (
        <Modal title="Alertas" onClose={() => setPanel(null)}>
          <div className="panel-stack">
            <div className="topbar-panel-box">
              <div className="topbar-panel-title">Contexto monitorado</div>
              <div className="topbar-panel-text">Filial {filial}. Area visual {area}. Alertas guiados por regra de negocio.</div>
            </div>

            {alertsLoading && <div className="topbar-panel-empty">Carregando alertas operacionais...</div>}

            {alertsError && <div className="topbar-alert-card warning">{alertsError}</div>}

            {!alertsLoading && !alertsError && alertsData.length === 0 && (
              <div className="topbar-panel-empty">Nenhum alerta ativo retornado pelo backend.</div>
            )}

            {alertsData.map((alert) => (
              <div key={`${alert.code}-${alert.title}`} className={`topbar-alert-card ${alert.severity}`}>
                <div className="topbar-panel-title">{alert.title}</div>
                <div className="topbar-panel-text">{alert.text}</div>
                {alert.business_context && <div className="topbar-panel-text"><small>{alert.business_context}</small></div>}
                {alert.route && (
                  <div className="panel-actions">
                    <button type="button" className="btn" onClick={() => openRoute(resolveAlertRoute(alert))}>
                      {alert.action_label || "Abrir modulo"}
                    </button>
                  </div>
                )}
              </div>
            ))}
          </div>
        </Modal>
      )}

      {panel === "help" && (
        <Modal title="Ajuda" onClose={() => setPanel(null)}>
          <div className="panel-stack">
            <div className="topbar-panel-box">
              <div className="topbar-panel-title">Navegacao rapida</div>
              <div className="topbar-panel-text">
                Use o campo de busca do topo e pressione Enter para abrir um modulo pelo nome ou caminho.
              </div>
            </div>

            <div className="topbar-panel-box">
              <div className="topbar-panel-title">Atalhos uteis</div>
              <ul className="help-list">
                <li>`Favoritos`: salva a rota atual no navegador para acesso rapido.</li>
                <li>`Alertas`: mostra lembretes operacionais e contexto da sessao.</li>
                <li>`Area`: troca o contexto visual padrao da sessao.</li>
                <li>`Filial`: muda o contexto usado pelas telas que respeitam filial.</li>
              </ul>
            </div>

            <div className="topbar-panel-box">
              <div className="topbar-panel-title">Modulos principais</div>
              <div className="panel-route-list">
                {routeCatalog.slice(0, 8).map((item) => (
                  <button key={item.path} type="button" className="route-chip" onClick={() => openRoute(item.path)}>
                    <span>{item.label}</span>
                    <small>{item.category}</small>
                  </button>
                ))}
              </div>
            </div>
          </div>
        </Modal>
      )}

      {panel === "area" && (
        <Modal title="Area padrao" onClose={() => setPanel(null)}>
          <div className="panel-stack">
            <div className="topbar-panel-box">
              <div className="topbar-panel-title">Contexto atual</div>
              <div className="topbar-panel-text">
                A area selecionada ajusta o contexto visual da sessao no frontend.
              </div>
            </div>

            <div className="panel-route-list">
              {AVAILABLE_AREAS.map((item) => (
                <button
                  key={item}
                  type="button"
                  className={`route-chip ${item === area ? "active" : ""}`}
                  onClick={() => {
                    setArea(item);
                    setPanel(null);
                  }}
                >
                  <span>{item}</span>
                  <small>{item === area ? "Selecionada" : "Selecionar"}</small>
                </button>
              ))}
            </div>
          </div>
        </Modal>
      )}
    </>
  );
}
