import { useEffect, useMemo, useState } from "react";
import { useNavigate, useSearchParams } from "react-router-dom";
import { PageHero } from "../components/PageHero";
import { getFilial, onFilialChange } from "../state/filial";
import { listFornecedores, type Fornecedor } from "../api/fornecedores";
import { buscarProdutos, type ProdutoResumo } from "../api/produtos";
import {
  consultarEstoque,
  entradaEstoque,
  extratoEstoque,
  type EstoqueSnapshot,
  type Sd3Movimento,
} from "../api/estoque";
import inventoryIcon from "../assets/shell-icons/inventory.png";
import supplierEntryBg from "../assets/hero-backgrounds/supplier-entry.webp";

type EntradaForm = {
  cod: string;
  filial: string;
  fornecedorCod: string;
  qtd: string;
  custoUnit: string;
  vencDias: string;
};

function emptyForm(): EntradaForm {
  return {
    cod: "",
    filial: getFilial(),
    fornecedorCod: "",
    qtd: "1",
    custoUnit: "0",
    vencDias: "30",
  };
}

function toNumber(value: string, fallback = 0) {
  const n = Number(value);
  return Number.isFinite(n) ? n : fallback;
}

function formatCurrency(value: unknown) {
  const n = Number(value);
  const safe = Number.isFinite(n) ? n : 0;
  return safe.toLocaleString("pt-BR", { style: "currency", currency: "BRL" });
}

function getErrorMessage(error: unknown, fallback: string) {
  if (error instanceof Error && error.message) return error.message;
  return fallback;
}

function findFornecedorName(items: Fornecedor[], cod: string) {
  const found = items.find((item) => item.cod === cod);
  return found?.nome ?? "Sem fornecedor";
}

