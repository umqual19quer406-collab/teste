import { useEffect, useMemo, useState } from "react";
import { Toolbar } from "../components/Toolbar";
import { Pager } from "../components/Pager";
import { DataTable, type Column, type SortDir } from "../components/DataTable";
import { PageHero } from "../components/PageHero";
import { getFilial, onFilialChange } from "../state/filial";
import partnersIcon from "../assets/shell-icons/partners.png";
import partnersBg from "../assets/hero-backgrounds/partners.jpg";
import {
  listarSa1Clientes,
  obterSa1Cliente,
  criarSa1Cliente,
  inativarSa1Cliente,
  setTabelaSa1Cliente,
  listarSa2Fornecedores,
  obterSa2Fornecedor,
  criarSa2Fornecedor,
  inativarSa2Fornecedor,
} from "../api/parceiros";
import {
  buscarPrecoTabela,
  criarTabelaPreco,
  definirPrecoTabela,
  listarItensTabelaPreco,
  listarTabelasPreco,
  type ItemPrecoTabela,
  type TabelaPreco,
} from "../api/precos";

type TabKey = "clientes" | "fornecedores" | "precos";

type ClienteForm = {
  cod: string;
  nome: string;
  doc: string;
  email: string;
  tel: string;
  end: string;
  mun: string;
  uf: string;
  cep: string;
  tabelaId: string;
  filial: string;
};

type FornForm = {
  cod: string;
  nome: string;
  doc: string;
  email: string;
  tel: string;
  end: string;
  mun: string;
  uf: string;
  cep: string;
  filial: string;
};

type TabelaForm = {
  codigo: string;
  descricao: string;
};

type PrecoForm = {
  tabelaId: string;
  produto: string;
  preco: string;
  dtIni: string;
};

function emptyCliente(): ClienteForm {
  return {
    cod: "",
    nome: "",
    doc: "",
    email: "",
    tel: "",
    end: "",
    mun: "",
    uf: "",
    cep: "",
    tabelaId: "",
    filial: getFilial(),
  };
}

function emptyFornecedor(): FornForm {
  return {
    cod: "",
    nome: "",
    doc: "",
    email: "",
    tel: "",
    end: "",
    mun: "",
    uf: "",
    cep: "",
    filial: getFilial(),
  };
}

function emptyTabela(): TabelaForm {
  return {
    codigo: "",
    descricao: "",
  };
}

function todayIso() {
  return new Date().toISOString().slice(0, 10);
}

function emptyPrecoForm(): PrecoForm {
  return {
    tabelaId: "",
    produto: "",
    preco: "",
    dtIni: todayIso(),
  };
}

function toNumber(value: string, fallback = 0) {
  const n = Number(value);
  return Number.isFinite(n) ? n : fallback;
}

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

