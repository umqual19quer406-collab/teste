import { useEffect, useMemo, useState } from "react";
import { useSearchParams } from "react-router-dom";
import { Toolbar } from "../components/Toolbar";
import { Pager } from "../components/Pager";
import { DataTable, type Column, type SortDir } from "../components/DataTable";
import { PageHero } from "../components/PageHero";
import { getFilial, onFilialChange } from "../state/filial";
import {
  listarContasCaixa,
  extratoCaixa,
  saldoCaixa,
  type CaixaConta,
  type CaixaMovimento,
  type CaixaSaldo,
} from "../api/financeiro/caixa";
import cashIcon from "../assets/shell-icons/cash.png";
import cashBg from "../assets/hero-backgrounds/cash.jpg";

function toNumber(value: unknown, fallback = 0): number {
  const n = Number(value);
  return Number.isFinite(n) ? n : fallback;
}

function toStringValue(value: unknown, fallback = ""): string {
  if (value === null || value === undefined) return fallback;
  const s = String(value).trim();
  return s ? s : fallback;
}

function formatCurrency(value: unknown) {
  return toNumber(value, 0).toLocaleString("pt-BR", { style: "currency", currency: "BRL" });
}

export function FinanceiroCaixa() {
  const [searchParams, setSearchParams] = useSearchParams();
  const [filialView, setFilialView] = useState(getFilial());
  const [contas, setContas] = useState<CaixaConta[]>([]);
  const [contaId, setContaId] = useState<number | "">("");

  const [de, setDe] = useState("");
  const [ate, setAte] = useState("");
  const [q, setQ] = useState(searchParams.get("q") ?? "");

  const [loading, setLoading] = useState(false);
  const [err, setErr] = useState<string | null>(null);
  const [saldo, setSaldo] = useState<CaixaSaldo | null>(null);
  const [movs, setMovs] = useState<CaixaMovimento[]>([]);

  const [page, setPage] = useState(1);
  const [pageSize, setPageSize] = useState(10);

  const [sortKey, setSortKey] = useState("data");
  const [sortDir, setSortDir] = useState<SortDir>("desc");

  function getErrorMessage(error: unknown, fallback: string): string {
    if (error instanceof Error && error.message) return error.message;
    return fallback;
  }

  async function loadContas() {
    setErr(null);
    try {
      const filial = getFilial();
      const data = await listarContasCaixa({ filial });
      setContas(data);
      if (!contaId && data.length > 0) {
        setContaId(toNumber(data[0].ID));
      }
    } catch (error: unknown) {
      setErr(getErrorMessage(error, "Erro ao carregar contas de caixa"));
    }
  }

  async function loadExtrato() {
    setErr(null);
    setLoading(true);
    try {
      if (!contaId) return;
      const filial = getFilial();
      const data = await extratoCaixa({
        filial,
        conta_id: Number(contaId),
        de: de || null,
        ate: ate || null,
      });
      setMovs(data);
      setPage(1);
    } catch (error: unknown) {
      setErr(getErrorMessage(error, "Erro ao carregar extrato"));
    } finally {
      setLoading(false);
    }
  }

  async function loadSaldo() {
    setErr(null);
    setLoading(true);
    try {
      if (!contaId) return;
      const filial = getFilial();
      const data = await saldoCaixa({
        filial,
        conta_id: Number(contaId),
        ate: ate || null,
      });
      setSaldo(data);
    } catch (error: unknown) {
      setErr(getErrorMessage(error, "Erro ao carregar saldo"));
    } finally {
      setLoading(false);
    }
  }

  useEffect(() => {
    loadContas();

    const unsub = onFilialChange((novaFilial) => {
      setFilialView(novaFilial);
      setErr(null);
      setContaId("");
      setMovs([]);
      setSaldo(null);
      setQ("");
      setPage(1);
      loadContas();
    });
    return unsub;
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  useEffect(() => {
    const nextQ = searchParams.get("q") ?? "";
    if (nextQ !== q) setQ(nextQ);
  }, [searchParams, q]);

  useEffect(() => {
    if (!contaId) return;
    loadExtrato();
    loadSaldo();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [contaId]);

  const columns: Column<CaixaMovimento>[] = useMemo(
    () => [
      {
        key: "data",
        header: "Data",
        sortable: true,
        value: (x) => toStringValue(x.E5_DATA ?? (x as Record<string, unknown>).data, "-"),
      },
      {
        key: "tipo",
        header: "Tipo",
        sortable: true,
        value: (x) => toStringValue(x.E5_TIPO ?? (x as Record<string, unknown>).tipo, "-"),
      },
      {
        key: "valor",
        header: "Valor",
        sortable: true,
        align: "right",
        value: (x) => toNumber(x.E5_VALOR ?? (x as Record<string, unknown>).valor, 0),
        render: (x) => formatCurrency(x.E5_VALOR ?? (x as Record<string, unknown>).valor),
      },
      {
        key: "saldo",
        header: "Saldo",
        sortable: true,
        align: "right",
        value: (x) => toNumber(x.E5_SALDO_ACUMULADO ?? (x as Record<string, unknown>).saldo, 0),
        render: (x) => formatCurrency(x.E5_SALDO_ACUMULADO ?? (x as Record<string, unknown>).saldo),
      },
      {
        key: "hist",
        header: "Historico",
        sortable: true,
        className: "hide-sm",
        value: (x) => toStringValue(x.E5_HIST ?? (x as Record<string, unknown>).hist, "-"),
      },
      {
        key: "origem",
        header: "Origem",
        sortable: true,
        className: "hide-sm",
        value: (x) => {
          const tipo = toStringValue(x.E5_ORIGEM_TIPO ?? (x as Record<string, unknown>).origem_tipo, "");
          const id = toStringValue(x.E5_ORIGEM_ID ?? (x as Record<string, unknown>).origem_id, "");
          return [tipo, id].filter(Boolean).join("#") || "-";
        },
      },
      {
        key: "categoria",
        header: "Categoria",
        sortable: true,
        className: "hide-sm",
        value: (x) =>
          toStringValue(x.CATEG_NOME ?? (x as Record<string, unknown>).categoria, "-"),
      },
      {
        key: "usuario",
        header: "Usuario",
        sortable: true,
        className: "hide-sm",
        value: (x) => toStringValue(x.E5_USUARIO ?? (x as Record<string, unknown>).usuario, "-"),
      },
    ],
    []
  );

  function normalize(v: unknown) {
    if (v === null || v === undefined) return "";
    if (typeof v === "boolean") return v ? "1" : "0";
    if (typeof v === "number") return String(v).padStart(20, "0");
    return String(v).toLowerCase().trim();
  }

  const filteredItems = useMemo(() => {
    const query = q.trim().toLowerCase();
    if (!query) return movs;
    return movs.filter((x) => {
      const hist = toStringValue(x.E5_HIST ?? (x as Record<string, unknown>).hist, "");
      const origem = toStringValue(x.E5_ORIGEM_TIPO ?? (x as Record<string, unknown>).origem_tipo, "");
      const user = toStringValue(x.E5_USUARIO ?? (x as Record<string, unknown>).usuario, "");
      const cat = toStringValue(x.CATEG_NOME ?? (x as Record<string, unknown>).categoria, "");
      return [hist, origem, user, cat].some((v) => v.toLowerCase().includes(query));
    });
  }, [movs, q]);

  const sortedItems = useMemo(() => {
    const col = columns.find((c) => c.key === sortKey);
    const valueFn = col?.value ?? ((r: CaixaMovimento) => (r as Record<string, unknown>)[sortKey]);

    const arr = [...filteredItems];
    arr.sort((a, b) => {
      const av = normalize(valueFn(a));
      const bv = normalize(valueFn(b));
      if (av < bv) return sortDir === "asc" ? -1 : 1;
      if (av > bv) return sortDir === "asc" ? 1 : -1;
      return 0;
    });
    return arr;
  }, [filteredItems, columns, sortKey, sortDir]);

  const totalPages = useMemo(
    () => Math.max(1, Math.ceil(sortedItems.length / pageSize)),
    [sortedItems.length, pageSize]
  );

  const pagedRows = useMemo(() => {
    const safePage = Math.min(Math.max(1, page), totalPages);
    const start = (safePage - 1) * pageSize;
    return sortedItems.slice(start, start + pageSize);
  }, [sortedItems, page, pageSize, totalPages]);

  return (
    <>
      <PageHero
        icon={cashIcon}
        backgroundImage={cashBg}
        backgroundPosition="center 42%"
        eyebrow="Tesouraria"
        title="Caixa e extrato"
        description="Consulta de contas, composicao de saldo e rastreio completo das entradas e saidas da operacao."
        metrics={[
          { label: "Filial", value: filialView },
          { label: "Conta", value: contaId ? String(contaId) : "Nao definida" },
          { label: "Saldo", value: saldo ? formatCurrency(saldo.saldo) : "Aguardando" },
        ]}
      />

      <div className="card">
      <Toolbar
        left={
          <div className="hint">
            Filial: <b>{filialView}</b>
          </div>
        }
        right={
          <>
            <select
              className="select"
              value={contaId}
              onChange={(e) => setContaId(e.target.value ? Number(e.target.value) : "")}
            >
              <option value="">Conta de Caixa</option>
              {contas.map((c) => (
                <option key={c.ID} value={c.ID}>
                  {toStringValue(c.E5_NOME, "Conta")} ({toStringValue(c.E5_FILIAL, filialView)})
                </option>
              ))}
            </select>

            <input
              className="input"
              type="date"
              value={de}
              onChange={(e) => setDe(e.target.value)}
              aria-label="Data inicial"
            />
            <input
              className="input"
              type="date"
              value={ate}
              onChange={(e) => setAte(e.target.value)}
              aria-label="Data final"
            />

            <input
              className="input minw-240"
              value={q}
              onChange={(e) => {
                setQ(e.target.value);
                setPage(1);
              }}
              placeholder="Filtrar extrato (hist, origem, usuario...)"
            />

            <button
              type="button"
              className="btn"
              onClick={() => {
                const next = new URLSearchParams(searchParams);
                if (q.trim()) next.set("q", q.trim());
                else next.delete("q");
                setSearchParams(next);
                loadExtrato();
              }}
              disabled={loading}
            >
              Extrato
            </button>
            <button type="button" className="btn" onClick={loadSaldo} disabled={loading}>
              Saldo
            </button>
          </>
        }
      />

      {err && <div className="alert mt-12">{err}</div>}

      <div className="section-title">Resumo</div>
      {saldo && (
        <div className="stats-grid">
          <div className="stat-card">
            <div>
              <div className="kpi-label">Entradas</div>
              <div className="kpi">{formatCurrency(saldo.entradas)}</div>
            </div>
            <div className="stat-icon success">E</div>
          </div>
          <div className="stat-card">
            <div>
              <div className="kpi-label">Saidas</div>
              <div className="kpi">{formatCurrency(saldo.saidas)}</div>
            </div>
            <div className="stat-icon">S</div>
          </div>
          <div className="stat-card">
            <div>
              <div className="kpi-label">Saldo</div>
              <div className="kpi">{formatCurrency(saldo.saldo)}</div>
            </div>
            <div className="stat-icon solid">$</div>
          </div>
        </div>
      )}

      <div className="section-title">Extrato</div>

      <div className="row-between mt-12">
        <Pager
          page={page}
          totalPages={totalPages}
          pageSize={pageSize}
          totalItems={sortedItems.length}
          onPageChange={setPage}
          onPageSizeChange={(ps) => {
            setPageSize(ps);
            setPage(1);
          }}
          showPageSize
        />
      </div>

      <DataTable
        rows={pagedRows}
        columns={columns}
        sortKey={sortKey}
        sortDir={sortDir}
        className="compact"
        wrapperClassName="table-scroller"
        onSortChange={(k, d) => {
          setSortKey(k);
          setSortDir(d);
          setPage(1);
        }}
        loading={loading}
        emptyText="Nenhum movimento encontrado."
      />
      </div>
    </>
  );
}
