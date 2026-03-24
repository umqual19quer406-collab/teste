import { Link } from "react-router-dom";
import { PageHero } from "../components/PageHero";
import dashboardIcon from "../assets/shell-icons/dashboard-ref.png";
import ordersIcon from "../assets/shell-icons/orders-ref.png";
import receivablesIcon from "../assets/shell-icons/receivables-ref.png";
import payablesIcon from "../assets/shell-icons/payables-ref.png";
import cashIcon from "../assets/shell-icons/cash-ref.png";
import reportsIcon from "../assets/shell-icons/reports-ref.png";
import partnersIcon from "../assets/shell-icons/partners-ref.png";
import usersIcon from "../assets/shell-icons/users-ref.svg";
import inventoryIcon from "../assets/shell-icons/products-ref.png";

const quickActions = [
  { to: "/vendas/pedidos", label: "Pedidos", subtitle: "Criacao, itens e faturamento", icon: ordersIcon },
  { to: "/financeiro/ar", label: "Contas a Receber", subtitle: "Recebimento e baixa", icon: receivablesIcon },
  { to: "/financeiro/ap", label: "Contas a Pagar", subtitle: "Pagamento operacional", icon: payablesIcon },
  { to: "/financeiro/caixa", label: "Caixa", subtitle: "Saldo e extrato", icon: cashIcon },
  { to: "/parceiros", label: "Parceiros", subtitle: "Clientes e fornecedores", icon: partnersIcon },
  { to: "/produtos", label: "Produtos", subtitle: "Cadastro e base comercial", icon: inventoryIcon },
  { to: "/relatorios/dre", label: "Relatorios", subtitle: "DRE e margem", icon: reportsIcon },
  { to: "/usuarios", label: "Usuarios", subtitle: "Bootstrap e perfis", icon: usersIcon },
];

export function Dashboard() {
  return (
    <div className="dashboard-stack">
      <PageHero
        icon={dashboardIcon}
        eyebrow="Centro de operacoes"
        title="Painel executivo"
        description="Atalhos operacionais para vendas, financeiro, cadastro e governanca, com uma linguagem visual mais proxima de ERP corporativo."
        metrics={[
          { label: "Modulos principais", value: "8" },
          { label: "Camadas", value: "API + Vite + SQL" },
          { label: "Foco", value: "Operacao" },
        ]}
        actions={
          <>
            <Link to="/vendas/pedidos" className="btn primary">
              Ir para pedidos
            </Link>
            <Link to="/financeiro/caixa" className="btn">
              Abrir caixa
            </Link>
          </>
        }
      />

      <section className="dashboard-grid">
        <div className="card dashboard-block dashboard-block-wide">
          <div className="dashboard-block-glow" />
          <div className="dashboard-block-header">
            <div>
              <div className="dashboard-block-eyebrow">Acesso rapido</div>
              <div className="dashboard-block-title">Modulos operacionais</div>
            </div>
          </div>

          <div className="quick-grid">
            {quickActions.map((item) => (
              <Link key={item.to} to={item.to} className="quick-card">
                <div className="quick-card-media">
                  <img src={item.icon} alt="" className="quick-card-icon" />
                </div>
                <div className="quick-card-label">{item.label}</div>
                <div className="quick-card-subtitle">{item.subtitle}</div>
              </Link>
            ))}
          </div>
        </div>

        <div className="card dashboard-block">
          <div className="dashboard-block-glow dashboard-block-glow-secondary" />
          <div className="dashboard-block-header">
            <div>
              <div className="dashboard-block-eyebrow">Operacao</div>
              <div className="dashboard-block-title">Leituras de ambiente</div>
            </div>
          </div>

          <div className="dashboard-summary-grid">
            <article className="summary-tile summary-tile-green">
              <div className="summary-tile-title">Recebiveis</div>
              <div className="summary-tile-value">AR integrado</div>
              <div className="summary-tile-sub">Recebimento e reflexo no caixa</div>
            </article>

            <article className="summary-tile summary-tile-red">
              <div className="summary-tile-title">Pagamentos</div>
              <div className="summary-tile-value">AP integrado</div>
              <div className="summary-tile-sub">Saida de caixa e baixa controlada</div>
            </article>

            <article className="summary-tile summary-tile-cyan">
              <div className="summary-tile-title">Comercial</div>
              <div className="summary-tile-value">Pedidos + reserva</div>
              <div className="summary-tile-sub">Fluxo de venda ate o financeiro</div>
            </article>
          </div>
        </div>
      </section>
    </div>
  );
}