export function EstoqueEntradaFornecedor() {
  const navigate = useNavigate();
  const [searchParams, setSearchParams] = useSearchParams();
  const [form, setForm] = useState<EntradaForm>(emptyForm());
  const [fornecedores, setFornecedores] = useState<Fornecedor[]>([]);
  const [fornecedorQuery, setFornecedorQuery] = useState("");
  const [fornecedorResultados, setFornecedorResultados] = useState<Fornecedor[]>([]);
  const [produtoQuery, setProdutoQuery] = useState("");
  const [produtoResultados, setProdutoResultados] = useState<ProdutoResumo[]>([]);
  const [beforeSnap, setBeforeSnap] = useState<EstoqueSnapshot | null>(null);
  const [afterSnap, setAfterSnap] = useState<EstoqueSnapshot | null>(null);
  const [extrato, setExtrato] = useState<Sd3Movimento[]>([]);
  const [loading, setLoading] = useState(false);
  const [loadingProdutos, setLoadingProdutos] = useState(false);
  const [loadingFornecedores, setLoadingFornecedores] = useState(false);
  const [err, setErr] = useState<string | null>(null);
  const [okMsg, setOkMsg] = useState<string | null>(null);

  const fornecedorNome = useMemo(
    () => findFornecedorName(fornecedores, form.fornecedorCod),
    [fornecedores, form.fornecedorCod]
  );

  async function loadFornecedores(filial = getFilial()) {
    try {
      const data = await listFornecedores({ ativos: true, filial });
      setFornecedores(data);
    } catch {
      setFornecedores([]);
    }
  }

  async function onBuscarProdutos() {
    const query = produtoQuery.trim();
    if (!query) {
      setProdutoResultados([]);
      return;
    }
    setErr(null);
    setLoadingProdutos(true);
    try {
      const data = await buscarProdutos({
        q: query,
        filial: form.filial || getFilial(),
        limite: 8,
      });
      setProdutoResultados(data);
    } catch (error: unknown) {
      setErr(getErrorMessage(error, "Falha ao buscar produtos"));
      setProdutoResultados([]);
    } finally {
      setLoadingProdutos(false);
    }
  }

  async function onBuscarFornecedores() {
    const query = fornecedorQuery.trim();
    if (!query) {
      setFornecedorResultados([]);
      return;
    }
    setErr(null);
    setLoadingFornecedores(true);
    try {
      const data = await listFornecedores({
        ativos: true,
        filial: form.filial || getFilial(),
      });
      const normalized = query.toLowerCase();
      const filtered = data.filter((item) => {
        const cod = item.cod.toLowerCase();
        const nome = (item.nome || "").toLowerCase();
        return cod.includes(normalized) || nome.includes(normalized);
      });
      setFornecedorResultados(filtered.slice(0, 8));
    } catch (error: unknown) {
      setErr(getErrorMessage(error, "Falha ao buscar fornecedores"));
      setFornecedorResultados([]);
    } finally {
      setLoadingFornecedores(false);
    }
  }

  async function refreshProduto(cod = form.cod.trim(), filial = form.filial || getFilial()) {
    if (!cod) return;
    const [snap, movimentos] = await Promise.all([
      consultarEstoque({ cod, filial }),
      extratoEstoque({ cod, filial, limite: 10 }),
    ]);
    setBeforeSnap(snap);
    setExtrato(movimentos);
  }

  useEffect(() => {
    loadFornecedores();
    const unsub = onFilialChange((novaFilial) => {
      setForm((current) => ({ ...current, filial: novaFilial }));
      setBeforeSnap(null);
      setAfterSnap(null);
      setExtrato([]);
      setErr(null);
      setOkMsg(null);
      loadFornecedores(novaFilial);
    });
    return unsub;
  }, []);

  useEffect(() => {
    const fornecedorCod = (searchParams.get("fornecedor") || "").trim().toUpperCase();
    const produtoCod = (searchParams.get("produto") || "").trim().toUpperCase();
    if (!fornecedorCod && !produtoCod) return;

    setForm((current) => ({
      ...current,
      fornecedorCod: fornecedorCod || current.fornecedorCod,
      cod: produtoCod || current.cod,
    }));

    if (fornecedorCod) {
      const fornecedor = fornecedores.find((item) => item.cod === fornecedorCod);
      setFornecedorQuery(fornecedor?.nome || fornecedorCod);
    }
    if (produtoCod) {
      setProdutoQuery(produtoCod);
    }
  }, [searchParams, fornecedores]);

  async function onConsultarProduto() {
    setErr(null);
    setOkMsg(null);
    try {
      await refreshProduto();
    } catch (error: unknown) {
      setBeforeSnap(null);
      setAfterSnap(null);
      setExtrato([]);
      setErr(getErrorMessage(error, "Falha ao consultar produto"));
    }
  }

  async function onLancarEntrada() {
    setErr(null);
    setOkMsg(null);
    setLoading(true);
    try {
      const cod = form.cod.trim();
      if (!cod) throw new Error("Informe o codigo do produto.");
      const qtd = toNumber(form.qtd, 0);
      const custoUnit = toNumber(form.custoUnit, -1);
      const vencDias = toNumber(form.vencDias, 30);
      if (qtd <= 0) throw new Error("Quantidade deve ser maior que zero.");
      if (custoUnit < 0) throw new Error("Custo unitario nao pode ser negativo.");

      const snapAnterior = await consultarEstoque({ cod, filial: form.filial || getFilial() });
      setBeforeSnap(snapAnterior);

      const snapNovo = await entradaEstoque({
        cod,
        qtd,
        filial: form.filial || getFilial(),
        custo_unit: custoUnit,
        forn: form.fornecedorCod.trim() || null,
        venc_dias: vencDias,
      });
      setAfterSnap(snapNovo);
      setOkMsg(
        [
          "Entrada registrada com sucesso.",
          form.fornecedorCod
            ? `Fornecedor ${form.fornecedorCod} vinculado; AP gerado conforme o valor da entrada.`
            : "Sem fornecedor informado; nenhum AP foi gerado.",
        ].join(" ")
      );
      const movimentos = await extratoEstoque({
        cod,
        filial: form.filial || getFilial(),
        limite: 10,
      });
      setExtrato(movimentos);
    } catch (error: unknown) {
      setErr(getErrorMessage(error, "Falha ao registrar entrada de estoque"));
    } finally {
      setLoading(false);
    }
  }

  return (
    <>
      <PageHero
        icon={inventoryIcon}
        backgroundImage={supplierEntryBg}
        backgroundPosition="center 46%"
        eyebrow="Custos, Estoque e Compras"
        title="Custo por fornecedor"
        description="Area operacional para formar custo medio por compra. Voce escolhe fornecedor, produto, quantidade e custo unitario; o sistema registra a entrada, recalcula o B1_CM e pode gerar o AP vinculado."
        metrics={[
          { label: "Filial", value: form.filial || getFilial() },
          { label: "Fornecedor", value: form.fornecedorCod ? fornecedorNome : "Nao vinculado" },
          { label: "Resultado", value: "Atualiza B1_CM" },
        ]}
      />

      <div className="card">
        <div className="section-title">Formacao de custo com fornecedor</div>

        {err ? <div className="alert mt-12">{err}</div> : null}
        {okMsg ? <div className="alert alert-success mt-12">{okMsg}</div> : null}

        <div className="stats-grid mt-12">
          <div className="stat-card">
            <div>
              <div className="kpi-label">Etapa 1</div>
              <div className="kpi">Fornecedor + Produto</div>
            </div>
            <div className="stat-icon">CF</div>
          </div>
          <div className="stat-card">
            <div>
              <div className="kpi-label">Etapa 2</div>
              <div className="kpi">Qtd + Custo Unitario</div>
            </div>
            <div className="stat-icon solid">CM</div>
          </div>
          <div className="stat-card">
            <div>
              <div className="kpi-label">Etapa 3</div>
              <div className="kpi">Atualiza B1_CM + AP</div>
            </div>
            <div className="stat-icon success">AP</div>
          </div>
        </div>

        <div className="detail-grid mt-12">
          <div className="card soft">
            <div className="kpi-label">Como usar</div>
            <div className="hint">
              Selecione um fornecedor e um produto, informe quantidade e custo unitario, depois lance
              a entrada. Esse fluxo forma o custo medio do produto a partir da compra.
            </div>
          </div>
          <div className="card soft">
            <div className="kpi-label">O que muda no produto</div>
            <div className="hint">
              O sistema recalcula o <strong>B1_CM</strong> e aumenta o estoque disponivel na filial.
            </div>
          </div>
          <div className="card soft">
            <div className="kpi-label">O que muda no financeiro</div>
            <div className="hint">
              Com fornecedor informado, a entrada pode abrir um titulo em Contas a Pagar para seguir o
              fluxo operacional completo.
            </div>
          </div>
        </div>

        <div className="form-grid mt-12">
          <div className="form-field">
            <label>Buscar fornecedor</label>
            <input
              value={fornecedorQuery}
              onChange={(e) => setFornecedorQuery(e.target.value)}
              placeholder="Codigo ou nome"
            />
          </div>
          <div className="form-field">
            <label>&nbsp;</label>
            <button
              className="btn"
              onClick={onBuscarFornecedores}
              disabled={loading || loadingFornecedores}
            >
              {loadingFornecedores ? "Buscando..." : "Buscar fornecedor"}
            </button>
          </div>
          <div className="form-field">
            <label>Buscar produto</label>
            <input
              value={produtoQuery}
              onChange={(e) => setProdutoQuery(e.target.value)}
              placeholder="Codigo ou descricao"
            />
          </div>
          <div className="form-field">
            <label>&nbsp;</label>
            <button className="btn" onClick={onBuscarProdutos} disabled={loading || loadingProdutos}>
              {loadingProdutos ? "Buscando..." : "Buscar produto"}
            </button>
          </div>
          <div className="form-field">
            <label>Produto (codigo)</label>
            <input
              value={form.cod}
              onChange={(e) => setForm({ ...form, cod: e.target.value.toUpperCase() })}
              placeholder="CEL124"
            />
          </div>
          <div className="form-field">
            <label>Fornecedor</label>
            <select
              className="select"
              value={form.fornecedorCod}
              onChange={(e) => setForm({ ...form, fornecedorCod: e.target.value })}
            >
              <option value="">Sem fornecedor (nao gerar AP)</option>
              {fornecedores.map((item) => (
                <option key={item.cod} value={item.cod}>
                  {item.cod} - {item.nome}
                </option>
              ))}
            </select>
          </div>
          <div className="form-field">
            <label>Quantidade</label>
            <input
              type="number"
              min="1"
              value={form.qtd}
              onChange={(e) => setForm({ ...form, qtd: e.target.value })}
            />
          </div>
          <div className="form-field">
            <label>Custo unitario</label>
            <input
              type="number"
              step="0.01"
              min="0"
              value={form.custoUnit}
              onChange={(e) => setForm({ ...form, custoUnit: e.target.value })}
            />
            <div className="hint">Valor de compra usado para recalcular o custo medio do produto.</div>
          </div>
          <div className="form-field">
            <label>Filial</label>
            <input
              value={form.filial}
              onChange={(e) => setForm({ ...form, filial: e.target.value })}
            />
          </div>
          <div className="form-field">
            <label>Vencimento AP (dias)</label>
            <input
              type="number"
              min="1"
              value={form.vencDias}
              onChange={(e) => setForm({ ...form, vencDias: e.target.value })}
            />
            <div className="hint">Usado somente quando houver fornecedor e geracao de AP.</div>
          </div>
          <div className="form-field">
            <label>&nbsp;</label>
            <button className="btn" onClick={onConsultarProduto} disabled={loading}>
              Consultar produto
            </button>
          </div>
          <div className="form-field">
            <label>&nbsp;</label>
            <button className="btn primary" onClick={onLancarEntrada} disabled={loading}>
              Lançar entrada
            </button>
          </div>
        </div>

        {fornecedorResultados.length > 0 && (
          <>
            <div className="section-title">Sugestoes de fornecedor</div>
            <div className="table-scroller">
              <table className="table mt-12 compact">
                <thead>
                  <tr>
                    <th>Codigo</th>
                    <th>Nome</th>
                    <th>Documento</th>
                    <th>Acoes</th>
                  </tr>
                </thead>
                <tbody>
                  {fornecedorResultados.map((item) => (
                    <tr key={item.cod}>
                      <td>{item.cod}</td>
                      <td>{item.nome}</td>
                      <td>{item.doc ?? "-"}</td>
                      <td>
                        <button
                          className="btn"
                          onClick={() => {
                            setForm((current) => ({ ...current, fornecedorCod: item.cod }));
                            setFornecedorQuery(item.nome || item.cod);
                            setFornecedorResultados([]);
                          }}
                        >
                          Usar fornecedor
                        </button>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </>
        )}

        {produtoResultados.length > 0 && (
          <>
            <div className="section-title">Sugestoes de produto</div>
            <div className="table-scroller">
              <table className="table mt-12 compact">
                <thead>
                  <tr>
                    <th>Codigo</th>
                    <th>Descricao</th>
                    <th>Preco</th>
                    <th>CM</th>
                    <th>Estoque</th>
                    <th>Acoes</th>
                  </tr>
                </thead>
                <tbody>
                  {produtoResultados.map((item) => (
                    <tr key={item.cod}>
                      <td>{item.cod}</td>
                      <td>{item.desc}</td>
                      <td>{formatCurrency(item.preco)}</td>
                      <td>{formatCurrency(item.cm)}</td>
                      <td>{item.estoque}</td>
                      <td>
                        <button
                          className="btn"
                          onClick={() => {
                            setForm((current) => ({ ...current, cod: item.cod }));
                            setProdutoQuery(item.desc || item.cod);
                            setProdutoResultados([]);
                          }}
                        >
                          Usar produto
                        </button>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </>
        )}

        {(beforeSnap || afterSnap) && (
          <>
            <div className="section-title">Antes e depois do custo medio</div>
            <div className="detail-grid mt-12">
              <div className="card soft">
                <div className="kpi-label">Produto</div>
                <div className="kpi">{(afterSnap ?? beforeSnap)?.B1_COD ?? "-"}</div>
                <div className="hint">{(afterSnap ?? beforeSnap)?.B1_DESC ?? "-"}</div>
              </div>
              <div className="card soft">
                <div className="kpi-label">CM antes</div>
                <div className="kpi">{formatCurrency(beforeSnap?.B1_CM ?? 0)}</div>
                <div className="hint">Base consultada antes da entrada</div>
              </div>
              <div className="card soft">
                <div className="kpi-label">CM depois</div>
                <div className="kpi">{formatCurrency(afterSnap?.B1_CM ?? beforeSnap?.B1_CM ?? 0)}</div>
                <div className="hint">B1_CM atualizado no estoque</div>
              </div>
              <div className="card soft">
                <div className="kpi-label">Estoque antes</div>
                <div className="kpi">{beforeSnap?.B1_ESTOQUE ?? "-"}</div>
                <div className="hint">Disponivel {beforeSnap?.DISPONIVEL ?? "-"}</div>
              </div>
              <div className="card soft">
                <div className="kpi-label">Estoque depois</div>
                <div className="kpi">{afterSnap?.B1_ESTOQUE ?? beforeSnap?.B1_ESTOQUE ?? "-"}</div>
                <div className="hint">Disponivel {afterSnap?.DISPONIVEL ?? "-"}</div>
              </div>
              <div className="card soft">
              <div className="kpi-label">Valor da entrada</div>
                <div className="kpi">
                  {formatCurrency(toNumber(form.qtd, 0) * toNumber(form.custoUnit, 0))}
                </div>
                <div className="hint">
                  {form.fornecedorCod ? "Com AP vinculado ao fornecedor" : "Sem AP automatico"}
                </div>
                {form.fornecedorCod ? (
                  <div className="mt-12">
                    <button
                      className="btn"
                      onClick={() =>
                        navigate(
                          `/financeiro/ap?status=ABERTO&q=${encodeURIComponent(
                            `ENTRADA:${(afterSnap ?? beforeSnap)?.B1_COD ?? form.cod.trim()}`
                          )}`
                        )
                      }
                    >
                      Abrir AP da entrada
                    </button>
                    <button
                      className="btn mt-12"
                      onClick={() => {
                        const next = new URLSearchParams(searchParams);
                        next.set("fornecedor", form.fornecedorCod);
                        next.set("produto", (afterSnap ?? beforeSnap)?.B1_COD ?? form.cod.trim());
                        setSearchParams(next);
                      }}
                    >
                      Fixar contexto
                    </button>
                  </div>
                ) : null}
              </div>
            </div>
          </>
        )}

        {extrato.length > 0 && (
          <>
            <div className="section-title">Ultimos movimentos SD3 do produto</div>
            <div className="table-scroller">
              <table className="table mt-12 compact">
                <thead>
                  <tr>
                    <th>ID</th>
                    <th>Data</th>
                    <th>Tipo</th>
                    <th>Qtd</th>
                    <th>Custo Unit</th>
                    <th>Valor</th>
                    <th>Origem</th>
                    <th>Usuario</th>
                  </tr>
                </thead>
                <tbody>
                  {extrato.map((item) => (
                    <tr key={item.ID}>
                      <td>{item.ID}</td>
                      <td>{item.D3_DATA}</td>
                      <td>{item.D3_TIPO}</td>
                      <td>{item.D3_QTD}</td>
                      <td>{formatCurrency(item.D3_CUSTO_UNIT)}</td>
                      <td>{formatCurrency(item.D3_VALOR)}</td>
                      <td>{item.D3_ORIGEM}</td>
                      <td>{item.D3_USUARIO ?? "-"}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </>
        )}
      </div>
    </>
  );
}
