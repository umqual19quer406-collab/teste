import { BrowserRouter, Navigate, Route, Routes, Outlet } from "react-router-dom";

import { AuthProvider } from "./auth/AuthContext";
import { RequireAuth } from "./auth/RequireAuth";

import { Login } from "./pages/Login";
import { ClientsList } from "./pages/clientsList";
import { FornecedoresList } from "./pages/FornecedoresList";
import { PedidosList } from "./pages/pedidosList";
import { FinanceiroAR } from "./pages/financeiroAR";
import { FinanceiroAP } from "./pages/financeiroAP";
import { FinanceiroCaixa } from "./pages/financeiroCaixa";
import { FinanceiroCategorias } from "./pages/financeiroCategorias";
import { RelatorioDRE } from "./pages/relatorioDRE";
import { ProdutosList } from "./pages/produtosList";
import { EstoqueEntradaFornecedor } from "./pages/estoqueEntradaFornecedor";
import { Parceiros } from "./pages/parceiros";
import { ReservasList } from "./pages/reservasList";
import { AuditoriaList } from "./pages/auditoriaList";
import { UsuariosList } from "./pages/usuariosList";
import { RelatorioMargemProduto } from "./pages/relatorioMargemProduto";
import { Dashboard } from "./pages/Dashboard";

// Se você já tem componentes de layout, use os seus imports aqui:
import { Sidebar } from "./layout/Sidebar";
import { Topbar } from "./layout/Topbar";

function AppLayout() {
  return (
    <div className="layout">
      <Sidebar />
      <main className="content">
        <Topbar />
        <section className="page">
          <Outlet />
        </section>
      </main>
    </div>
  );
}

export default function App() {
  return (
    <AuthProvider>
      <BrowserRouter>
        <Routes>
          {/* Public */}
          <Route path="/login" element={<Login />} />

          {/* Protected */}
          <Route
            element={
              <RequireAuth>
                <AppLayout />
              </RequireAuth>
            }
          >
            <Route path="/" element={<Navigate to="/dashboard" replace />} />
            <Route path="/dashboard" element={<Dashboard />} />
            <Route path="/clientes" element={<ClientsList />} />
            <Route path="/fornecedores" element={<FornecedoresList />} />
            <Route path="/pedidos" element={<PedidosList />} />
            <Route path="/vendas/pedidos" element={<PedidosList />} />
            <Route path="/financeiro/ar" element={<FinanceiroAR />} />
            <Route path="/financeiro/ap" element={<FinanceiroAP />} />
            <Route path="/financeiro/caixa" element={<FinanceiroCaixa />} />
            <Route path="/financeiro/categorias" element={<FinanceiroCategorias />} />
            <Route path="/relatorios/dre" element={<RelatorioDRE />} />
            <Route path="/produtos" element={<ProdutosList />} />
            <Route path="/custos/fornecedor" element={<EstoqueEntradaFornecedor />} />
            <Route path="/estoque/entrada-fornecedor" element={<EstoqueEntradaFornecedor />} />
            <Route path="/parceiros" element={<Parceiros />} />
            <Route path="/reservas" element={<ReservasList />} />
            <Route path="/auditoria" element={<AuditoriaList />} />
            <Route path="/usuarios" element={<UsuariosList />} />
            <Route path="/relatorios/margem-produto" element={<RelatorioMargemProduto />} />

            {/* Adicione próximos módulos aqui */}
            {/* <Route path="/fornecedores" element={<FornecedoresList />} /> */}
            {/* <Route path="/produtos" element={<ProdutosList />} /> */}
          </Route>

          {/* 404 */}
          <Route path="*" element={<Navigate to="/clientes" replace />} />
        </Routes>
      </BrowserRouter>
    </AuthProvider>
  );
}
