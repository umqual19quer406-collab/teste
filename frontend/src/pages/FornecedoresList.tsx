import { useEffect, useMemo, useState } from "react";
import { Link, useNavigate } from "react-router-dom";
import { Toolbar } from "../components/Toolbar";
import { Modal } from "../components/Modal";
import { ConfirmDialog } from "../components/ConfirmDialog";
import { Pager } from "../components/Pager";
import { DataTable, type Column, type SortDir } from "../components/DataTable";
import { PageHero } from "../components/PageHero";
import partnersIcon from "../assets/shell-icons/partners.png";
import suppliersBg from "../assets/hero-backgrounds/suppliers.webp";

import {
  listFornecedores,
  buscarFornecedores,
  createFornecedor,
  updateFornecedor,
  setFornecedorAtivo,
  type Fornecedor,
} from "../api/fornecedores";
import { getFilial, onFilialChange } from "../state/filial";

type FormState = {
  cod: string;
  nome: string;
  doc: string;
  email: string;
  fone: string;
  filial: string;
};

function emptyForm(): FormState {
  return {
    cod: "",
    nome: "",
    doc: "",
    email: "",
    fone: "",
    filial: getFilial(),
  };
}

type SortKey = "cod" | "nome" | "doc" | "ativo_sn";

export function FornecedoresList() {
  const navigate = useNavigate();
  const [filialView, setFilialView] = useState(getFilial());

  const [ativos, setAtivos] = useState(true);
  const [q, setQ] = useState("");

  const [loading, setLoading] = useState(false);
  const [err, setErr] = useState<string | null>(null);
  const [items, setItems] = useState<Fornecedor[]>([]);

  const [page, setPage] = useState(1);
  const [pageSize, setPageSize] = useState(10);

  const [sortKey, setSortKey] = useState<SortKey>("nome");
  const [sortDir, setSortDir] = useState<SortDir>("asc");

  const [modalOpen, setModalOpen] = useState(false);
  const [editingCod, setEditingCod] = useState<string | null>(null);
  const [form, setForm] = useState<FormState>(() => emptyForm());

  const [confirmOpen, setConfirmOpen] = useState(false);
  const [confirmFornecedor, setConfirmFornecedor] = useState<Fornecedor | null>(null);

  const modalTitle = useMemo(
    () => (editingCod ? `Editar Fornecedor: ${editingCod}` : "Novo Fornecedor"),
    [editingCod]
  );

  function getErrorMessage(error: unknown, fallback: string): string {
    if (error instanceof Error && error.message) return error.message;
    return fallback;
  }

  function askToggleAtivo(f: Fornecedor) {
    setConfirmFornecedor(f);
    setConfirmOpen(true);
  }

  async function load() {
    setErr(null);
    setLoading(true);
    try {
      const filial = getFilial();
      const data = await listFornecedores({ ativos, filial });
      setItems(data);
      setPage(1);
    } catch (error: unknown) {
      setErr(getErrorMessage(error, "Erro ao carregar"));
    } finally {
      setLoading(false);
    }
  }

  async function doSearch() {
    setErr(null);
    setLoading(true);
    try {
      if (!q.trim()) {
        await load();
        return;
      }
      const filial = getFilial();
      const data = await buscarFornecedores({ q: q.trim(), filial });
      setItems(data);
      setPage(1);
    } catch (error: unknown) {
      setErr(getErrorMessage(error, "Erro na busca"));
    } finally {
      setLoading(false);
    }
  }

  useEffect(() => {
    load();

    const unsub = onFilialChange((novaFilial) => {
      setFilialView(novaFilial);
      setQ("");
      setErr(null);

      setModalOpen(false);
      setEditingCod(null);
      setForm(emptyForm());

      setConfirmOpen(false);
      setConfirmFornecedor(null);

      setPage(1);
      load();
    });

    return unsub;
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  function openNew() {
    setEditingCod(null);
    setForm(emptyForm());
    setModalOpen(true);
  }

  function openEdit(f: Fornecedor) {
    setEditingCod(f.cod);
    setForm({
      cod: f.cod,
      nome: f.nome ?? "",
      doc: f.doc ?? "",
      email: f.email ?? "",
      fone: f.fone ?? "",
      filial: f.filial ?? getFilial(),
    });
    setModalOpen(true);
  }

  async function save() {
    setErr(null);
    setLoading(true);
    try {
      if (!form.cod.trim() || !form.nome.trim()) {
        throw new Error("Código e Nome são obrigatórios.");
      }

      if (editingCod) {
        await updateFornecedor(editingCod, {
          filial: form.filial,
          nome: form.nome,
          doc: form.doc || null,
          email: form.email || null,
          fone: form.fone || null,
        });
      } else {
        await createFornecedor({
          filial: form.filial,
          cod: form.cod,
          nome: form.nome,
          doc: form.doc || null,
          email: form.email || null,
          fone: form.fone || null,
        });
      }

      setModalOpen(false);
      await load();
    } catch (error: unknown) {
      setErr(getErrorMessage(error, "Erro ao salvar"));
    } finally {
      setLoading(false);
    }
  }

  async function toggleAtivo(f: Fornecedor) {
    setErr(null);
    setLoading(true);
    try {
      const ativoAtual = (f.ativo_sn ?? "S") === "S";
      await setFornecedorAtivo(f.cod, {
        ativo: !ativoAtual,
        filial: f.filial ?? getFilial(),
      });
      await load();
    } catch (error: unknown) {
      setErr(getErrorMessage(error, "Erro ao alterar ativo"));
    } finally {
      setLoading(false);
    }
  }

  function norm(v: unknown) {
    return (v ?? "").toString().toLowerCase().trim();
  }

  function getSortValue(item: Fornecedor, key: SortKey): unknown {
    if (key === "ativo_sn") return item.ativo_sn ?? "S";
    if (key === "cod") return item.cod;
    if (key === "nome") return item.nome;
    return item.doc;
  }

  const sortedItems = useMemo(() => {
    const arr = [...items];
    arr.sort((a, b) => {
      const av = norm(getSortValue(a, sortKey));
      const bv = norm(getSortValue(b, sortKey));

      if (av < bv) return sortDir === "asc" ? -1 : 1;
      if (av > bv) return sortDir === "asc" ? 1 : -1;

      return norm(a.cod).localeCompare(norm(b.cod));
    });
    return arr;
  }, [items, sortKey, sortDir]);

  const totalPages = useMemo(() => {
    return Math.max(1, Math.ceil(sortedItems.length / pageSize));
  }, [sortedItems.length, pageSize]);

  const pagedRows = useMemo(() => {
    const safePage = Math.min(Math.max(1, page), totalPages);
    const start = (safePage - 1) * pageSize;
    return sortedItems.slice(start, start + pageSize);
  }, [sortedItems, page, pageSize, totalPages]);

  const columns: Column<Fornecedor>[] = useMemo(
    () => [
      { key: "cod", header: "Código", sortable: true },
      { key: "nome", header: "Nome", sortable: true },
      { key: "doc", header: "Doc", sortable: true, className: "hide-sm" },
      {
        key: "ativo_sn",
        header: "Ativo",
        sortable: true,
        value: (f) => f.ativo_sn ?? "S",
        render: (f) =>
          (f.ativo_sn ?? "S") === "S" ? (
            <span className="badge success">
              <span className="badge-dot" /> Ativo
            </span>
          ) : (
            <span className="badge muted">
              <span className="badge-dot" /> Inativo
            </span>
          ),
      },
      {
        key: "acoes",
        header: "Ações",
        width: 340,
        render: (f) => (
          <div className="row gap-10">
            <button className="btn" onClick={() => openEdit(f)}>
              Editar
            </button>
            <button
              className="btn"
              onClick={() =>
                navigate(`/custos/fornecedor?fornecedor=${encodeURIComponent(f.cod)}`)
              }
            >
              Custo
            </button>
            <button
              className={`btn ${(f.ativo_sn ?? "S") === "S" ? "danger" : ""}`}
              onClick={() => askToggleAtivo(f)}
            >
              {(f.ativo_sn ?? "S") === "S" ? "Inativar" : "Ativar"}
            </button>
          </div>
        ),
      },
    ],
    [navigate]
  );

  return (
    <>
      <PageHero
        icon={partnersIcon}
        backgroundImage={suppliersBg}
        backgroundPosition="center 34%"
        eyebrow="Cadastros"
        title="Fornecedores"
        description="Consulta operacional de fornecedores, com manutencao cadastral, filtros por status e controle por filial."
        metrics={[
          { label: "Filial", value: filialView },
          { label: "Fornecedores", value: String(sortedItems.length) },
          { label: "Ativos", value: String(sortedItems.filter((f) => (f.ativo_sn ?? "S") === "S").length) },
        ]}
        actions={
          <div className="row gap-10">
            <Link to="/custos/fornecedor" className="btn">
              Abrir custo
            </Link>
            <button type="button" className="btn primary" onClick={openNew}>Novo fornecedor</button>
          </div>
        }
      />

      <div className="card">
      <Toolbar
        left={
          <div className="hint">
            Filial: <b>{filialView}</b> — {ativos ? "Mostrando apenas ativos" : "Mostrando todos"}
          </div>
        }
        right={
          <>
            <input
              className="input minw-240"
              value={q}
              onChange={(e) => setQ(e.target.value)}
              placeholder="Buscar (código, nome, doc...)"
              aria-label="Buscar fornecedores"
            />

            <button className="btn" onClick={doSearch} disabled={loading}>
              Buscar
            </button>

            <select
              className="select"
              value={ativos ? "true" : "false"}
              onChange={(e) => {
                setAtivos(e.target.value === "true");
                setPage(1);
              }}
              aria-label="Filtro ativos"
            >
              <option value="true">Ativos</option>
              <option value="false">Todos</option>
            </select>

            <button className="btn" onClick={load} disabled={loading}>
              Aplicar
            </button>
            <button
              className="btn ghost"
              onClick={() => {
                setQ("");
                setAtivos(true);
                setPage(1);
              }}
              disabled={loading}
            >
              Limpar
            </button>

            <button className="btn primary" onClick={openNew}>
              Novo
            </button>
          </>
        }
      />

      {err && <div className="alert mt-12">{err}</div>}

      <div className="section-title">Resumo</div>
      <div className="stats-grid">
        <div className="stat-card">
          <div>
            <div className="kpi-label">Fornecedores (filtrados)</div>
            <div className="kpi">{sortedItems.length}</div>
          </div>
          <div className="stat-icon">FR</div>
        </div>
        <div className="stat-card">
          <div>
            <div className="kpi-label">Ativos no filtro</div>
            <div className="kpi">
              {sortedItems.filter((f) => (f.ativo_sn ?? "S") === "S").length}
            </div>
          </div>
          <div className="stat-icon success">OK</div>
        </div>
        <div className="stat-card">
          <div>
            <div className="kpi-label">Filial</div>
            <div className="kpi">{filialView}</div>
          </div>
          <div className="stat-icon solid">F</div>
        </div>
      </div>

      <div className="row-between mt-12">
        <div className="hint">
          <Pager
            page={page}
            totalPages={totalPages}
            pageSize={pageSize}
            totalItems={sortedItems.length}
            onPageChange={(p) => setPage(p)}
            onPageSizeChange={(ps) => {
              setPageSize(ps);
              setPage(1);
            }}
            showPageSize
          />
        </div>
      </div>

      <DataTable
        rows={pagedRows}
        columns={columns}
        sortKey={sortKey}
        sortDir={sortDir}
        className="compact"
        wrapperClassName="table-scroller"
        onSortChange={(k, d) => {
          setSortKey(k as SortKey);
          setSortDir(d);
          setPage(1);
        }}
        loading={loading}
        emptyText="Nenhum fornecedor encontrado."
      />

      {modalOpen && (
        <Modal title={modalTitle} onClose={() => setModalOpen(false)}>
          <div className="form-grid">
            <div className="form-field">
              <label>Código</label>
              <input
                value={form.cod}
                onChange={(e) => setForm({ ...form, cod: e.target.value })}
                disabled={!!editingCod}
              />
            </div>

            <div className="form-field">
              <label>Filial</label>
              <input
                value={form.filial}
                onChange={(e) => setForm({ ...form, filial: e.target.value })}
              />
            </div>

            <div className="form-field col-span-all">
              <label>Nome</label>
              <input value={form.nome} onChange={(e) => setForm({ ...form, nome: e.target.value })} />
            </div>

            <div className="form-field">
              <label>Documento</label>
              <input value={form.doc} onChange={(e) => setForm({ ...form, doc: e.target.value })} />
            </div>

            <div className="form-field">
              <label>Email</label>
              <input value={form.email} onChange={(e) => setForm({ ...form, email: e.target.value })} />
            </div>

            <div className="form-field">
              <label>Fone</label>
              <input value={form.fone} onChange={(e) => setForm({ ...form, fone: e.target.value })} />
            </div>
          </div>

          <div className="form-actions">
            <button className="btn" onClick={() => setModalOpen(false)} disabled={loading}>
              Cancelar
            </button>
            <button className="btn primary" onClick={save} disabled={loading}>
              Salvar
            </button>
          </div>
        </Modal>
      )}

      {confirmOpen && confirmFornecedor && (
        <ConfirmDialog
          title={(confirmFornecedor.ativo_sn ?? "S") === "S" ? "Inativar fornecedor" : "Ativar fornecedor"}
          message={
            (confirmFornecedor.ativo_sn ?? "S") === "S"
              ? `Deseja realmente INATIVAR o fornecedor ${confirmFornecedor.cod} - ${confirmFornecedor.nome}?`
              : `Deseja realmente ATIVAR o fornecedor ${confirmFornecedor.cod} - ${confirmFornecedor.nome}?`
          }
          confirmText={(confirmFornecedor.ativo_sn ?? "S") === "S" ? "Inativar" : "Ativar"}
          cancelText="Cancelar"
          danger={(confirmFornecedor.ativo_sn ?? "S") === "S"}
          loading={loading}
          onClose={() => {
            setConfirmOpen(false);
            setConfirmFornecedor(null);
          }}
          onConfirm={async () => {
            await toggleAtivo(confirmFornecedor);
            setConfirmOpen(false);
            setConfirmFornecedor(null);
          }}
        />
      )}
      </div>
    </>
  );
}
