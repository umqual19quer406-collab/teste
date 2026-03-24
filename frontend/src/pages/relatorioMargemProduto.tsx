import { useEffect, useMemo, useState } from "react";
import { Toolbar } from "../components/Toolbar";
import { DataTable, type Column, type SortDir } from "../components/DataTable";
import { Pager } from "../components/Pager";
import { PageHero } from "../components/PageHero";
import { getFilial, onFilialChange } from "../state/filial";
import { obterMargemProduto, type MargemProdutoRow } from "../api/relatorios/margem-produto";
import reportsIcon from "../assets/shell-icons/reports.png";
import marginBg from "../assets/hero-backgrounds/margin.webp";

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

export function RelatorioMargemProduto() {
  const [filialView, setFilialView] = useState(getFilial());
  const [de, setDe] = useState("");
  const [ate, setAte] = useState("");
  const [q, setQ] = useState("");

  const [loading, setLoading] = useState(false);
  const [err, setErr] = useState<string | null>(null);
  const [rows, setRows] = useState<MargemProdutoRow[]>([]);

  const [page, setPage] = useState(1);
  const [pageSize, setPageSize] = useState(10);

  const [sortKey, setSortKey] = useState("margem");
  const [sortDir, setSortDir] = useState<SortDir>("desc");

  function getErrorMessage(error: unknown, fallback: string): string {
    if (error instanceof Error && error.message) return error.message;
    return fallback;
  }

  async function load() {
    setErr(null);
    setLoading(true);
    try {
      const filial = getFilial();
      const data = await obterMargemProduto({ filial, de: de || null, ate: ate || null });
      setRows(Array.isArray(data) ? data : []);
      setPage(1);
    } catch (error: unknown) {
      setErr(getErrorMessage(error, "Erro ao carregar margem por produto"));
    } finally {
      setLoading(false);
    }
  }

  useEffect(() => {
    load();

    const unsub = onFilialChange((novaFilial) => {
      setFilialView(novaFilial);
      setErr(null);
      setQ("");
      setPage(1);
      load();
    });
    return unsub;
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  const filtered = useMemo(() => {
    const query = q.trim().toLowerCase();
    if (!query) return rows;
    return rows.filter((x) => toStringValue(x.produto, "").toLowerCase().includes(query));
  }, [rows, q]);

  const totalPages = useMemo(
    () => Math.max(1, Math.ceil(filtered.length / pageSize)),
    [filtered.length, pageSize]
  );

  const pagedRows = useMemo(() => {
    const safePage = Math.min(Math.max(1, page), totalPages);
    const start = (safePage - 1) * pageSize;
    return filtered.slice(start, start + pageSize);
  }, [filtered, page, pageSize, totalPages]);

  const totalReceita = useMemo(() => filtered.reduce((acc, r) => acc + toNumber(r.receita, 0), 0), [filtered]);
  const totalCmv = useMemo(() => filtered.reduce((acc, r) => acc + toNumber(r.cmv, 0), 0), [filtered]);
  const totalMargem = useMemo(() => filtered.reduce((acc, r) => acc + toNumber(r.margem, 0), 0), [filtered]);

  const columns: Column<MargemProdutoRow>[] = useMemo(
    () => [
      { key: "produto", header: "Produto", sortable: true },
      {
        key: "receita",
        header: "Receita",
        sortable: true,
        align: "right",
        render: (x) => formatCurrency(x.receita),
      },
      {
        key: "cmv",
        header: "CMV",
        sortable: true,
        align: "right",
        render: (x) => formatCurrency(x.cmv),
      },
      {
        key: "margem",
        header: "Margem",
        sortable: true,
        align: "right",
        render: (x) => formatCurrency(x.margem),
      },
    ],
    []
  );

  return (
    <>
      <PageHero
        icon={reportsIcon}
        backgroundImage={marginBg}
        backgroundPosition="center 36%"
        eyebrow="Relatorios gerenciais"
        title="Margem por produto"
        description="Leitura sintetica da relacao entre receita, CMV e margem para apoiar priorizacao comercial e estoque."
        metrics={[
          { label: "Filial", value: filialView },
          { label: "Receita", value: formatCurrency(totalReceita) },
          { label: "Margem", value: formatCurrency(totalMargem) },
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
            <input
              className="input minw-240"
              value={q}
              onChange={(e) => { setQ(e.target.value); setPage(1); }}
              placeholder="Filtrar produto..."
            />
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
            <button type="button" className="btn" onClick={load} disabled={loading}>
              Aplicar
            </button>
            <button
              type="button"
              className="btn ghost"
              onClick={() => {
                setQ("");
                setDe("");
                setAte("");
                setPage(1);
              }}
              disabled={loading}
            >
              Limpar
            </button>
          </>
        }
      />

      {err && <div className="alert mt-12">{err}</div>}

      <div className="section-title">Resumo</div>
      <div className="stats-grid">
        <div className="stat-card">
          <div>
            <div className="kpi-label">Receita</div>
            <div className="kpi">{formatCurrency(totalReceita)}</div>
          </div>
          <div className="stat-icon">R$</div>
        </div>
        <div className="stat-card">
          <div>
            <div className="kpi-label">CMV</div>
            <div className="kpi">{formatCurrency(totalCmv)}</div>
          </div>
          <div className="stat-icon solid">C</div>
        </div>
        <div className="stat-card">
          <div>
            <div className="kpi-label">Margem</div>
            <div className="kpi">{formatCurrency(totalMargem)}</div>
          </div>
          <div className="stat-icon success">M</div>
        </div>
      </div>

      <div className="row-between mt-12">
        <Pager
          page={page}
          totalPages={totalPages}
          pageSize={pageSize}
          totalItems={filtered.length}
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
        emptyText="Nenhum produto encontrado."
      />
      </div>
    </>
  );
}
