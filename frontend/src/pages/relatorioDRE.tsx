import { useEffect, useMemo, useState } from "react";
import { Toolbar } from "../components/Toolbar";
import { DataTable, type Column, type SortDir } from "../components/DataTable";
import { Pager } from "../components/Pager";
import { PageHero } from "../components/PageHero";
import { getFilial, onFilialChange } from "../state/filial";
import { obterDre, type DreResponse, type DreLinha } from "../api/relatorios/dre";
import reportsIcon from "../assets/shell-icons/reports.png";
import dreBg from "../assets/hero-backgrounds/dre.png";

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

export function RelatorioDRE() {
  const [filialView, setFilialView] = useState(getFilial());
  const [de, setDe] = useState("");
  const [ate, setAte] = useState("");
  const [q, setQ] = useState("");

  const [loading, setLoading] = useState(false);
  const [err, setErr] = useState<string | null>(null);
  const [dre, setDre] = useState<DreResponse | null>(null);

  const [page, setPage] = useState(1);
  const [pageSize, setPageSize] = useState(10);

  const [sortKey, setSortKey] = useState("grupo");
  const [sortDir, setSortDir] = useState<SortDir>("asc");

  function getErrorMessage(error: unknown, fallback: string): string {
    if (error instanceof Error && error.message) return error.message;
    return fallback;
  }

  async function load() {
    setErr(null);
    setLoading(true);
    try {
      const filial = getFilial();
      const data = await obterDre({ filial, de: de || null, ate: ate || null });
      setDre(data);
      setPage(1);
    } catch (error: unknown) {
      setErr(getErrorMessage(error, "Erro ao carregar DRE"));
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

  const rows = useMemo(() => {
    const all = dre?.linhas ?? [];
    const query = q.trim().toLowerCase();
    if (!query) return all;
    return all.filter((x) =>
      toStringValue(x.grupo ?? (x as Record<string, unknown>).Grupo, "").toLowerCase().includes(query)
    );
  }, [dre, q]);

  const totalPages = useMemo(
    () => Math.max(1, Math.ceil(rows.length / pageSize)),
    [rows.length, pageSize]
  );

  const pagedRows = useMemo(() => {
    const safePage = Math.min(Math.max(1, page), totalPages);
    const start = (safePage - 1) * pageSize;
    return rows.slice(start, start + pageSize);
  }, [rows, page, pageSize, totalPages]);

  const columns: Column<DreLinha>[] = useMemo(
    () => [
      {
        key: "grupo",
        header: "Grupo",
        sortable: true,
        value: (x) => toStringValue(x.grupo ?? (x as Record<string, unknown>).Grupo, "-"),
      },
      {
        key: "valor",
        header: "Valor",
        sortable: true,
        align: "right",
        value: (x) => toNumber(x.valor ?? (x as Record<string, unknown>).Valor, 0),
        render: (x) => formatCurrency(x.valor ?? (x as Record<string, unknown>).Valor),
      },
    ],
    []
  );

  return (
    <>
      <PageHero
        icon={reportsIcon}
        backgroundImage={dreBg}
        backgroundPosition="center 26%"
        eyebrow="Relatorios gerenciais"
        title="DRE"
        description="Visao consolidada do resultado por periodo, com leitura rapida de grupos e total acumulado."
        metrics={[
          { label: "Filial", value: filialView },
          { label: "Linhas", value: String(rows.length) },
          { label: "Total", value: dre ? formatCurrency(dre.total) : "Aguardando" },
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
              placeholder="Filtrar grupo..."
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
          </>
        }
      />

      {err && <div className="alert mt-12">{err}</div>}

      <div className="section-title">Resumo</div>
      {dre && (
        <div className="stats-grid">
          <div className="stat-card">
            <div>
              <div className="kpi-label">Total</div>
              <div className="kpi">{formatCurrency(dre.total)}</div>
            </div>
            <div className="stat-icon success">R$</div>
          </div>
        </div>
      )}

      <div className="row-between mt-12">
        <Pager
          page={page}
          totalPages={totalPages}
          pageSize={pageSize}
          totalItems={rows.length}
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
        emptyText="Nenhuma linha no periodo."
      />
      </div>
    </>
  );
}
