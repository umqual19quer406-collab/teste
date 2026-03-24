import { useEffect, useState } from "react";
import { NavLink } from "react-router-dom";
import { getArea, onAreaChange } from "../state/uiPrefs";

type MenuItem = {
  to: string;
  label: string;
  code: string;
};

type MenuSection = {
  title: string;
  items: MenuItem[];
};

const sections: MenuSection[] = [
  {
    title: "Painel",
    items: [{ to: "/dashboard", label: "Dashboard", code: "DB" }],
  },
  {
    title: "Cadastros",
    items: [
      { to: "/clientes", label: "Clientes", code: "CL" },
      { to: "/fornecedores", label: "Fornecedores", code: "FR" },
      { to: "/produtos", label: "Produtos", code: "PR" },
      { to: "/custos/fornecedor", label: "Custo por Fornecedor", code: "CF" },
      { to: "/parceiros", label: "Parceiros", code: "SA" },
    ],
  },
  {
    title: "Vendas",
    items: [
      { to: "/vendas/pedidos", label: "Pedidos", code: "VD" },
      { to: "/reservas", label: "Reservas", code: "RS" },
    ],
  },
  {
    title: "Financeiro",
    items: [
      { to: "/financeiro/ar", label: "Contas a Receber", code: "AR" },
      { to: "/financeiro/ap", label: "Contas a Pagar", code: "AP" },
      { to: "/financeiro/caixa", label: "Caixa", code: "CX" },
      { to: "/financeiro/categorias", label: "Categorias", code: "CT" },
    ],
  },
  {
    title: "Relatorios",
    items: [
      { to: "/relatorios/dre", label: "DRE", code: "DR" },
      { to: "/relatorios/margem-produto", label: "Margem por Produto", code: "MG" },
    ],
  },
  {
    title: "Administracao",
    items: [
      { to: "/auditoria", label: "Auditoria", code: "AU" },
      { to: "/usuarios", label: "Usuarios", code: "US" },
    ],
  },
];

function linkClass(isActive: boolean) {
  return `nav-item ${isActive ? "active" : ""}`;
}

export function Sidebar() {
  const [area, setArea] = useState(getArea());

  useEffect(() => onAreaChange(setArea), []);

  return (
    <aside className="sidebar-shell">
      <div className="sidebar-brand">
        <div className="brand-mark">MP</div>
        <div>
          <div className="brand-title">Mini Protheus</div>
          <div className="brand-subtitle">ERP operacional</div>
        </div>
      </div>

      <div className="profile-card">
        <div className="profile-avatar">UQ</div>
        <div className="profile-meta">
          <div className="profile-name">Sessao Ativa</div>
          <div className="profile-role">{area}</div>
        </div>
      </div>

      <div className="sidebar-scroll">
        {sections.map((section) => (
          <section key={section.title} className="nav-section">
            <div className="nav-section-title">{section.title}</div>
            <div className="nav-list">
              {section.items.map((item) => (
                <NavLink key={item.to} to={item.to} className={({ isActive }) => linkClass(isActive)}>
                  <span className="nav-code">{item.code}</span>
                  <span className="nav-label">{item.label}</span>
                </NavLink>
              ))}
            </div>
          </section>
        ))}
      </div>

      <div className="sidebar-footer">
        <div className="sidebar-footer-label">Ambiente</div>
        <div className="sidebar-footer-value">{area}</div>
      </div>
    </aside>
  );
}
