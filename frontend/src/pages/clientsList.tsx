import { useEffect, useMemo, useState } from "react";
import { Toolbar } from "../components/Toolbar";
import { Modal } from "../components/Modal";
import { ConfirmDialog } from "../components/ConfirmDialog";
import { Pager } from "../components/Pager";
import { DataTable, type Column, type SortDir } from "../components/DataTable";
import { PageHero } from "../components/PageHero";
import { getFilial, onFilialChange } from "../state/filial";
import clientsIcon from "../assets/shell-icons/clients.png";
import clientsBg from "../assets/hero-backgrounds/clients.jpg";
import {
  listClientes,
  buscarClientes,
  createCliente,
  updateCliente,
  setClienteAtivo,
  type Cliente,
} from "../api/clients";

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

function getErrorMessage(error: unknown, fallback: string): string {
  if (error instanceof Error && error.message) return error.message;
  return fallback;
}

function norm(v: unknown) {
  return (v ?? "").toString().toLowerCase().trim();
}

function getSortValue(item: Cliente, key: SortKey): unknown {
  if (key === "ativo_sn") return item.ativo_sn ?? "S";
  if (key === "cod") return item.cod;
  if (key === "nome") return item.nome;
  return item.doc;
}

export function ClientsList() {
  const [filialView, setFilialView] = useState(getFilial());
  const [ativos, setAtivos] = useState(true);
  const [q, setQ] = useState("");

  const [loading, setLoading] = useState(false);
  const [err, setErr] = useState<string | null>(null);
  const [items, setItems] = useState<Cliente[]>([]);

  const [page, setPage] = useState(1);
  const [pageSize, setPageSize] = useState(10);

  const [sortKey, setSortKey] = useState<SortKey>("nome");
  const [sortDir, setSortDir] = useState<SortDir>("asc");

  const [modalOpen, setModalOpen] = useState(false);
  const [editingCod, setEditingCod] = useState<string | null>(null);
  const [form, setForm] = useState<FormState>(() => emptyForm());

  const [confirmOpen, setConfirmOpen] = useState(false);
  const [confirmItem, setConfirmItem] = useState<Cliente | null>(null);

  const modalTitle = useMemo(() => (editingCod ? `Editar: ${editingCod}` : "Novo"), [editingCod]);

  function askToggleAtivo(c: Cliente) {
    setConfirmItem(c);
    setConfirmOpen(true);
  }

  async function load() {
    setErr(null);
    setLoading(true);
    try {
      const filial = getFilial();
      const data = await listClientes({ ativos, filial });
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
      const data = await buscarClientes({ q: q.trim(), filial });
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
      setConfirmItem(null);
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

  function openEdit(c: Cliente) {
    setEditingCod(c.cod);
    setForm({
      cod: c.cod,
      nome: c.nome ?? "",
      doc: c.doc ?? "",
      email: c.email ?? "",
      fone: c.fone ?? "",
      filial: c.filial ?? getFilial(),
    });
    setModalOpen(true);
  }

  async function save() {
    setErr(null);
    setLoading(true);
    try {
      if (!form.cod.trim() || !form.nome.trim()) {
        throw new Error("Codigo e Nome sao obrigatorios.");
      }

      if (editingCod) {
        await updateCliente(editingCod, {
          filial: form.filial,
          nome: form.nome,
          doc: form.doc || null,
          email: form.email || null,
          fone: form.fone || null,
        });
      } else {
        await createCliente({
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

  async function toggleAtivo(c: Cliente) {
    setErr(null);
    setLoading(true);
    try {
      const ativoAtual = (c.ativo_sn ?? "S") === "S";
      await setClienteAtivo(c.cod, { ativo: !ativoAtual, filial: c.filial ?? getFilial() });
      await load();
    } catch (error: unknown) {
      setErr(getErrorMessage(error, "Erro ao alterar ativo"));
    } finally {
      setLoading(false);
    }
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

  const totalPages = useMemo(
    () => Math.max(1, Math.ceil(sortedItems.length / pageSize)),
    [sortedItems.length, pageSize]
  );

  const pagedRows = useMemo(() => {
    const safePage = Math.min(Math.max(1, page), totalPages);
    const start = (safePage - 1) * pageSize;
    return sortedItems.slice(start, start + pageSize);
  }, [sortedItems, page, pageSize, totalPages]);

  const columns: Column<Cliente>[] = useMemo(
    () => [
      { key: "cod", header: "Codigo", sortable: true },
      { key: "nome", header: "Nome", sortable: true },
      { key: "doc", header: "Doc", sortable: true, className: "hide-sm" },
      {
        key: "ativo_sn",
        header: "Ativo",
        sortable: true,
        value: (x) => x.ativo_sn ?? "S",
        render: (x) =>
          (x.ativo_sn ?? "S") === "S" ? (
            <span className="badge success"><span className="badge-dot" /> Ativo</span>
          ) : (
            <span className="badge muted"><span className="badge-dot" /> Inativo</span>
          ),
      },
      {
        key: "acoes",
        header: "Acoes",
        width: 240,
        render: (x) => (
          <div className="row gap-10">
            <button className="btn" onClick={() => openEdit(x)}>Editar</button>
            <button
              className={`btn ${(x.ativo_sn ?? "S") === "S" ? "danger" : ""}`}
              onClick={() => askToggleAtivo(x)}
            >
              {(x.ativo_sn ?? "S") === "S" ? "Inativar" : "Ativar"}
            </button>
          </div>
        ),
      },
    ],
    []
  );

  return (
    <>
      <PageHero
        icon={clientsIcon}
        backgroundImage={clientsBg}
        backgroundPosition="center 38%"
        eyebrow="Cadastros"
        title="Clientes"
        description="Base comercial de clientes ativos, com busca, manutencao cadastral e controle de status por filial."
        metrics={[
          { label: "Filial", value: filialView },
          { label: "Clientes", value: String(sortedItems.length) },
          { label: "Ativos", value: String(sortedItems.filter((c) => (c.ativo_sn ?? "S") === "S").length) },
        ]}
        actions={<button type="button" className="btn primary" onClick={openNew}>Novo cliente</button>}
      />

      <div className="card">
      <Toolbar
        left={
          <div className="hint">
            Filial: <b>{filialView}</b> - {ativos ? "Mostrando apenas ativos" : "Mostrando todos"}
          </div>
        }
        right={
          <>
            <input
              className="input minw-240"
              value={q}
              onChange={(e) => setQ(e.target.value)}
              placeholder="Buscar (codigo, nome, doc...)"
            />
            <button type="button" className="btn" onClick={doSearch} disabled={loading}>
              Buscar
            </button>

            <select
              className="select"
              value={ativos ? "true" : "false"}
              onChange={(e) => {
                setAtivos(e.target.value === "true");
                setPage(1);
              }}
            >
              <option value="true">Ativos</option>
              <option value="false">Todos</option>
            </select>

            <button type="button" className="btn" onClick={load} disabled={loading}>
              Aplicar
            </button>
            <button
              type="button"
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
            <button type="button" className="btn primary" onClick={openNew}>
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
            <div className="kpi-label">Clientes (filtrados)</div>
            <div className="kpi">{sortedItems.length}</div>
          </div>
          <div className="stat-icon">CL</div>
        </div>
        <div className="stat-card">
          <div>
            <div className="kpi-label">Ativos no filtro</div>
            <div className="kpi">
              {sortedItems.filter((c) => (c.ativo_sn ?? "S") === "S").length}
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
            onPageChange={setPage}
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
        emptyText="Nenhum registro encontrado."
      />

      {modalOpen && (
        <Modal title={modalTitle} onClose={() => setModalOpen(false)}>
          <div className="form-grid">
            <div className="form-field">
              <label>Codigo</label>
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
            <button type="button" className="btn" onClick={() => setModalOpen(false)} disabled={loading}>
              Cancelar
            </button>
            <button type="button" className="btn primary" onClick={save} disabled={loading}>
              Salvar
            </button>
          </div>
        </Modal>
      )}

      {confirmOpen && confirmItem && (
        <ConfirmDialog
          title={(confirmItem.ativo_sn ?? "S") === "S" ? "Inativar" : "Ativar"}
          message={
            (confirmItem.ativo_sn ?? "S") === "S"
              ? `Deseja realmente INATIVAR o codigo ${confirmItem.cod}?`
              : `Deseja realmente ATIVAR o codigo ${confirmItem.cod}?`
          }
          confirmText={(confirmItem.ativo_sn ?? "S") === "S" ? "Inativar" : "Ativar"}
          cancelText="Cancelar"
          danger={(confirmItem.ativo_sn ?? "S") === "S"}
          loading={loading}
          onClose={() => {
            setConfirmOpen(false);
            setConfirmItem(null);
          }}
          onConfirm={async () => {
            await toggleAtivo(confirmItem);
            setConfirmOpen(false);
            setConfirmItem(null);
          }}
        />
      )}
      </div>
    </>
  );
}
