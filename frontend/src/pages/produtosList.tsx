import { useState } from "react";
import { Link } from "react-router-dom";
import { getFilial } from "../state/filial";
import { upsertProduto } from "../api/produtos";
import { PageHero } from "../components/PageHero";
import productsIcon from "../assets/shell-icons/products-ref.png";
import productsBg from "../assets/hero-backgrounds/products.webp";

type ProdutoForm = {
  cod: string;
  desc: string;
  preco: string;
  filial: string;
};

function emptyProduto(): ProdutoForm {
  return { cod: "", desc: "", preco: "0", filial: getFilial() };
}

function toNumber(value: string, fallback = 0) {
  const n = Number(value);
  return Number.isFinite(n) ? n : fallback;
}

function getErrorMessage(error: unknown, fallback: string): string {
  if (error instanceof Error && error.message) return error.message;
  return fallback;
}

export function ProdutosList() {
  const [form, setForm] = useState<ProdutoForm>(emptyProduto());
  const [loading, setLoading] = useState(false);
  const [err, setErr] = useState<string | null>(null);
  const [lastResp, setLastResp] = useState<Record<string, unknown> | null>(null);

  async function onSalvar() {
    setErr(null);
    setLoading(true);
    try {
      if (!form.cod.trim() || !form.desc.trim()) {
        throw new Error("Codigo e descricao sao obrigatorios.");
      }
      const resp = await upsertProduto({
        cod: form.cod.trim(),
        desc: form.desc.trim(),
        preco: toNumber(form.preco, 0),
        filial: form.filial || getFilial(),
      });
      setLastResp(resp);
      setForm(emptyProduto());
    } catch (error: unknown) {
      setErr(getErrorMessage(error, "Falha ao salvar produto"));
    } finally {
      setLoading(false);
    }
  }

  return (
    <>
      <PageHero
        icon={productsIcon}
        backgroundImage={productsBg}
        backgroundPosition="center 42%"
        eyebrow="Cadastro e Estoque"
        title="Produtos"
        description="Cadastro base de produtos e ponto de partida para operacoes de estoque, custo medio e entrada por fornecedor."
        metrics={[
          { label: "Filial", value: form.filial || getFilial() },
          { label: "Acao", value: "Upsert" },
          { label: "Operacao", value: "Cadastro + Estoque" },
        ]}
        actions={
          <Link
            to={`/custos/fornecedor${form.cod.trim() ? `?produto=${encodeURIComponent(form.cod.trim())}` : ""}`}
            className="btn primary"
          >
            Formar custo
          </Link>
        }
      />

      <div className="card">
      <div className="section-title">Produto</div>

      {err && <div className="alert mt-12">{err}</div>}

      <div className="stats-grid mt-12">
        <div className="stat-card">
          <div>
            <div className="kpi-label">Acao</div>
            <div className="kpi">Upsert</div>
          </div>
          <div className="stat-icon">PR</div>
        </div>
        <div className="stat-card">
          <div>
            <div className="kpi-label">Endpoint</div>
            <div className="kpi">/produto</div>
          </div>
          <div className="stat-icon solid">API</div>
        </div>
        <div className="stat-card">
          <div>
            <div className="kpi-label">Perfil</div>
            <div className="kpi">Admin</div>
          </div>
          <div className="stat-icon success">AUTH</div>
        </div>
      </div>

      <div className="form-grid mt-12">
        <div className="form-field">
          <label>Codigo</label>
          <input
            value={form.cod}
            onChange={(e) => setForm({ ...form, cod: e.target.value })}
            placeholder="PRD001"
          />
        </div>
        <div className="form-field">
          <label>Descricao</label>
          <input
            value={form.desc}
            onChange={(e) => setForm({ ...form, desc: e.target.value })}
            placeholder="Produto X"
          />
        </div>
        <div className="form-field">
          <label>Preco</label>
          <input
            type="number"
            step="0.01"
            value={form.preco}
            onChange={(e) => setForm({ ...form, preco: e.target.value })}
          />
        </div>
        <div className="form-field">
          <label>Filial</label>
          <input
            value={form.filial}
            onChange={(e) => setForm({ ...form, filial: e.target.value })}
          />
        </div>
        <div className="form-field">
          <label>&nbsp;</label>
          <div className="row gap-10">
            <button className="btn primary" onClick={onSalvar} disabled={loading}>
              Salvar produto
            </button>
            <Link
              to={`/custos/fornecedor${form.cod.trim() ? `?produto=${encodeURIComponent(form.cod.trim())}` : ""}`}
              className="btn"
            >
              Ir para custo
            </Link>
          </div>
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
