import { useEffect, useMemo, useState } from "react";
import { Toolbar } from "../components/Toolbar";
import { DataTable, type Column, type SortDir } from "../components/DataTable";
import { Pager } from "../components/Pager";
import { PageHero } from "../components/PageHero";
import { listarAuditoria, type LogItem } from "../api/auditoria";
import usersIcon from "../assets/shell-icons/users.png";
import auditoriaBg from "../assets/hero-backgrounds/auditoria.jpg";

function toStringValue(value: unknown, fallback = ""): string {
  if (value === null || value === undefined) return fallback;
  const s = String(value).trim();
  return s ? s : fallback;
}

function normalize(v: unknown) {
  if (v === null || v === undefined) return "";
  if (typeof v === "boolean") return v ? "1" : "0";
  if (typeof v === "number") return String(v).padStart(20, "0");
  return String(v).toLowerCase().trim();
}

function getErrorMessage(error: unknown, fallback: string): string {
  if (error instanceof Error && error.message) return error.message;
  return fallback;
}

export function AuditoriaList() {
  const [q, setQ] = useState("");
  const [loading, setLoading] = useState(false);
  const [err, setErr] = useState<string | null>(null);
  const [items, setItems] = useState<LogItem[]>([]);

  const [page, setPage] = useState(1);
  const [pageSize, setPageSize] = useState(10);

  const [sortKey, setSortKey] = useState("id");
  const [sortDir, setSortDir] = useState<SortDir>("desc");

  async function load() {
    setErr(null);
    setLoading(true);
    try {
      const data = await listarAuditoria();
      setItems(data);
    } catch (error: unknown) {
      setErr(getErrorMessage(error, "Erro ao carregar auditoria"));
    } finally {
      setLoading(false);
    }
  }

  useEffect(() => {
    load();
  }, []);

  const filtered = useMemo(() => {
    const query = q.trim().toLowerCase();
    if (!query) return items;
    return items.filter((x) => {
      const usuario = toStringValue(x.L_USUARIO, "");
      const acao = toStringValue(x.L_ACAO, "");
      const data = toStringValue(x.L_DATA, "");
      const id = String(x.ID ?? "");
      return [usuario, acao, data, id].some((v) => v.toLowerCase().includes(query));
    });
  }, [items, q]);

  const columns: Column<LogItem>[] = useMemo(
    () => [
      { key: "id", header: "ID", sortable: true, value: (x) => x.ID ?? 0 },
      { key: "usuario", header: "Usuario", sortable: true, value: (x) => toStringValue(x.L_USUARIO, "-") },
      { key: "acao", header: "Acao", sortable: true, value: (x) => toStringValue(x.L_ACAO, "-") },
      { key: "data", header: "Data", sortable: true, value: (x) => toStringValue(x.L_DATA, "-"), className: "hide-sm" },
    ],
    []
  );

  const sorted = useMemo(() => {
    const col = columns.find((c) => c.key === sortKey);
    const valueFn = col?.value ?? ((r: LogItem) => (r as Record<string, unknown>)[sortKey]);
    const arr = [...filtered];
    arr.sort((a, b) => {
      const av = normalize(valueFn(a));
      const bv = normalize(valueFn(b));
      if (av < bv) return sortDir === "asc" ? -1 : 1;
      if (av > bv) return sortDir === "asc" ? 1 : -1;
      return 0;
    });
    return arr;
  }, [filtered, columns, sortKey, sortDir]);

  const totalPages = useMemo(
    () => Math.max(1, Math.ceil(sorted.length / pageSize)),
    [sorted.length, pageSize]
  );

  const pagedRows = useMemo(() => {
    const safePage = Math.min(Math.max(1, page), totalPages);
    const start = (safePage - 1) * pageSize;
    return sorted.slice(start, start + pageSize);
  }, [sorted, page, pageSize, totalPages]);

  return (
    <>
      <PageHero
        icon={usersIcon}
        backgroundImage={auditoriaBg}
        backgroundPosition="center 26%"
        eyebrow="Governanca"
        title="Auditoria operacional"
        description="Rastreie usuario, acao e data das operacoes expostas pelo backend para leitura administrativa."
        metrics={[
          { label: "Registros", value: String(sorted.length) },
          { label: "Busca", value: q ? "Ativa" : "Nenhuma" },
          { label: "Fonte", value: "/auditoria" },
        ]}
      />

      <div className="card">
      <Toolbar
        left={<div className="hint">Auditoria (ultimos 200 registros)</div>}
        right={
          <>
            <input
              className="input minw-240"
              value={q}
              onChange={(e) => setQ(e.target.value)}
              placeholder="Buscar por usuario, acao..."
            />
            <button className="btn" onClick={load} disabled={loading}>
              Atualizar
            </button>
            <button
              className="btn ghost"
              onClick={() => setQ("")}
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
            <div className="kpi-label">Registros (filtrados)</div>
            <div className="kpi">{sorted.length}</div>
          </div>
          <div className="stat-icon">LOG</div>
        </div>
        <div className="stat-card">
          <div>
            <div className="kpi-label">Busca</div>
            <div className="kpi">{q ? "Ativa" : "Nenhuma"}</div>
          </div>
          <div className="stat-icon solid">SR</div>
        </div>
        <div className="stat-card">
          <div>
            <div className="kpi-label">Fonte</div>
            <div className="kpi">/auditoria</div>
          </div>
          <div className="stat-icon success">API</div>
        </div>
      </div>

      <div className="row-between mt-12">
        <Pager
          page={page}
          totalPages={totalPages}
          pageSize={pageSize}
          totalItems={sorted.length}
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
        emptyText="Nenhum registro encontrado."
      />
      </div>
    </>
  );
}
