import { useState } from "react";
import { useNavigate } from "react-router-dom";
import { useAuth } from "../auth/AuthContext";

export function Login() {
  const { login } = useAuth();
  const navigate = useNavigate();
  const [username, setUsername] = useState("");
  const [password, setPassword] = useState("");
  const [err, setErr] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);

  function getErrorMessage(error: unknown, fallback: string): string {
    if (error instanceof Error && error.message) return error.message;
    return fallback;
  }

  return (
    <div className="login-shell">
      <div className="login-backdrop" />

      <section className="login-showcase">
        <div className="login-showcase-inner">
          <div className="login-badge">ERP operacional com vendas, financeiro e reservas</div>
          <h1 className="login-title">Mini Protheus</h1>
          <p className="login-copy">
            Ambiente de operacao para pedidos, parceiros, contas a receber, contas a pagar,
            caixa, auditoria e relatorios gerenciais.
          </p>

          <div className="showcase-grid">
            <article className="showcase-card">
              <div className="showcase-card-label">Comercial</div>
              <div className="showcase-card-value">Pedidos, faturamento e reservas</div>
            </article>
            <article className="showcase-card">
              <div className="showcase-card-label">Financeiro</div>
              <div className="showcase-card-value">AR, AP, caixa e categorias</div>
            </article>
            <article className="showcase-card">
              <div className="showcase-card-label">Governanca</div>
              <div className="showcase-card-value">Usuarios, bootstrap e auditoria</div>
            </article>
          </div>
        </div>
      </section>

      <section className="login-panel">
        <div className="login-card">
          <div className="login-card-top">
            <div className="login-card-mark">MP</div>
            <div>
              <div className="login-card-title">Acesso ao sistema</div>
              <div className="login-card-subtitle">Use sua credencial para entrar no ambiente ERP</div>
            </div>
          </div>

          {err && <div className="alert login-alert">{err}</div>}

          <div className="form-field">
            <label>Usuario</label>
            <input
              className="input"
              value={username}
              onChange={(event) => setUsername(event.target.value)}
              placeholder="admin"
            />
          </div>

          <div className="form-field">
            <label>Senha</label>
            <input
              className="input"
              type="password"
              value={password}
              onChange={(event) => setPassword(event.target.value)}
              placeholder="Digite sua senha"
            />
          </div>

          <div className="login-helper-row">
            <span className="login-helper-label">Backend</span>
            <span className="login-helper-value">JWT + FastAPI + SQL Server</span>
          </div>

          <button
            className="btn primary login-submit"
            disabled={loading}
            onClick={async () => {
              setErr(null);
              setLoading(true);
              try {
                await login(username, password);
                navigate("/clientes");
              } catch (error: unknown) {
                setErr(getErrorMessage(error, "Falha no login"));
              } finally {
                setLoading(false);
              }
            }}
          >
            {loading ? "Entrando..." : "Entrar no ERP"}
          </button>
        </div>
      </section>
    </div>
  );
}