export function Parceiros() {
  const [tab, setTab] = useState<TabKey>("clientes");
  const [filialView, setFilialView] = useState(getFilial());

  const [loading, setLoading] = useState(false);
  const [err, setErr] = useState<string | null>(null);
  const [lastResp, setLastResp] = useState<Record<string, unknown> | null>(null);

  const [clientes, setClientes] = useState<Record<string, unknown>[]>([]);
  const [fornecedores, setFornecedores] = useState<Record<string, unknown>[]>([]);
  const [tabelas, setTabelas] = useState<TabelaPreco[]>([]);
  const [itensTabela, setItensTabela] = useState<ItemPrecoTabela[]>([]);

  const [cliAtivo, setCliAtivo] = useState(true);
  const [cliQ, setCliQ] = useState("");
  const [fornAtivo, setFornAtivo] = useState(true);
  const [fornQ, setFornQ] = useState("");

  const [cliPage, setCliPage] = useState(1);
  const [cliPageSize, setCliPageSize] = useState(10);
  const [fornPage, setFornPage] = useState(1);
  const [fornPageSize, setFornPageSize] = useState(10);

  const [cliForm, setCliForm] = useState<ClienteForm>(emptyCliente());
  const [fornForm, setFornForm] = useState<FornForm>(emptyFornecedor());
  const [tabelaForm, setTabelaForm] = useState<TabelaForm>(emptyTabela());
  const [precoForm, setPrecoForm] = useState<PrecoForm>(emptyPrecoForm());

  const [cliBuscaCod, setCliBuscaCod] = useState("");
  const [fornBuscaCod, setFornBuscaCod] = useState("");
  const [cliDelCod, setCliDelCod] = useState("");
  const [fornDelCod, setFornDelCod] = useState("");
  const [cliSetTabelaCod, setCliSetTabelaCod] = useState("");
  const [cliSetTabelaId, setCliSetTabelaId] = useState("");
  const [precoLookupProduto, setPrecoLookupProduto] = useState("");
  const [precoLookupTabelaId, setPrecoLookupTabelaId] = useState("");
  const [precoLookupData, setPrecoLookupData] = useState(todayIso());

  const [sortKey, setSortKey] = useState("cod");
  const [sortDir, setSortDir] = useState<SortDir>("asc");

  async function loadClientes() {
    setErr(null);
    setLoading(true);
    try {
      const data = await listarSa1Clientes({ filial: filialView, ativo: cliAtivo, q: cliQ || undefined });
      setClientes(Array.isArray(data) ? data : []);
    } catch (error: unknown) {
      setErr(getErrorMessage(error, "Erro ao carregar clientes SA1"));
    } finally {
      setLoading(false);
    }
  }

  async function loadFornecedores() {
    setErr(null);
    setLoading(true);
    try {
      const data = await listarSa2Fornecedores({ filial: filialView, ativo: fornAtivo, q: fornQ || undefined });
      setFornecedores(Array.isArray(data) ? data : []);
    } catch (error: unknown) {
      setErr(getErrorMessage(error, "Erro ao carregar fornecedores SA2"));
    } finally {
      setLoading(false);
    }
  }

  async function loadTabelas() {
    setErr(null);
    setLoading(true);
    try {
      const data = await listarTabelasPreco({ filial: filialView });
      setTabelas(Array.isArray(data) ? data : []);
    } catch (error: unknown) {
      setErr(getErrorMessage(error, "Erro ao carregar tabelas de preco"));
    } finally {
      setLoading(false);
    }
  }

  async function loadItensTabela(tabelaId: number) {
    setErr(null);
    setLoading(true);
    try {
      const data = await listarItensTabelaPreco(tabelaId, { filial: filialView });
      setItensTabela(Array.isArray(data) ? data : []);
    } catch (error: unknown) {
      setErr(getErrorMessage(error, "Erro ao carregar itens da tabela"));
    } finally {
      setLoading(false);
    }
  }

  useEffect(() => {
    if (tab === "clientes") loadClientes();
    if (tab === "fornecedores") loadFornecedores();
    if (tab === "precos") loadTabelas();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [tab, filialView, cliAtivo, cliQ, fornAtivo, fornQ]);

  useEffect(() => {
    const unsub = onFilialChange((nova) => {
      setFilialView(nova);
      setCliForm((f) => ({ ...f, filial: nova }));
      setFornForm((f) => ({ ...f, filial: nova }));
      setPrecoForm((f) => ({ ...f, tabelaId: "", dtIni: f.dtIni || todayIso() }));
      setPrecoLookupTabelaId("");
      setItensTabela([]);
    });
    return unsub;
  }, []);

  async function onCriarCliente() {
    setErr(null);
    setLoading(true);
    try {
      if (!cliForm.cod.trim() || !cliForm.nome.trim()) {
        throw new Error("Codigo e nome sao obrigatorios.");
      }
      const resp = await criarSa1Cliente({
        filial: cliForm.filial || filialView,
        cod: cliForm.cod.trim(),
        nome: cliForm.nome.trim(),
        doc: cliForm.doc.trim() || null,
        email: cliForm.email.trim() || null,
        tel: cliForm.tel.trim() || null,
        end: cliForm.end.trim() || null,
        mun: cliForm.mun.trim() || null,
        uf: cliForm.uf.trim() || null,
        cep: cliForm.cep.trim() || null,
        tabela_id: cliForm.tabelaId ? toNumber(cliForm.tabelaId, 0) : null,
      });
      setLastResp(resp);
      setCliForm(emptyCliente());
      await loadClientes();
    } catch (error: unknown) {
      setErr(getErrorMessage(error, "Falha ao criar cliente"));
    } finally {
      setLoading(false);
    }
  }

  async function onCriarFornecedor() {
    setErr(null);
    setLoading(true);
    try {
      if (!fornForm.cod.trim() || !fornForm.nome.trim()) {
        throw new Error("Codigo e nome sao obrigatorios.");
      }
      const resp = await criarSa2Fornecedor({
        filial: fornForm.filial || filialView,
        cod: fornForm.cod.trim(),
        nome: fornForm.nome.trim(),
        doc: fornForm.doc.trim() || null,
        email: fornForm.email.trim() || null,
        tel: fornForm.tel.trim() || null,
        end: fornForm.end.trim() || null,
        mun: fornForm.mun.trim() || null,
        uf: fornForm.uf.trim() || null,
        cep: fornForm.cep.trim() || null,
      });
      setLastResp(resp);
      setFornForm(emptyFornecedor());
      await loadFornecedores();
    } catch (error: unknown) {
      setErr(getErrorMessage(error, "Falha ao criar fornecedor"));
    } finally {
      setLoading(false);
    }
  }

  async function onBuscarCliente(cod?: string) {
    const target = cod ?? cliBuscaCod.trim();
    setErr(null);
    setLoading(true);
    try {
      if (!target) throw new Error("Informe o codigo do cliente.");
      const resp = await obterSa1Cliente(target, { filial: filialView });
      setLastResp(resp);
    } catch (error: unknown) {
      setErr(getErrorMessage(error, "Falha ao buscar cliente"));
    } finally {
      setLoading(false);
    }
  }

  async function onBuscarFornecedor(cod?: string) {
    const target = cod ?? fornBuscaCod.trim();
    setErr(null);
    setLoading(true);
    try {
      if (!target) throw new Error("Informe o codigo do fornecedor.");
      const resp = await obterSa2Fornecedor(target, { filial: filialView });
      setLastResp(resp);
    } catch (error: unknown) {
      setErr(getErrorMessage(error, "Falha ao buscar fornecedor"));
    } finally {
      setLoading(false);
    }
  }

  async function onInativarCliente(cod?: string) {
    const target = cod ?? cliDelCod.trim();
    if (!target) {
      setErr("Informe o codigo do cliente.");
      return;
    }
    setErr(null);
    setLoading(true);
    try {
      const resp = await inativarSa1Cliente(target, { filial: filialView });
      setLastResp(resp);
      setCliDelCod("");
      await loadClientes();
    } catch (error: unknown) {
      setErr(getErrorMessage(error, "Falha ao inativar cliente"));
    } finally {
      setLoading(false);
    }
  }

  async function onInativarFornecedor(cod?: string) {
    const target = cod ?? fornDelCod.trim();
    if (!target) {
      setErr("Informe o codigo do fornecedor.");
      return;
    }
    setErr(null);
    setLoading(true);
    try {
      const resp = await inativarSa2Fornecedor(target, { filial: filialView });
      setLastResp(resp);
      setFornDelCod("");
      await loadFornecedores();
    } catch (error: unknown) {
      setErr(getErrorMessage(error, "Falha ao inativar fornecedor"));
    } finally {
      setLoading(false);
    }
  }

  async function onSetTabela() {
    setErr(null);
    setLoading(true);
    try {
      if (!cliSetTabelaCod.trim()) throw new Error("Informe o codigo do cliente.");
      const resp = await setTabelaSa1Cliente({
        cod: cliSetTabelaCod.trim(),
        tabela_id: cliSetTabelaId ? toNumber(cliSetTabelaId, 0) : null,
        filial: filialView,
      });
      setLastResp(resp);
      setCliSetTabelaCod("");
      setCliSetTabelaId("");
      await loadClientes();
    } catch (error: unknown) {
      setErr(getErrorMessage(error, "Falha ao definir tabela"));
    } finally {
      setLoading(false);
    }
  }

  async function onCriarTabela() {
    setErr(null);
    setLoading(true);
    try {
      if (!tabelaForm.codigo.trim() || !tabelaForm.descricao.trim()) {
        throw new Error("Codigo e descricao da tabela sao obrigatorios.");
      }
      const resp = await criarTabelaPreco({
        filial: filialView,
        codigo: tabelaForm.codigo.trim(),
        descricao: tabelaForm.descricao.trim(),
      });
      setLastResp(resp);
      setTabelaForm(emptyTabela());
      await loadTabelas();
      if (resp && typeof resp.id === "number") {
        setPrecoForm((f) => ({ ...f, tabelaId: String(resp.id) }));
        setPrecoLookupTabelaId(String(resp.id));
        await loadItensTabela(Number(resp.id));
      }
    } catch (error: unknown) {
      setErr(getErrorMessage(error, "Falha ao criar tabela de preco"));
    } finally {
      setLoading(false);
    }
  }

  async function onDefinirPreco() {
    setErr(null);
    setLoading(true);
    try {
      if (!precoForm.tabelaId || !precoForm.produto.trim() || !precoForm.preco || !precoForm.dtIni) {
        throw new Error("Tabela, produto, preco e data inicial sao obrigatorios.");
      }
      const resp = await definirPrecoTabela({
        filial: filialView,
        tabela_id: toNumber(precoForm.tabelaId, 0),
        produto: precoForm.produto.trim(),
        preco: toNumber(precoForm.preco, 0),
        dt_ini: precoForm.dtIni,
      });
      setLastResp(resp);
      setPrecoForm((f) => ({ ...emptyPrecoForm(), tabelaId: f.tabelaId }));
      await loadItensTabela(toNumber(precoForm.tabelaId, 0));
    } catch (error: unknown) {
      setErr(getErrorMessage(error, "Falha ao definir preco"));
    } finally {
      setLoading(false);
    }
  }

  async function onBuscarPrecoVigente() {
    setErr(null);
    setLoading(true);
    try {
      if (!precoLookupTabelaId || !precoLookupProduto.trim() || !precoLookupData) {
        throw new Error("Tabela, produto e data sao obrigatorios.");
      }
      const resp = await buscarPrecoTabela({
        filial: filialView,
        tabela_id: toNumber(precoLookupTabelaId, 0),
        produto: precoLookupProduto.trim(),
        data: precoLookupData,
      });
      setLastResp(resp);
    } catch (error: unknown) {
      setErr(getErrorMessage(error, "Falha ao buscar preco vigente"));
    } finally {
      setLoading(false);
    }
  }

  const clienteColumns: Column<Record<string, unknown>>[] = [
      { key: "cod", header: "Codigo", sortable: true, value: (x) => toStringValue(x.A1_COD ?? x.cod, "") },
      { key: "nome", header: "Nome", sortable: true, value: (x) => toStringValue(x.A1_NOME ?? x.nome, "") },
      { key: "doc", header: "Doc", sortable: true, className: "hide-sm", value: (x) => toStringValue(x.A1_DOC ?? x.doc, "-") },
      { key: "email", header: "Email", sortable: true, className: "hide-sm", value: (x) => toStringValue(x.A1_EMAIL ?? x.email, "-") },
      { key: "tel", header: "Tel", sortable: true, className: "hide-sm", value: (x) => toStringValue(x.A1_TEL ?? x.tel, "-") },
      {
        key: "tabela",
        header: "Tabela",
        sortable: true,
        className: "hide-sm",
        value: (x) =>
          `${toStringValue(x.TABELA_COD ?? x.tabela_cod ?? "-", "-")} ${toStringValue(x.TABELA_DESC ?? x.tabela_desc ?? "", "")}`.trim(),
      },
      {
        key: "acoes",
        header: "Acoes",
        render: (x) => (
          <div className="row gap-10">
            <button className="btn" onClick={() => onBuscarCliente(toStringValue(x.A1_COD ?? x.cod, ""))}>
              Detalhar
            </button>
            <button className="btn danger" onClick={() => onInativarCliente(toStringValue(x.A1_COD ?? x.cod, ""))}>
              Inativar
            </button>
          </div>
        ),
      },
  ];

  const fornecedorColumns: Column<Record<string, unknown>>[] = [
      { key: "cod", header: "Codigo", sortable: true, value: (x) => toStringValue(x.A2_COD ?? x.cod, "") },
      { key: "nome", header: "Nome", sortable: true, value: (x) => toStringValue(x.A2_NOME ?? x.nome, "") },
      { key: "doc", header: "Doc", sortable: true, className: "hide-sm", value: (x) => toStringValue(x.A2_DOC ?? x.doc, "-") },
      { key: "email", header: "Email", sortable: true, className: "hide-sm", value: (x) => toStringValue(x.A2_EMAIL ?? x.email, "-") },
      { key: "tel", header: "Tel", sortable: true, className: "hide-sm", value: (x) => toStringValue(x.A2_TEL ?? x.tel, "-") },
      {
        key: "acoes",
        header: "Acoes",
        render: (x) => (
          <div className="row gap-10">
            <button className="btn" onClick={() => onBuscarFornecedor(toStringValue(x.A2_COD ?? x.cod, ""))}>
              Detalhar
            </button>
            <button className="btn danger" onClick={() => onInativarFornecedor(toStringValue(x.A2_COD ?? x.cod, ""))}>
              Inativar
            </button>
          </div>
        ),
      },
  ];

  const tabelaColumns: Column<TabelaPreco>[] = [
    { key: "codigo", header: "Codigo", sortable: true, value: (x) => x.codigo },
    { key: "descricao", header: "Descricao", sortable: true, value: (x) => x.descricao },
    { key: "id", header: "ID", sortable: true, value: (x) => String(x.id) },
    {
      key: "ativa",
      header: "Status",
      sortable: true,
      render: (x) => (
        <span className={`badge ${x.ativa ? "success" : "muted"}`}>
          <span className="badge-dot" />
          {x.ativa ? "Ativa" : "Inativa"}
        </span>
      ),
    },
    {
      key: "acoes",
      header: "Acoes",
      render: (x) => (
        <button
          className="btn"
          onClick={() => {
            setPrecoForm((f) => ({ ...f, tabelaId: String(x.id) }));
            setPrecoLookupTabelaId(String(x.id));
            void loadItensTabela(x.id);
          }}
        >
          Usar tabela
        </button>
      ),
    },
  ];

  const itemTabelaColumns: Column<ItemPrecoTabela>[] = [
    { key: "produto", header: "Produto", sortable: true, value: (x) => x.produto },
    {
      key: "preco",
      header: "Preco",
      sortable: true,
      value: (x) => x.preco,
      render: (x) => x.preco.toLocaleString("pt-BR", { style: "currency", currency: "BRL" }),
    },
    { key: "dt_ini", header: "Dt. ini", sortable: true, value: (x) => x.dt_ini ?? "", render: (x) => x.dt_ini ?? "-" },
    { key: "dt_fim", header: "Dt. fim", sortable: true, value: (x) => x.dt_fim ?? "", render: (x) => x.dt_fim ?? "Vigente" },
    {
      key: "vigente",
      header: "Status",
      sortable: true,
      render: (x) => (
        <span className={`badge ${x.vigente ? "success" : "muted"}`}>
          <span className="badge-dot" />
          {x.vigente ? "Vigente" : "Historico"}
        </span>
      ),
    },
  ];

  const currentRows: Array<Record<string, unknown> | TabelaPreco> =
    tab === "clientes" ? clientes : tab === "fornecedores" ? fornecedores : tabelas;
  const currentCols: Column<Record<string, unknown> | TabelaPreco>[] =
    tab === "clientes"
      ? (clienteColumns as Column<Record<string, unknown> | TabelaPreco>[])
      : tab === "fornecedores"
        ? (fornecedorColumns as Column<Record<string, unknown> | TabelaPreco>[])
        : (tabelaColumns as Column<Record<string, unknown> | TabelaPreco>[]);

  const sortedRows = useMemo(() => {
    const col = currentCols.find((c) => c.key === sortKey);
    const valueFn = col?.value ?? ((r: Record<string, unknown>) => r[sortKey]);
    const arr = [...currentRows];
    arr.sort((a, b) => {
      const av = normalize(valueFn(a));
      const bv = normalize(valueFn(b));
      if (av < bv) return sortDir === "asc" ? -1 : 1;
      if (av > bv) return sortDir === "asc" ? 1 : -1;
      return 0;
    });
    return arr;
  }, [currentRows, currentCols, sortKey, sortDir]);

  const totalPages = useMemo(() => {
    const pageSize = tab === "clientes" ? cliPageSize : fornPageSize;
    return Math.max(1, Math.ceil(sortedRows.length / pageSize));
  }, [sortedRows.length, tab, cliPageSize, fornPageSize]);

  const pagedRows = useMemo(() => {
    const page = tab === "clientes" ? cliPage : fornPage;
    const pageSize = tab === "clientes" ? cliPageSize : fornPageSize;
    const safePage = Math.min(Math.max(1, page), totalPages);
    const start = (safePage - 1) * pageSize;
    return sortedRows.slice(start, start + pageSize);
  }, [sortedRows, tab, cliPage, cliPageSize, fornPage, fornPageSize, totalPages]);

  return (
    <>
      <PageHero
        icon={partnersIcon}
        backgroundImage={partnersBg}
        backgroundPosition="center 38%"
        eyebrow="Relacionamento"
        title="Parceiros e precificacao"
        description="Painel operacional para clientes, fornecedores e tabelas de preco em estrutura Protheus, incluindo busca, inativacao, vinculo comercial e precificacao por vigencia."
        metrics={[
          { label: "Filial", value: filialView },
          { label: "Aba", value: tab === "clientes" ? "Clientes" : tab === "fornecedores" ? "Fornecedores" : "Tabelas de preco" },
          { label: "Registros", value: String(currentRows.length) },
        ]}
      />

      <div className="card">
      <Toolbar
        left={<div className="hint">Filial: <b>{filialView}</b></div>}
        right={
          <>
            <button className={`btn ${tab === "clientes" ? "primary" : ""}`} onClick={() => setTab("clientes")}>
              Clientes (SA1)
            </button>
            <button className={`btn ${tab === "fornecedores" ? "primary" : ""}`} onClick={() => setTab("fornecedores")}>
              Fornecedores (SA2)
            </button>
            <button className={`btn ${tab === "precos" ? "primary" : ""}`} onClick={() => setTab("precos")}>
              Tabelas de preco
            </button>
          </>
        }
      />

      {err && <div className="alert mt-12">{err}</div>}

      {tab === "clientes" && (
        <>
          <div className="section-title">Clientes SA1</div>
          <div className="row-between mt-12">
            <div className="row gap-10">
              <input
                className="input minw-240"
                value={cliQ}
                onChange={(e) => { setCliQ(e.target.value); setCliPage(1); }}
                placeholder="Buscar por codigo, nome, doc..."
              />
              <select className="select" value={cliAtivo ? "true" : "false"} onChange={(e) => { setCliAtivo(e.target.value === "true"); setCliPage(1); }}>
                <option value="true">Ativos</option>
                <option value="false">Todos</option>
              </select>
            </div>
            <div className="row gap-10">
              <button className="btn" onClick={() => { setCliPage(1); loadClientes(); }} disabled={loading}>Atualizar</button>
              <button className="btn ghost" onClick={() => { setCliQ(""); setCliPage(1); }} disabled={loading}>Limpar</button>
            </div>
          </div>

          <div className="row-between mt-12">
            <Pager
              page={cliPage}
              totalPages={totalPages}
              pageSize={cliPageSize}
              totalItems={sortedRows.length}
              onPageChange={setCliPage}
              onPageSizeChange={(ps) => { setCliPageSize(ps); setCliPage(1); }}
              showPageSize
            />
          </div>

          <DataTable
            rows={pagedRows}
            columns={clienteColumns}
            sortKey={sortKey}
            sortDir={sortDir}
            className="compact"
            wrapperClassName="table-scroller"
            onSortChange={(k, d) => {
              setSortKey(k);
              setSortDir(d);
              setCliPage(1);
            }}
            loading={loading}
            emptyText="Nenhum cliente encontrado."
          />

          <div className="section-title">Criar cliente</div>
          <div className="form-grid mt-12">
            <div className="form-field"><label>Codigo</label><input value={cliForm.cod} onChange={(e) => setCliForm({ ...cliForm, cod: e.target.value })} /></div>
            <div className="form-field"><label>Nome</label><input value={cliForm.nome} onChange={(e) => setCliForm({ ...cliForm, nome: e.target.value })} /></div>
            <div className="form-field"><label>Documento</label><input value={cliForm.doc} onChange={(e) => setCliForm({ ...cliForm, doc: e.target.value })} /></div>
            <div className="form-field"><label>Email</label><input value={cliForm.email} onChange={(e) => setCliForm({ ...cliForm, email: e.target.value })} /></div>
            <div className="form-field"><label>Telefone</label><input value={cliForm.tel} onChange={(e) => setCliForm({ ...cliForm, tel: e.target.value })} /></div>
            <div className="form-field"><label>Endereco</label><input value={cliForm.end} onChange={(e) => setCliForm({ ...cliForm, end: e.target.value })} /></div>
            <div className="form-field"><label>Municipio</label><input value={cliForm.mun} onChange={(e) => setCliForm({ ...cliForm, mun: e.target.value })} /></div>
            <div className="form-field"><label>UF</label><input value={cliForm.uf} onChange={(e) => setCliForm({ ...cliForm, uf: e.target.value })} /></div>
            <div className="form-field"><label>CEP</label><input value={cliForm.cep} onChange={(e) => setCliForm({ ...cliForm, cep: e.target.value })} /></div>
            <div className="form-field"><label>Tabela ID (opcional)</label><input value={cliForm.tabelaId} onChange={(e) => setCliForm({ ...cliForm, tabelaId: e.target.value })} /></div>
            <div className="form-field"><label>Filial</label><input value={cliForm.filial} onChange={(e) => setCliForm({ ...cliForm, filial: e.target.value })} /></div>
            <div className="form-field"><label>&nbsp;</label><button className="btn primary" onClick={onCriarCliente} disabled={loading}>Criar cliente</button></div>
          </div>

          <div className="section-title">Operacoes rapidas</div>
          <div className="form-grid mt-12">
            <div className="form-field"><label>Buscar por codigo</label><input value={cliBuscaCod} onChange={(e) => setCliBuscaCod(e.target.value)} /></div>
            <div className="form-field"><label>&nbsp;</label><button className="btn" onClick={() => onBuscarCliente()} disabled={loading}>Buscar</button></div>
            <div className="form-field"><label>Inativar por codigo</label><input value={cliDelCod} onChange={(e) => setCliDelCod(e.target.value)} /></div>
            <div className="form-field"><label>&nbsp;</label><button className="btn danger" onClick={() => onInativarCliente()} disabled={loading}>Inativar</button></div>
            <div className="form-field"><label>Set tabela (codigo)</label><input value={cliSetTabelaCod} onChange={(e) => setCliSetTabelaCod(e.target.value)} /></div>
            <div className="form-field"><label>Tabela ID</label><input value={cliSetTabelaId} onChange={(e) => setCliSetTabelaId(e.target.value)} /></div>
            <div className="form-field"><label>&nbsp;</label><button className="btn" onClick={onSetTabela} disabled={loading}>Definir tabela</button></div>
          </div>
        </>
      )}

      {tab === "fornecedores" && (
        <>
          <div className="section-title">Fornecedores SA2</div>
          <div className="row-between mt-12">
            <div className="row gap-10">
              <input
                className="input minw-240"
                value={fornQ}
                onChange={(e) => { setFornQ(e.target.value); setFornPage(1); }}
                placeholder="Buscar por codigo, nome, doc..."
              />
              <select className="select" value={fornAtivo ? "true" : "false"} onChange={(e) => { setFornAtivo(e.target.value === "true"); setFornPage(1); }}>
                <option value="true">Ativos</option>
                <option value="false">Todos</option>
              </select>
            </div>
            <div className="row gap-10">
              <button className="btn" onClick={() => { setFornPage(1); loadFornecedores(); }} disabled={loading}>Atualizar</button>
              <button className="btn ghost" onClick={() => { setFornQ(""); setFornPage(1); }} disabled={loading}>Limpar</button>
            </div>
          </div>

          <div className="row-between mt-12">
            <Pager
              page={fornPage}
              totalPages={totalPages}
              pageSize={fornPageSize}
              totalItems={sortedRows.length}
              onPageChange={setFornPage}
              onPageSizeChange={(ps) => { setFornPageSize(ps); setFornPage(1); }}
              showPageSize
            />
          </div>

          <DataTable
            rows={pagedRows}
            columns={fornecedorColumns}
            sortKey={sortKey}
            sortDir={sortDir}
            className="compact"
            wrapperClassName="table-scroller"
            onSortChange={(k, d) => {
              setSortKey(k);
              setSortDir(d);
              setFornPage(1);
            }}
            loading={loading}
            emptyText="Nenhum fornecedor encontrado."
          />

          <div className="section-title">Criar fornecedor</div>
          <div className="form-grid mt-12">
            <div className="form-field"><label>Codigo</label><input value={fornForm.cod} onChange={(e) => setFornForm({ ...fornForm, cod: e.target.value })} /></div>
            <div className="form-field"><label>Nome</label><input value={fornForm.nome} onChange={(e) => setFornForm({ ...fornForm, nome: e.target.value })} /></div>
            <div className="form-field"><label>Documento</label><input value={fornForm.doc} onChange={(e) => setFornForm({ ...fornForm, doc: e.target.value })} /></div>
            <div className="form-field"><label>Email</label><input value={fornForm.email} onChange={(e) => setFornForm({ ...fornForm, email: e.target.value })} /></div>
            <div className="form-field"><label>Telefone</label><input value={fornForm.tel} onChange={(e) => setFornForm({ ...fornForm, tel: e.target.value })} /></div>
            <div className="form-field"><label>Endereco</label><input value={fornForm.end} onChange={(e) => setFornForm({ ...fornForm, end: e.target.value })} /></div>
            <div className="form-field"><label>Municipio</label><input value={fornForm.mun} onChange={(e) => setFornForm({ ...fornForm, mun: e.target.value })} /></div>
            <div className="form-field"><label>UF</label><input value={fornForm.uf} onChange={(e) => setFornForm({ ...fornForm, uf: e.target.value })} /></div>
            <div className="form-field"><label>CEP</label><input value={fornForm.cep} onChange={(e) => setFornForm({ ...fornForm, cep: e.target.value })} /></div>
            <div className="form-field"><label>Filial</label><input value={fornForm.filial} onChange={(e) => setFornForm({ ...fornForm, filial: e.target.value })} /></div>
            <div className="form-field"><label>&nbsp;</label><button className="btn primary" onClick={onCriarFornecedor} disabled={loading}>Criar fornecedor</button></div>
          </div>

          <div className="section-title">Operacoes rapidas</div>
          <div className="form-grid mt-12">
            <div className="form-field"><label>Buscar por codigo</label><input value={fornBuscaCod} onChange={(e) => setFornBuscaCod(e.target.value)} /></div>
            <div className="form-field"><label>&nbsp;</label><button className="btn" onClick={() => onBuscarFornecedor()} disabled={loading}>Buscar</button></div>
            <div className="form-field"><label>Inativar por codigo</label><input value={fornDelCod} onChange={(e) => setFornDelCod(e.target.value)} /></div>
            <div className="form-field"><label>&nbsp;</label><button className="btn danger" onClick={() => onInativarFornecedor()} disabled={loading}>Inativar</button></div>
          </div>
        </>
      )}

      {tab === "precos" && (
        <>
          <div className="section-title">Tabelas de preco</div>
          <div className="row-between mt-12">
            <div className="hint">Filial: <b>{filialView}</b> | Reserva e parceiros usam a tabela comercial vigente.</div>
            <div className="row gap-10">
              <button className="btn" onClick={loadTabelas} disabled={loading}>Atualizar</button>
            </div>
          </div>

          <DataTable
            rows={tabelas}
            columns={tabelaColumns}
            sortKey={sortKey}
            sortDir={sortDir}
            className="compact"
            wrapperClassName="table-scroller"
            onSortChange={(k, d) => {
              setSortKey(k);
              setSortDir(d);
            }}
            loading={loading}
            emptyText="Nenhuma tabela de preco encontrada."
          />

          <div className="section-title">Criar tabela</div>
          <div className="form-grid mt-12">
            <div className="form-field"><label>Codigo</label><input value={tabelaForm.codigo} onChange={(e) => setTabelaForm({ ...tabelaForm, codigo: e.target.value })} /></div>
            <div className="form-field"><label>Descricao</label><input value={tabelaForm.descricao} onChange={(e) => setTabelaForm({ ...tabelaForm, descricao: e.target.value })} /></div>
            <div className="form-field"><label>&nbsp;</label><button className="btn primary" onClick={onCriarTabela} disabled={loading}>Criar tabela</button></div>
          </div>

          <div className="section-title">Definir preco vigente</div>
          <div className="form-grid mt-12">
            <div className="form-field">
              <label>Tabela</label>
              <select value={precoForm.tabelaId} onChange={(e) => setPrecoForm({ ...precoForm, tabelaId: e.target.value })}>
                <option value="">Selecione</option>
                {tabelas.map((t) => (
                  <option key={t.id} value={String(t.id)}>{t.codigo} - {t.descricao}</option>
                ))}
              </select>
            </div>
            <div className="form-field"><label>Produto</label><input value={precoForm.produto} onChange={(e) => setPrecoForm({ ...precoForm, produto: e.target.value })} /></div>
            <div className="form-field"><label>Preco</label><input type="number" step="0.01" value={precoForm.preco} onChange={(e) => setPrecoForm({ ...precoForm, preco: e.target.value })} /></div>
            <div className="form-field"><label>Data inicial</label><input type="date" value={precoForm.dtIni} onChange={(e) => setPrecoForm({ ...precoForm, dtIni: e.target.value })} /></div>
            <div className="form-field"><label>&nbsp;</label><button className="btn primary" onClick={onDefinirPreco} disabled={loading}>Salvar preco</button></div>
          </div>

          <div className="section-title">Consultar preco vigente</div>
          <div className="form-grid mt-12">
            <div className="form-field">
              <label>Tabela</label>
              <select value={precoLookupTabelaId} onChange={(e) => setPrecoLookupTabelaId(e.target.value)}>
                <option value="">Selecione</option>
                {tabelas.map((t) => (
                  <option key={t.id} value={String(t.id)}>{t.codigo} - {t.descricao}</option>
                ))}
              </select>
            </div>
            <div className="form-field"><label>Produto</label><input value={precoLookupProduto} onChange={(e) => setPrecoLookupProduto(e.target.value)} /></div>
            <div className="form-field"><label>Data</label><input type="date" value={precoLookupData} onChange={(e) => setPrecoLookupData(e.target.value)} /></div>
            <div className="form-field"><label>&nbsp;</label><button className="btn" onClick={onBuscarPrecoVigente} disabled={loading}>Buscar preco</button></div>
          </div>

          <div className="section-title">Itens da tabela</div>
          <div className="row-between mt-12">
            <div className="hint">
              {precoLookupTabelaId
                ? <>Tabela selecionada: <b>{precoLookupTabelaId}</b></>
                : "Selecione uma tabela para listar os precos cadastrados."}
            </div>
            <div className="row gap-10">
              <button
                className="btn"
                onClick={() => {
                  const tabelaId = precoLookupTabelaId || precoForm.tabelaId;
                  if (!tabelaId) {
                    setErr("Selecione uma tabela para listar os itens.");
                    return;
                  }
                  void loadItensTabela(toNumber(tabelaId, 0));
                }}
                disabled={loading}
              >
                Listar itens
              </button>
            </div>
          </div>

          <DataTable
            rows={itensTabela}
            columns={itemTabelaColumns}
            sortKey="produto"
            sortDir="asc"
            className="compact"
            wrapperClassName="table-scroller"
            onSortChange={() => {}}
            loading={loading}
            emptyText="Nenhum preco cadastrado para a tabela selecionada."
          />
        </>
      )}

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
