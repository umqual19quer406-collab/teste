import { useEffect, useMemo, useState } from "react";
import { useNavigate, useSearchParams } from "react-router-dom";
import { Toolbar } from "../components/Toolbar";
import { Pager } from "../components/Pager";
import { DataTable, type Column, type SortDir } from "../components/DataTable";
import { PageHero } from "../components/PageHero";
import { getFilial, onFilialChange } from "../state/filial";
import { listarAR, receberAR, baixarAR, type ArTitulo } from "../api/financeiro/ar";
import { listarContasCaixa, type CaixaConta } from "../api/financeiro/caixa";
import receivablesIcon from "../assets/shell-icons/receivables.png";
import receivablesBg from "../assets/hero-backgrounds/receivables.jpg";

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

function getId(item: ArTitulo) {
  return toNumber(item.ID ?? (item as Record<string, unknown>).id);
}

function getStatus(item: ArTitulo) {
  return toStringValue(item.E1_STATUS ?? (item as Record<string, unknown>).status, "ABERTO");
}

function getMovId(item: ArTitulo) {
  return toNumber(item.E1_SE5_ID ?? (item as Record<string, unknown>).se5_id, 0);
}

function getSortValue(item: ArTitulo, key: string) {
  switch (key) {
    case "id":
      return getId(item);
    case "cliente":
      return toStringValue(item.E1_CLIENTE ?? (item as Record<string, unknown>).cliente, "-");
    case "valor":
      return toNumber(item.E1_VALOR ?? (item as Record<string, unknown>).valor, 0);
    case "venc":
      return toStringValue(item.E1_VENC ?? (item as Record<string, unknown>).venc, "-");
    case "status":
      return getStatus(item);
    case "ref":
      return toStringValue(item.E1_REF ?? (item as Record<string, unknown>).ref, "-");
    case "mov":
      return getMovId(item);
    default:
      return (item as Record<string, unknown>)[key];
  }
}

