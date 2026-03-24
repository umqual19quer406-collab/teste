import { useState } from "react";
import { bootstrapAdmin, criarUsuario } from "../api/usuarios";
import { PageHero } from "../components/PageHero";
import usersIcon from "../assets/shell-icons/users.png";
import usersBg from "../assets/hero-backgrounds/users.webp";

type BootstrapForm = {
  login: string;
  senha: string;
};

type UsuarioForm = {
  login: string;
  senha: string;
  perfil: string;
};

function emptyBootstrap(): BootstrapForm {
  return { login: "", senha: "" };
}

function emptyUsuario(): UsuarioForm {
  return { login: "", senha: "", perfil: "operador" };
}

function getErrorMessage(error: unknown, fallback: string): string {
  if (error instanceof Error && error.message) return error.message;
  return fallback;
}

export function UsuariosList() {
  const [bootForm, setBootForm] = useState<BootstrapForm>(emptyBootstrap());
  const [userForm, setUserForm] = useState<UsuarioForm>(emptyUsuario());

  const [loading, setLoading] = useState(false);
  const [err, setErr] = useState<string | null>(null);
  const [lastResp, setLastResp] = useState<Record<string, unknown> | null>(null);

  async function onBootstrap() {
    setErr(null);
    setLoading(true);
    try {
      if (!bootForm.login.trim() || !bootForm.senha.trim()) {
        throw new Error("Login e senha sao obrigatorios.");
      }
      const resp = await bootstrapAdmin({
        login: bootForm.login.trim(),
        senha: bootForm.senha,
      });
      setLastResp(resp as Record<string, unknown>);
      setBootForm(emptyBootstrap());
    } catch (error: unknown) {
      setErr(getErrorMessage(error, "Falha no bootstrap"));
    } finally {
      setLoading(false);
    }
  }

  async function onCriarUsuario() {
    setErr(null);
    setLoading(true);
    try {
      if (!userForm.login.trim() || !userForm.senha.trim() || !userForm.perfil.trim()) {
        throw new Error("Login, senha e perfil sao obrigatorios.");
      }
      const resp = await criarUsuario({
        login: userForm.login.trim(),
        senha: userForm.senha,
        perfil: userForm.perfil,
      });
      setLastResp(resp as Record<string, unknown>);
      setUserForm(emptyUsuario());
    } catch (error: unknown) {
      setErr(getErrorMessage(error, "Falha ao criar usuario"));
    } finally {
      setLoading(false);
    }
  }

  return (
    <>
      <PageHero
        icon={usersIcon}
        backgroundImage={usersBg}
        backgroundPosition="center 24%"
        eyebrow="Administracao"
        title="Usuarios e bootstrap"
        description="Controle do admin inicial e criacao de novos usuarios para operacao, auditoria e administracao."
        metrics={[
          { label: "Bootstrap", value: "One-time" },
          { label: "Criacao", value: "Admin only" },
          { label: "Contrato", value: "/usuarios" },
        ]}
      />

      <div className="card">
      <div className="section-title">Usuarios</div>

      {err && <div className="alert mt-12">{err}</div>}

      <div className="stats-grid mt-12">
        <div className="stat-card">
          <div>
            <div className="kpi-label">Acoes</div>
            <div className="kpi">Bootstrap / Criar</div>
          </div>
          <div className="stat-icon">US</div>
        </div>
        <div className="stat-card">
          <div>
            <div className="kpi-label">Requer login</div>
            <div className="kpi">Somente /usuarios</div>
          </div>
          <div className="stat-icon solid">AUTH</div>
        </div>
        <div className="stat-card">
          <div>
            <div className="kpi-label">Bootstrap</div>
            <div className="kpi">Admin inicial</div>
          </div>
          <div className="stat-icon success">ADM</div>
        </div>
      </div>

      <div className="form-grid mt-12">
        <div className="form-field col-span-all">
          <label>Bootstrap (criar admin inicial)</label>
          <div className="hint">Use apenas uma vez. Depois disso, o endpoint bloqueia.</div>
        </div>
        <div className="form-field">
          <label>Login</label>
          <input
            value={bootForm.login}
            onChange={(e) => setBootForm({ ...bootForm, login: e.target.value })}
            placeholder="admin"
          />
        </div>
        <div className="form-field">
          <label>Senha</label>
          <input
            type="password"
            value={bootForm.senha}
            onChange={(e) => setBootForm({ ...bootForm, senha: e.target.value })}
            placeholder="••••••"
          />
        </div>
        <div className="form-field">
          <label>&nbsp;</label>
          <button className="btn primary" onClick={onBootstrap} disabled={loading}>
            Executar bootstrap
          </button>
        </div>
      </div>

      <div className="form-grid mt-12">
        <div className="form-field col-span-all">
          <label>Criar usuario</label>
          <div className="hint">Requer login como admin.</div>
        </div>
        <div className="form-field">
          <label>Login</label>
          <input
            value={userForm.login}
            onChange={(e) => setUserForm({ ...userForm, login: e.target.value })}
            placeholder="usuario"
          />
        </div>
        <div className="form-field">
          <label>Senha</label>
          <input
            type="password"
            value={userForm.senha}
            onChange={(e) => setUserForm({ ...userForm, senha: e.target.value })}
            placeholder="••••••"
          />
        </div>
        <div className="form-field">
          <label>Perfil</label>
          <select
            className="select"
            value={userForm.perfil}
            onChange={(e) => setUserForm({ ...userForm, perfil: e.target.value })}
          >
            <option value="admin">admin</option>
            <option value="operador">operador</option>
            <option value="auditor">auditor</option>
          </select>
        </div>
        <div className="form-field">
          <label>&nbsp;</label>
          <button className="btn" onClick={onCriarUsuario} disabled={loading}>
            Criar usuario
          </button>
        </div>
      </div>

      {lastResp && (
        <div className="card soft mt-12">
          <div style={{ fontWeight: 700 }}>Ultima resposta da API</div>
          <pre style={{ margin: 0, whiteSpace: "pre-wrap" }}>{JSON.stringify(lastResp, null, 2)}</pre>
        </div>
      )}
      </div>
    </>
  );
}