export function FinanceiroAR() {
  const navigate = useNavigate();
  const [searchParams, setSearchParams] = useSearchParams();
  const [filialView, setFilialView] = useState(getFilial());
  const [status, setStatus] = useState("ABERTO");
  const [q, setQ] = useState("");

  const [loading, setLoading] = useState(false);
  const [err, setErr] = useState<string | null>(null);
  const [okMsg, setOkMsg] = useState<string | null>(null);
  const [items, setItems] = useState<ArTitulo[]>([]);

  const [contas, setContas] = useState<CaixaConta[]>([]);
  const [contaId, setContaId] = useState<number | "">("");

  const [page, setPage] = useState(1);
  const [pageSize, setPageSize] = useState(10);

  const [sortKey, setSortKey] = useState("id");
  const [sortDir, setSortDir] = useState<SortDir>("desc");
  const alertFilter = searchParams.get("alert") ?? "";

  const alertLabelMap: Record<string, string> = {
    ar_overdue: "Exibindo apenas titulos de AR vencidos.",
    ar_due_today: "Exibindo apenas titulos de AR com vencimento hoje.",
    ar_due_soon: "Exibindo apenas titulos de AR que vencem nos proximos 3 dias.",
  };

  function getErrorMessage(error: unknown, fallback: string): string {
    if (error instanceof Error && error.message) return error.message;
    return fallback;
  }

  async function load() {
    setErr(null);
    setLoading(true);
    try {
      const filial = getFilial();
      const data = await listarAR({ filial, status });
      setItems(data);
      setQ("");
      setPage(1);
    } catch (error: unknown) {
      setErr(getErrorMessage(error, "Erro ao carregar AR"));
    } finally {
      setLoading(false);
    }
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

  async function receber(item: ArTitulo) {
    setErr(null);
    setOkMsg(null);
    setLoading(true);
    try {
      if (!contaId) throw new Error("Selecione a conta de caixa.");
      const result = await receberAR({ titulo_id: getId(item), conta_id: Number(contaId) });
      const se5Id = toNumber(result.se5_id ?? result.mov_id, 0);
      setOkMsg(
        se5Id > 0
          ? `Recebimento realizado. Movimento de caixa gerado: ${se5Id}.`
          : "Recebimento realizado com sucesso."
      );
      await load();
    } catch (error: unknown) {
      setErr(getErrorMessage(error, "Erro ao receber AR"));
    } finally {
      setLoading(false);
    }
  }

  async function baixar(item: ArTitulo) {
    setErr(null);
    setOkMsg(null);
    setLoading(true);
    try {
      if (!contaId) throw new Error("Selecione a conta de caixa.");
      const result = await baixarAR({ titulo_id: getId(item), conta_id: Number(contaId) });
      const se5Id = toNumber(result.se5_id ?? result.mov_id, 0);
      setOkMsg(
        se5Id > 0
          ? `Baixa realizada. Movimento de caixa vinculado: ${se5Id}.`
          : "Baixa realizada com sucesso."
      );
      await load();
    } catch (error: unknown) {
      setErr(getErrorMessage(error, "Erro ao baixar AR"));
    } finally {
      setLoading(false);
    }
  }

  useEffect(() => {
    load();
    loadContas();

    const unsub = onFilialChange((novaFilial) => {
      setFilialView(novaFilial);
      setErr(null);
      setStatus("ABERTO");
      setContaId("");
      setQ("");
      setPage(1);
      load();
      loadContas();
    });
    return unsub;
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  useEffect(() => {
    if (!alertFilter) return;
    setStatus("ABERTO");
    setQ("");
    setPage(1);
  }, [alertFilter]);

  const columns: Column<ArTitulo>[] = [
      { key: "id", header: "ID", sortable: true, value: (x) => getId(x) },
      {
        key: "cliente",
        header: "Cliente",
        sortable: true,
        value: (x) => toStringValue(x.E1_CLIENTE ?? (x as Record<string, unknown>).cliente, "-"),
      },
      {
        key: "valor",
        header: "Valor",
        sortable: true,
        align: "right",
        value: (x) => toNumber(x.E1_VALOR ?? (x as Record<string, unknown>).valor, 0),
        render: (x) => formatCurrency(x.E1_VALOR ?? (x as Record<string, unknown>).valor),
      },
      {
        key: "venc",
        header: "Venc.",
        sortable: true,
        className: "hide-sm",
        value: (x) => toStringValue(x.E1_VENC ?? (x as Record<string, unknown>).venc, "-"),
      },
      {
        key: "status",
        header: "Status",
        sortable: true,
        className: "hide-sm",
        value: (x) => getStatus(x),
      },
      {
        key: "ref",
        header: "Ref",
        sortable: true,
        className: "hide-sm",
        value: (x) => toStringValue(x.E1_REF ?? (x as Record<string, unknown>).ref, "-"),
      },
      {
        key: "mov",
        header: "Mov. Caixa",
        sortable: true,
        className: "hide-sm",
        value: (x) => getMovId(x),
        render: (x) => {
          const movId = getMovId(x);
          return movId > 0 ? movId : "-";
        },
      },
      {
        key: "acoes",
        header: "Acoes",
        render: (x) => {
          const s = getStatus(x);
          const movId = getMovId(x);
          const disabled = loading || s !== "ABERTO";
          return (
            <div className="row gap-10">
              <button className="btn primary" disabled={disabled} onClick={() => receber(x)}>
                Receber
              </button>
              <button className="btn" disabled={disabled} onClick={() => baixar(x)}>
                Baixar
              </button>
              <button
                className="btn ghost"
                disabled={movId <= 0}
                onClick={() => navigate(`/financeiro/categorias?mov_id=${movId}`)}
              >
                Categorizar
              </button>
            </div>
          );
        },
      },
  ];

  function normalize(v: unknown) {
    if (v === null || v === undefined) return "";
    if (typeof v === "boolean") return v ? "1" : "0";
    if (typeof v === "number") return String(v).padStart(20, "0");
    return String(v).toLowerCase().trim();
  }

  const filteredItems = useMemo(() => {
    const query = q.trim().toLowerCase();
    return items.filter((x) => {
      if (alertFilter) {
        const venc = new Date(toStringValue(x.E1_VENC ?? (x as Record<string, unknown>).venc, ""));
        if (Number.isNaN(venc.getTime())) return false;

        const today = new Date();
        today.setHours(0, 0, 0, 0);
        venc.setHours(0, 0, 0, 0);
        const diffDays = Math.round((venc.getTime() - today.getTime()) / 86400000);

        if (alertFilter === "ar_overdue" && diffDays >= 0) return false;
        if (alertFilter === "ar_due_today" && diffDays !== 0) return false;
        if (alertFilter === "ar_due_soon" && (diffDays < 1 || diffDays > 3)) return false;
      }
      if (!query) return true;
      const cliente = toStringValue(x.E1_CLIENTE ?? (x as Record<string, unknown>).cliente, "");
      const ref = toStringValue(x.E1_REF ?? (x as Record<string, unknown>).ref, "");
      const id = String(getId(x));
      const movId = String(getMovId(x));
      return [cliente, ref, id, movId].some((v) => v.toLowerCase().includes(query));
    });
  }, [items, q, alertFilter]);

  const sortedItems = useMemo(() => {
    const arr = [...filteredItems];
    arr.sort((a, b) => {
      const av = normalize(getSortValue(a, sortKey));
      const bv = normalize(getSortValue(b, sortKey));
      if (av < bv) return sortDir === "asc" ? -1 : 1;
      if (av > bv) return sortDir === "asc" ? 1 : -1;
      return 0;
    });
    return arr;
  }, [filteredItems, sortKey, sortDir]);

  const totalPages = useMemo(
    () => Math.max(1, Math.ceil(sortedItems.length / pageSize)),
    [sortedItems.length, pageSize]
  );

  const pagedRows = useMemo(() => {
    const safePage = Math.min(Math.max(1, page), totalPages);
    const start = (safePage - 1) * pageSize;
    return sortedItems.slice(start, start + pageSize);
  }, [sortedItems, page, pageSize, totalPages]);

  const totalValor = useMemo(
    () => filteredItems.reduce((acc, x) => acc + toNumber(x.E1_VALOR ?? (x as Record<string, unknown>).valor, 0), 0),
    [filteredItems]
  );

  return (
    <>
      <PageHero
        icon={receivablesIcon}
        backgroundImage={receivablesBg}
        backgroundPosition="center 40%"
        eyebrow="Financeiro"
        title="Contas a receber"
        description="Titulos abertos, recebimento operacional e baixa assistida com conta de caixa vinculada."
        metrics={[
          { label: "Filial", value: filialView },
          { label: "Status", value: status },
          { label: "Valor filtrado", value: formatCurrency(totalValor) },
        ]}
      />

      <div className="card">
      {alertFilter && (
        <div className="context-banner">
          <div>
            <div className="context-banner-title">Filtro aplicado por alerta</div>
            <div className="context-banner-text">{alertLabelMap[alertFilter] ?? "Filtro contextual de alerta ativo."}</div>
          </div>
          <button
            type="button"
            className="btn ghost"
            onClick={() => {
              const next = new URLSearchParams(searchParams);
              next.delete("alert");
              setSearchParams(next);
            }}
          >
            Limpar filtro do alerta
          </button>
        </div>
      )}

      <Toolbar
        left={
          <div className="hint">
            Filial: <b>{filialView}</b> | Status: <b>{status}</b>
          </div>
        }
        right={
          <>
            <input
              className="input minw-240"
              value={q}
              onChange={(e) => {
                setQ(e.target.value);
                setPage(1);
              }}
              placeholder="Buscar por cliente, ref ou ID..."
            />

            <select className="select" value={status} onChange={(e) => { setStatus(e.target.value); setPage(1); }}>
              <option value="ABERTO">ABERTO</option>
              <option value="BAIXADO">BAIXADO</option>
              <option value="CANCELADO">CANCELADO</option>
            </select>

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

            <button type="button" className="btn" onClick={load} disabled={loading}>
              Aplicar
            </button>
            <button
              type="button"
              className="btn ghost"
              onClick={() => {
                setQ("");
                setStatus("ABERTO");
                setPage(1);
              }}
              disabled={loading}
            >
              Limpar
            </button>
          </>
        }
      />

      {okMsg && <div className="alert alert-success mt-12">{okMsg}</div>}
      {err && <div className="alert mt-12">{err}</div>}

      <div className="section-title">Resumo</div>
      <div className="stats-grid">
        <div className="stat-card">
          <div>
            <div className="kpi-label">Titulos (filtrados)</div>
            <div className="kpi">{filteredItems.length}</div>
          </div>
          <div className="stat-icon">AR</div>
        </div>
        <div className="stat-card">
          <div>
            <div className="kpi-label">Valor total (filtrado)</div>
            <div className="kpi">{formatCurrency(totalValor)}</div>
          </div>
          <div className="stat-icon success">R$</div>
        </div>
        <div className="stat-card">
          <div>
            <div className="kpi-label">Status atual</div>
            <div className="kpi">{status}</div>
          </div>
          <div className="stat-icon solid">ST</div>
        </div>
      </div>

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
        emptyText="Nenhum titulo encontrado."
      />
      </div>
    </>
  );
}
