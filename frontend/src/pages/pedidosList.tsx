import { useEffect, useMemo, useState } from "react";
import { useNavigate, useSearchParams } from "react-router-dom";
import { Toolbar } from "../components/Toolbar";
import { Modal } from "../components/Modal";
import { ConfirmDialog } from "../components/ConfirmDialog";
import { Pager } from "../components/Pager";
import { DataTable, type Column, type SortDir } from "../components/DataTable";
import { PageHero } from "../components/PageHero";
import { PedidoDetalhePanel } from "./pedidoDetalhe";
import { getFilial, onFilialChange } from "../state/filial";
import ordersIcon from "../assets/shell-icons/orders.png";
import ordersBg from "../assets/hero-backgrounds/orders.jpg";
import { buscarProdutos, type ProdutoResumo } from "../api/produtos";
import {
  adicionarItem,
  cancelarPedido,
  criarPedido,
  editarItem,
  estornarPedido,
  excluirItem,
  faturarPedido,
  listarPedidos,
  listarPedidosEnriquecido,
  obterPedido,
  recalcularPedido,
  type CancelarPedidoInput,
  type EstornarPedidoInput,
  type FaturarPedidoInput,
} from "../api/vendas";

type PedidoRow = Record<string, unknown>;
type PedidoResumo = { id: number; filial: string; status: string; origem: string; valorTotal: number; data: string; qtdItens: number };
type ItemResumo = { id: number; pedidoId: number; produto: string; qtd: number; total: number; precoUnit: number; cmvUnit: number; ativo: string };

type PedidoForm = { filial: string; valorTotal: string; icms: string; ipi: string; totalBruto: string };
type AddItemForm = { filial: string; produto: string; qtd: string; total: string; precoUnit: string; cmvUnit: string };
type EditItemForm = { filial: string; qtd: string; total: string; precoUnit: string; cmvUnit: string };
type FaturarForm = { filial: string; clienteCod: string; vencDias: string };
type CancelarForm = { filial: string; modo: "AUTO" | "SIMPLES" | "ESTORNAR"; reativarReserva: boolean };
type EstornarForm = { filial: string; motivo: string };
type ConfirmState = { title: string; message: string; danger?: boolean; confirmText?: string; run: () => Promise<void> };
type SortKey = "id" | "data" | "filial" | "status" | "origem" | "valorTotal";

function toRecord(value: unknown): Record<string, unknown> {
  return value && typeof value === "object" ? (value as Record<string, unknown>) : {};
}

function toNumber(value: unknown, fallback = 0): number {
  if (typeof value === "number") return value;
  if (typeof value === "string" && value.trim()) {
    const n = Number(value);
    return Number.isFinite(n) ? n : fallback;
  }
  return fallback;
}

function toStringValue(value: unknown, fallback = ""): string {
  if (typeof value === "string") return value;
  if (value === null || value === undefined) return fallback;
  return String(value);
}

function getErrorMessage(error: unknown, fallback: string): string {
  if (error instanceof Error && error.message) return error.message;
  return fallback;
}

function emptyPedidoForm(): PedidoForm {
  return { filial: getFilial(), valorTotal: "0", icms: "", ipi: "", totalBruto: "" };
}

function emptyItemForm(): AddItemForm {
  return { filial: getFilial(), produto: "", qtd: "1", total: "0", precoUnit: "", cmvUnit: "" };
}

function emptyFaturarForm(): FaturarForm {
  return { filial: getFilial(), clienteCod: "", vencDias: "30" };
}

function emptyCancelarForm(): CancelarForm {
  return { filial: getFilial(), modo: "AUTO", reativarReserva: true };
}

function emptyEstornarForm(): EstornarForm {
  return { filial: getFilial(), motivo: "" };
}

function normalizePedido(row: unknown): PedidoResumo {
  const x = toRecord(row);
  return {
    id: toNumber(x.ID ?? x.id),
    filial: toStringValue(x.C5_FILIAL ?? x.filial, "01"),
    status: toStringValue(x.C5_STATUS ?? x.status, "ABERTO"),
    origem: toStringValue(x.C5_ORIGEM ?? x.origem, "VENDA"),
    valorTotal: toNumber(x.C5_VALOR_TOTAL ?? x.valor_total ?? x.total ?? x.valorTotal),
    data: toStringValue(x.C5_DATA ?? x.criado_em ?? x.data ?? ""),
    qtdItens: toNumber(x.qtd_itens ?? x.qtdItens ?? x.QTD_ITENS, 0),
  };
}

function normalizeItem(row: unknown): ItemResumo {
  const x = toRecord(row);
  return {
    id: toNumber(x.ID ?? x.id),
    pedidoId: toNumber(x.C6_PEDIDO_ID ?? x.pedido_id),
    produto: toStringValue(x.C6_PRODUTO ?? x.produto),
    qtd: toNumber(x.C6_QTD ?? x.qtd),
    total: toNumber(x.C6_TOTAL ?? x.total ?? x.C6_VALOR),
    precoUnit: toNumber(x.C6_PRECO_UNIT ?? x.preco_unit),
    cmvUnit: toNumber(x.C6_CMV_UNIT ?? x.cmv_unit),
    ativo: toStringValue(x.C6_ATIVO ?? x.ativo_sn ?? "1"),
  };
}

export function PedidosList() {
  const navigate = useNavigate();
  const [searchParams, setSearchParams] = useSearchParams();
  const [filialView, setFilialView] = useState(getFilial());
  const [status, setStatus] = useState("");
  const [origem, setOrigem] = useState("");
  const [de, setDe] = useState("");
  const [ate, setAte] = useState("");
  const [modoEnriquecido, setModoEnriquecido] = useState(false);

  const [rows, setRows] = useState<PedidoResumo[]>([]);
  const [total, setTotal] = useState(0);
  const [loading, setLoading] = useState(false);
  const [loadingItemProduto, setLoadingItemProduto] = useState(false);
  const [itemProdutoResultados, setItemProdutoResultados] = useState<ProdutoResumo[]>([]);
  const [loadingBuscaProdutoItem, setLoadingBuscaProdutoItem] = useState(false);
  const [err, setErr] = useState<string | null>(null);
  const [lastAction, setLastAction] = useState<Record<string, unknown> | null>(null);

  const [page, setPage] = useState(1);
  const [pageSize, setPageSize] = useState(10);
  const [sortKey, setSortKey] = useState<SortKey>("id");
  const [sortDir, setSortDir] = useState<SortDir>("desc");

  const [selectedPedidoId, setSelectedPedidoId] = useState<number | null>(null);
  const [pedidoDetalhe, setPedidoDetalhe] = useState<Record<string, unknown> | null>(null);
  const [itens, setItens] = useState<ItemResumo[]>([]);
  const [arResumo, setArResumo] = useState<Record<string, unknown> | null>(null);

  const [modalNovoPedido, setModalNovoPedido] = useState(false);
  const [pedidoForm, setPedidoForm] = useState<PedidoForm>(emptyPedidoForm());

  const [modalAddItem, setModalAddItem] = useState(false);
  const [itemForm, setItemForm] = useState<AddItemForm>(emptyItemForm());

  const [editItemId, setEditItemId] = useState<number | null>(null);
  const [modalEditItem, setModalEditItem] = useState(false);
  const [editItemForm, setEditItemForm] = useState<EditItemForm>({ filial: getFilial(), qtd: "1", total: "0", precoUnit: "", cmvUnit: "" });

  const [modalFaturar, setModalFaturar] = useState(false);
  const [faturarForm, setFaturarForm] = useState<FaturarForm>(emptyFaturarForm());

  const [modalCancelar, setModalCancelar] = useState(false);
  const [cancelarForm, setCancelarForm] = useState<CancelarForm>(emptyCancelarForm());

  const [modalEstornar, setModalEstornar] = useState(false);
  const [estornarForm, setEstornarForm] = useState<EstornarForm>(emptyEstornarForm());

  const [confirmState, setConfirmState] = useState<ConfirmState | null>(null);
  const alertFilter = searchParams.get("alert") ?? "";

  const alertLabelMap: Record<string, string> = {
    pedidos_no_items: "Exibindo apenas pedidos abertos sem itens.",
    pedidos_open: "Exibindo apenas pedidos abertos com itens aguardando faturamento.",
  };

  const offset = (page - 1) * pageSize;

  async function carregarPedidos() {
    setErr(null);
    setLoading(true);
    try {
      const params = {
        filial: filialView,
        status: status || undefined,
        origem: origem || undefined,
        de: de || undefined,
        ate: ate || undefined,
        limit: pageSize,
        offset,
      };
      const resp = modoEnriquecido ? await listarPedidosEnriquecido(params) : await listarPedidos(params);
      const items = Array.isArray(resp.items) ? resp.items : [];
      setRows(items.map(normalizePedido));
      setTotal(toNumber(resp.total, items.length));
    } catch (error: unknown) {
      setErr(getErrorMessage(error, "Erro ao carregar pedidos"));
    } finally {
      setLoading(false);
    }
  }

  async function carregarDetalhe(pedidoId: number) {
    setErr(null);
    setLoading(true);
    try {
      const resp = await obterPedido(pedidoId);
      const obj = toRecord(resp);
      const pedido = toRecord(obj.pedido ?? obj);
      const itensRaw = Array.isArray(obj.itens) ? obj.itens : [];
      const ar = toRecord(obj.ar_resumo);
      setSelectedPedidoId(pedidoId);
      setPedidoDetalhe(pedido);
      setItens(itensRaw.map(normalizeItem));
      setArResumo(Object.keys(ar).length ? ar : null);
    } catch (error: unknown) {
      setErr(getErrorMessage(error, "Erro ao obter pedido"));
    } finally {
      setLoading(false);
    }
  }

  useEffect(() => {
    carregarPedidos();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [filialView, status, origem, de, ate, page, pageSize, modoEnriquecido]);

  useEffect(() => {
    const unsub = onFilialChange((novaFilial) => {
      setFilialView(novaFilial);
      setPage(1);
      setSelectedPedidoId(null);
      setPedidoDetalhe(null);
      setItens([]);
      setArResumo(null);
      setPedidoForm(emptyPedidoForm());
      setItemForm(emptyItemForm());
      setFaturarForm(emptyFaturarForm());
      setCancelarForm(emptyCancelarForm());
      setEstornarForm(emptyEstornarForm());
    });
    return unsub;
  }, []);

  useEffect(() => {
    if (!alertFilter) return;
    setStatus("ABERTO");
    setPage(1);
    if (alertFilter === "pedidos_no_items" || alertFilter === "pedidos_open") {
      setModoEnriquecido(true);
    }
  }, [alertFilter]);

  const businessFilteredRows = useMemo(() => {
    if (alertFilter === "pedidos_no_items") {
      return rows.filter((row) => row.qtdItens === 0);
    }
    if (alertFilter === "pedidos_open") {
      return rows.filter((row) => row.qtdItens > 0);
    }
    return rows;
  }, [rows, alertFilter]);

  const sortedRows = useMemo(() => {
    const arr = [...businessFilteredRows];
    arr.sort((a, b) => {
      const av = sortKey === "id" || sortKey === "valorTotal" ? (a[sortKey] as number) : String(a[sortKey] ?? "").toLowerCase();
      const bv = sortKey === "id" || sortKey === "valorTotal" ? (b[sortKey] as number) : String(b[sortKey] ?? "").toLowerCase();
      if (av < bv) return sortDir === "asc" ? -1 : 1;
      if (av > bv) return sortDir === "asc" ? 1 : -1;
      return 0;
    });
    return arr;
  }, [businessFilteredRows, sortKey, sortDir]);

  const totalPages = Math.max(1, Math.ceil(sortedRows.length / pageSize));

  const totalValor = useMemo(
    () => sortedRows.reduce((acc, r) => acc + toNumber(r.valorTotal, 0), 0),
    [sortedRows]
  );

  const columns: Column<PedidoRow>[] = useMemo(
    () => [
      { key: "id", header: "ID", sortable: true },
      { key: "data", header: "Data", sortable: true },
      { key: "filial", header: "Filial", sortable: true, className: "hide-sm" },
      { key: "status", header: "Status", sortable: true, className: "hide-sm" },
      { key: "origem", header: "Origem", sortable: true, className: "hide-sm" },
      {
        key: "valorTotal",
        header: "Valor",
        sortable: true,
        render: (r) => toNumber(r.valorTotal).toLocaleString("pt-BR", { style: "currency", currency: "BRL" }),
      },
      {
        key: "acoes",
        header: "Acoes",
        width: 240,
        render: (r) => {
          const pedidoId = toNumber(r.id);
          return (
            <div className="row gap-10">
              <button className="btn" onClick={() => carregarDetalhe(pedidoId)}>Detalhar</button>
              <button className="btn" onClick={() => abrirModalAddItem(pedidoId)}>Add Item</button>
            </div>
          );
        },
      },
    ],
    []
  );

  function abrirModalAddItem(pedidoId: number) {
    setSelectedPedidoId(pedidoId);
    setItemForm(emptyItemForm());
    setItemProdutoResultados([]);
    setModalAddItem(true);
  }

  async function buscarProdutosParaItem(queryValue?: string) {
    const query = (queryValue ?? itemForm.produto).trim();
    if (!query) {
      setItemProdutoResultados([]);
      return;
    }
    setLoadingBuscaProdutoItem(true);
    try {
      const results = await buscarProdutos({ q: query, filial: itemForm.filial || filialView, limite: 8 });
      setItemProdutoResultados(results);
    } catch {
      setItemProdutoResultados([]);
    } finally {
      setLoadingBuscaProdutoItem(false);
    }
  }

  function usarProdutoNoItem(produto: ProdutoResumo) {
    setItemForm((current) => ({
      ...current,
      produto: produto.cod,
      cmvUnit: current.cmvUnit || String(produto.cm ?? 0),
    }));
    setItemProdutoResultados([]);
  }

  async function carregarCmvAtualProduto(produtoCod: string) {
    const cod = produtoCod.trim();
    if (!cod) return;
    setLoadingItemProduto(true);
    try {
      const results = await buscarProdutos({ q: cod, filial: itemForm.filial || filialView, limite: 8 });
      const match =
        results.find((item) => item.cod.trim().toUpperCase() === cod.toUpperCase()) ??
        results[0];
      if (!match) return;
      setItemForm((current) => ({
        ...current,
        produto: current.produto || match.cod,
        cmvUnit: current.cmvUnit || String(match.cm ?? 0),
      }));
    } catch {
      // mantem fluxo manual do operador se a consulta falhar
    } finally {
      setLoadingItemProduto(false);
    }
  }

  function abrirModalEditItem(itemId: number, row: Record<string, unknown>) {
    setEditItemId(itemId);
    setEditItemForm({
      filial: toStringValue(row.filial, filialView),
      qtd: String(toNumber(row.qtd, 1)),
      total: String(toNumber(row.total, 0)),
      precoUnit: String(toNumber(row.precoUnit, 0)),
      cmvUnit: String(toNumber(row.cmvUnit, 0)),
    });
    setModalEditItem(true);
  }

  async function onCriarPedido() {
    setErr(null);
    setLoading(true);
    try {
      const resp = await criarPedido({
        filial: pedidoForm.filial || filialView,
        valor_total: toNumber(pedidoForm.valorTotal, 0),
        icms: pedidoForm.icms ? toNumber(pedidoForm.icms) : null,
        ipi: pedidoForm.ipi ? toNumber(pedidoForm.ipi) : null,
        total_bruto: pedidoForm.totalBruto ? toNumber(pedidoForm.totalBruto) : null,
      });
      setLastAction(toRecord(resp));
      setModalNovoPedido(false);
      await carregarPedidos();
    } catch (error: unknown) {
      setErr(getErrorMessage(error, "Erro ao criar pedido"));
    } finally {
      setLoading(false);
    }
  }

  async function onAdicionarItem() {
    if (!selectedPedidoId) return;
    setErr(null);
    setLoading(true);
    try {
      const resp = await adicionarItem(selectedPedidoId, {
        filial: itemForm.filial || filialView,
        produto: itemForm.produto,
        qtd: toNumber(itemForm.qtd, 1),
        total: toNumber(itemForm.total, 0),
        preco_unit: itemForm.precoUnit ? toNumber(itemForm.precoUnit) : null,
        cmv_unit: itemForm.cmvUnit ? toNumber(itemForm.cmvUnit) : null,
      });
      setLastAction(toRecord(resp));
      setModalAddItem(false);
      await carregarPedidos();
      await carregarDetalhe(selectedPedidoId);
    } catch (error: unknown) {
      setErr(getErrorMessage(error, "Erro ao adicionar item"));
    } finally {
      setLoading(false);
    }
  }

  async function onEditarItem() {
    if (!editItemId || !selectedPedidoId) return;
    setErr(null);
    setLoading(true);
    try {
      const resp = await editarItem(editItemId, {
        filial: editItemForm.filial || filialView,
        qtd: toNumber(editItemForm.qtd, 1),
        total: toNumber(editItemForm.total, 0),
        preco_unit: editItemForm.precoUnit ? toNumber(editItemForm.precoUnit) : null,
        cmv_unit: editItemForm.cmvUnit ? toNumber(editItemForm.cmvUnit) : null,
      });
      setLastAction(toRecord(resp));
      setModalEditItem(false);
      await carregarPedidos();
      await carregarDetalhe(selectedPedidoId);
    } catch (error: unknown) {
      setErr(getErrorMessage(error, "Erro ao editar item"));
    } finally {
      setLoading(false);
    }
  }

  function confirmarExcluirItem(itemId: number) {
    setConfirmState({
      title: "Excluir item",
      message: `Deseja excluir o item ${itemId}?`,
      danger: true,
      confirmText: "Excluir",
      run: async () => {
        if (!selectedPedidoId) return;
        const resp = await excluirItem(itemId, { filial: filialView });
        setLastAction(toRecord(resp));
        await carregarPedidos();
        await carregarDetalhe(selectedPedidoId);
      },
    });
  }

  async function onFaturarPedido() {
    if (!selectedPedidoId) return;
    setErr(null);
    setLoading(true);
    try {
      const payload: FaturarPedidoInput = {
        filial: faturarForm.filial || filialView,
        cliente_cod: faturarForm.clienteCod || null,
        venc_dias: toNumber(faturarForm.vencDias, 30),
      };
      const resp = await faturarPedido(selectedPedidoId, payload);
      setLastAction(toRecord(resp));
      setModalFaturar(false);
      await carregarPedidos();
      await carregarDetalhe(selectedPedidoId);
    } catch (error: unknown) {
      setErr(getErrorMessage(error, "Erro ao faturar pedido"));
    } finally {
      setLoading(false);
    }
  }

  async function onCancelarPedido() {
    if (!selectedPedidoId) return;
    setErr(null);
    setLoading(true);
    try {
      const payload: CancelarPedidoInput = {
        filial: cancelarForm.filial || filialView,
        modo: cancelarForm.modo,
        reativar_reserva: cancelarForm.reativarReserva,
      };
      const resp = await cancelarPedido(selectedPedidoId, payload);
      setLastAction(toRecord(resp));
      setModalCancelar(false);
      await carregarPedidos();
      await carregarDetalhe(selectedPedidoId);
    } catch (error: unknown) {
      setErr(getErrorMessage(error, "Erro ao cancelar pedido"));
    } finally {
      setLoading(false);
    }
  }

  async function onRecalcularPedido() {
    if (!selectedPedidoId) return;
    setErr(null);
    setLoading(true);
    try {
      const resp = await recalcularPedido(selectedPedidoId, { forcar: false });
      setLastAction(toRecord(resp));
      await carregarPedidos();
      await carregarDetalhe(selectedPedidoId);
    } catch (error: unknown) {
      setErr(getErrorMessage(error, "Erro ao recalcular pedido"));
    } finally {
      setLoading(false);
    }
  }

  async function onEstornarPedido() {
    if (!selectedPedidoId) return;
    setErr(null);
    setLoading(true);
    try {
      const payload: EstornarPedidoInput = {
        filial: estornarForm.filial || filialView,
        motivo: estornarForm.motivo || null,
      };
      const resp = await estornarPedido(selectedPedidoId, payload);
      setLastAction(toRecord(resp));
      setModalEstornar(false);
      await carregarPedidos();
      await carregarDetalhe(selectedPedidoId);
    } catch (error: unknown) {
      setErr(getErrorMessage(error, "Erro ao estornar pedido"));
    } finally {
      setLoading(false);
    }
  }

  async function confirmarAcaoAtual() {
    if (!confirmState) return;
    setErr(null);
    setLoading(true);
    try {
      await confirmState.run();
      setConfirmState(null);
    } catch (error: unknown) {
      setErr(getErrorMessage(error, "Falha na operacao"));
    } finally {
      setLoading(false);
    }
  }

  return (
    <>
      <PageHero
        icon={ordersIcon}
        backgroundImage={ordersBg}
        backgroundPosition="center 46%"
        eyebrow="Comercial"
        title="Pedidos de venda"
        description="Controle de criacao, itens, faturamento, cancelamento e estorno em uma unica trilha operacional."
        metrics={[
          { label: "Filial", value: filialView },
          { label: "Pedidos", value: String(sortedRows.length) },
          { label: "Modo", value: modoEnriquecido ? "Enriquecido" : "Simples" },
        ]}
        actions={
          <>
            <button className="btn primary" onClick={() => { setPedidoForm(emptyPedidoForm()); setModalNovoPedido(true); }}>
              Novo pedido
            </button>
            <button className="btn" onClick={() => { setModoEnriquecido((v) => !v); setPage(1); }}>
              Alternar modo
            </button>
          </>
        }
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
        left={<div className="hint">Filial: <b>{filialView}</b></div>}
        right={
          <>
            <select className="select" value={modoEnriquecido ? "enriquecido" : "simples"} onChange={(e) => {
              setModoEnriquecido(e.target.value === "enriquecido");
              setPage(1);
            }}>
              <option value="simples">Lista simples</option>
              <option value="enriquecido">Lista enriquecida</option>
            </select>
            <select className="select" value={status} onChange={(e) => { setStatus(e.target.value); setPage(1); }}>
              <option value="">Status: todos</option>
              <option value="ABERTO">ABERTO</option>
              <option value="FATURADO">FATURADO</option>
              <option value="CANCELADO">CANCELADO</option>
            </select>
            <select className="select" value={origem} onChange={(e) => { setOrigem(e.target.value); setPage(1); }}>
              <option value="">Origem: todas</option>
              <option value="VENDA">VENDA</option>
              <option value="RESERVA">RESERVA</option>
            </select>
            <input className="input" type="date" value={de} onChange={(e) => { setDe(e.target.value); setPage(1); }} />
            <input className="input" type="date" value={ate} onChange={(e) => { setAte(e.target.value); setPage(1); }} />
            <button className="btn" onClick={() => { setPage(1); carregarPedidos(); }} disabled={loading}>Aplicar</button>
            <button
              className="btn ghost"
              onClick={() => {
                setStatus("");
                setOrigem("");
                setDe("");
                setAte("");
                setPage(1);
              }}
              disabled={loading}
            >
              Limpar
            </button>
            <button className="btn primary" onClick={() => { setPedidoForm(emptyPedidoForm()); setModalNovoPedido(true); }}>Novo pedido</button>
          </>
        }
      />

      {err && <div className="alert mt-12">{err}</div>}

      <div className="section-title">Resumo</div>
      <div className="stats-grid">
        <div className="stat-card">
          <div>
            <div className="kpi-label">Pedidos (total)</div>
            <div className="kpi">{total}</div>
          </div>
          <div className="stat-icon">PD</div>
        </div>
        <div className="stat-card">
          <div>
            <div className="kpi-label">Valor na pagina</div>
            <div className="kpi">
              {totalValor.toLocaleString("pt-BR", { style: "currency", currency: "BRL" })}
            </div>
          </div>
          <div className="stat-icon success">R$</div>
        </div>
        <div className="stat-card">
          <div>
            <div className="kpi-label">Modo</div>
            <div className="kpi">{modoEnriquecido ? "Enriq." : "Simples"}</div>
          </div>
          <div className="stat-icon solid">MD</div>
        </div>
      </div>

      <Pager
        page={page}
        totalPages={totalPages}
        pageSize={pageSize}
        totalItems={sortedRows.length}
        onPageChange={setPage}
        onPageSizeChange={(size) => { setPageSize(size); setPage(1); }}
        showPageSize
      />

      <DataTable
        rows={sortedRows as unknown as PedidoRow[]}
        columns={columns}
        sortKey={sortKey}
        sortDir={sortDir}
        className="compact"
        wrapperClassName="table-scroller"
        onSortChange={(k, d) => { setSortKey(k as SortKey); setSortDir(d); }}
        loading={loading}
        emptyText="Nenhum pedido encontrado."
      />

      <PedidoDetalhePanel
        selectedPedidoId={selectedPedidoId}
        loading={loading}
        pedidoDetalhe={pedidoDetalhe}
        arResumo={arResumo}
        itens={itens}
        onRecalcularPedido={onRecalcularPedido}
        onAbrirFaturar={() => {
          setFaturarForm(emptyFaturarForm());
          setModalFaturar(true);
        }}
        onAbrirCancelar={() => {
          setCancelarForm(emptyCancelarForm());
          setModalCancelar(true);
        }}
        onAbrirEstornar={() => {
          setEstornarForm(emptyEstornarForm());
          setModalEstornar(true);
        }}
        onAbrirAddItem={() => {
          if (selectedPedidoId) abrirModalAddItem(selectedPedidoId);
        }}
        onAbrirEditItem={abrirModalEditItem}
        onConfirmarExcluirItem={confirmarExcluirItem}
        onAbrirCustoItem={(produtoCod) => {
          if (!produtoCod) return;
          navigate(`/custos/fornecedor?produto=${encodeURIComponent(produtoCod)}`);
        }}
      />

      {lastAction && (
        <div className="card mt-12">
          <div style={{ fontWeight: 700 }}>Ultima resposta da API</div>
          <pre style={{ margin: 0, whiteSpace: "pre-wrap" }}>{JSON.stringify(lastAction, null, 2)}</pre>
        </div>
      )}

      {modalNovoPedido && (
        <Modal title="Criar pedido" onClose={() => setModalNovoPedido(false)}>
          <div className="form-grid">
            <div className="form-field"><label>Filial</label><input value={pedidoForm.filial} onChange={(e) => setPedidoForm({ ...pedidoForm, filial: e.target.value })} /></div>
            <div className="form-field"><label>Valor total</label><input type="number" step="0.01" value={pedidoForm.valorTotal} onChange={(e) => setPedidoForm({ ...pedidoForm, valorTotal: e.target.value })} /></div>
            <div className="form-field"><label>ICMS (opcional)</label><input type="number" step="0.01" value={pedidoForm.icms} onChange={(e) => setPedidoForm({ ...pedidoForm, icms: e.target.value })} /></div>
            <div className="form-field"><label>IPI (opcional)</label><input type="number" step="0.01" value={pedidoForm.ipi} onChange={(e) => setPedidoForm({ ...pedidoForm, ipi: e.target.value })} /></div>
            <div className="form-field"><label>Total bruto (opcional)</label><input type="number" step="0.01" value={pedidoForm.totalBruto} onChange={(e) => setPedidoForm({ ...pedidoForm, totalBruto: e.target.value })} /></div>
          </div>
          <div className="form-actions">
            <button className="btn" onClick={() => setModalNovoPedido(false)} disabled={loading}>Cancelar</button>
            <button className="btn primary" onClick={onCriarPedido} disabled={loading}>Criar</button>
          </div>
        </Modal>
      )}

      {modalAddItem && (
        <Modal title={`Adicionar item ao pedido ${selectedPedidoId ?? ""}`} onClose={() => setModalAddItem(false)}>
      <div className="form-grid">
        <div className="form-field"><label>Filial</label><input value={itemForm.filial} onChange={(e) => setItemForm({ ...itemForm, filial: e.target.value })} /></div>
            <div className="form-field">
              <label>Produto</label>
              <div className="row gap-10">
                <input
                  value={itemForm.produto}
                  onChange={(e) => {
                    const next = e.target.value;
                    setItemForm({ ...itemForm, produto: next });
                    if (!next.trim()) setItemProdutoResultados([]);
                  }}
                  onBlur={() => carregarCmvAtualProduto(itemForm.produto)}
                />
                <button
                  type="button"
                  className="btn"
                  disabled={loadingBuscaProdutoItem || !itemForm.produto.trim()}
                  onClick={() => buscarProdutosParaItem(itemForm.produto)}
                >
                  {loadingBuscaProdutoItem ? "Buscando..." : "Buscar"}
                </button>
                <button
                  type="button"
                  className="btn"
                  disabled={loadingItemProduto || !itemForm.produto.trim()}
                  onClick={() => carregarCmvAtualProduto(itemForm.produto)}
                >
                  {loadingItemProduto ? "Carregando..." : "CM atual"}
                </button>
              </div>
              {itemProdutoResultados.length > 0 ? (
                <div className="search-results-panel mt-12">
                  <table className="inline-search-table">
                    <thead>
                      <tr>
                        <th>Codigo</th>
                        <th>Descricao</th>
                        <th>CM Atual</th>
                        <th>Estoque</th>
                        <th></th>
                      </tr>
                    </thead>
                    <tbody>
                      {itemProdutoResultados.map((produto) => (
                        <tr key={`${produto.filial ?? "01"}:${produto.cod}`}>
                          <td>{produto.cod}</td>
                          <td>{produto.desc}</td>
                          <td>{Number(produto.cm ?? 0).toLocaleString("pt-BR", { style: "currency", currency: "BRL" })}</td>
                          <td>{Number(produto.estoque ?? 0)}</td>
                          <td>
                            <button type="button" className="btn" onClick={() => usarProdutoNoItem(produto)}>
                              Usar produto
                            </button>
                          </td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              ) : null}
            </div>
        <div className="form-field"><label>Qtd</label><input type="number" value={itemForm.qtd} onChange={(e) => setItemForm({ ...itemForm, qtd: e.target.value })} /></div>
        <div className="form-field"><label>Total</label><input type="number" step="0.01" value={itemForm.total} onChange={(e) => setItemForm({ ...itemForm, total: e.target.value })} /></div>
        <div className="form-field"><label>Preco unit (opcional)</label><input type="number" step="0.01" value={itemForm.precoUnit} onChange={(e) => setItemForm({ ...itemForm, precoUnit: e.target.value })} /></div>
            <div className="form-field">
              <label>CMV unit (opcional)</label>
              <input
                type="number"
                step="0.01"
                value={itemForm.cmvUnit}
                onChange={(e) => setItemForm({ ...itemForm, cmvUnit: e.target.value })}
              />
              <div className="hint">Se vazio, o faturamento usa o B1_CM do produto. Se preenchido, usa o CMV do item.</div>
            </div>
      </div>
          <div className="form-actions">
            <button className="btn" onClick={() => setModalAddItem(false)} disabled={loading}>Cancelar</button>
            <button className="btn primary" onClick={onAdicionarItem} disabled={loading}>Adicionar</button>
          </div>
        </Modal>
      )}

      {modalEditItem && (
        <Modal title={`Editar item ${editItemId ?? ""}`} onClose={() => setModalEditItem(false)}>
      <div className="form-grid">
        <div className="form-field"><label>Filial</label><input value={editItemForm.filial} onChange={(e) => setEditItemForm({ ...editItemForm, filial: e.target.value })} /></div>
        <div className="form-field"><label>Qtd</label><input type="number" value={editItemForm.qtd} onChange={(e) => setEditItemForm({ ...editItemForm, qtd: e.target.value })} /></div>
        <div className="form-field"><label>Total</label><input type="number" step="0.01" value={editItemForm.total} onChange={(e) => setEditItemForm({ ...editItemForm, total: e.target.value })} /></div>
        <div className="form-field"><label>Preco unit (opcional)</label><input type="number" step="0.01" value={editItemForm.precoUnit} onChange={(e) => setEditItemForm({ ...editItemForm, precoUnit: e.target.value })} /></div>
        <div className="form-field"><label>CMV unit (opcional)</label><input type="number" step="0.01" value={editItemForm.cmvUnit} onChange={(e) => setEditItemForm({ ...editItemForm, cmvUnit: e.target.value })} /></div>
      </div>
          <div className="form-actions">
            <button className="btn" onClick={() => setModalEditItem(false)} disabled={loading}>Cancelar</button>
            <button className="btn primary" onClick={onEditarItem} disabled={loading}>Salvar</button>
          </div>
        </Modal>
      )}

      {modalFaturar && (
        <Modal title={`Faturar pedido ${selectedPedidoId ?? ""}`} onClose={() => setModalFaturar(false)}>
          <div className="form-grid">
            <div className="form-field"><label>Filial</label><input value={faturarForm.filial} onChange={(e) => setFaturarForm({ ...faturarForm, filial: e.target.value })} /></div>
            <div className="form-field"><label>Cliente cod (opcional)</label><input value={faturarForm.clienteCod} onChange={(e) => setFaturarForm({ ...faturarForm, clienteCod: e.target.value })} /></div>
            <div className="form-field"><label>Vencimento (dias)</label><input type="number" value={faturarForm.vencDias} onChange={(e) => setFaturarForm({ ...faturarForm, vencDias: e.target.value })} /></div>
          </div>
          <div className="form-actions">
            <button className="btn" onClick={() => setModalFaturar(false)} disabled={loading}>Cancelar</button>
            <button className="btn primary" onClick={onFaturarPedido} disabled={loading}>Faturar</button>
          </div>
        </Modal>
      )}

      {modalCancelar && (
        <Modal title={`Cancelar pedido ${selectedPedidoId ?? ""}`} onClose={() => setModalCancelar(false)}>
          <div className="form-grid">
            <div className="form-field"><label>Filial</label><input value={cancelarForm.filial} onChange={(e) => setCancelarForm({ ...cancelarForm, filial: e.target.value })} /></div>
            <div className="form-field"><label>Modo</label><select value={cancelarForm.modo} onChange={(e) => setCancelarForm({ ...cancelarForm, modo: e.target.value as CancelarForm["modo"] })}><option value="AUTO">AUTO</option><option value="SIMPLES">SIMPLES</option><option value="ESTORNAR">ESTORNAR</option></select></div>
            <div className="form-field"><label>Reativar reserva</label><select value={cancelarForm.reativarReserva ? "true" : "false"} onChange={(e) => setCancelarForm({ ...cancelarForm, reativarReserva: e.target.value === "true" })}><option value="true">true</option><option value="false">false</option></select></div>
          </div>
          <div className="form-actions">
            <button className="btn" onClick={() => setModalCancelar(false)} disabled={loading}>Voltar</button>
            <button className="btn danger" onClick={onCancelarPedido} disabled={loading}>Cancelar pedido</button>
          </div>
        </Modal>
      )}

      {modalEstornar && (
        <Modal title={`Estornar pedido ${selectedPedidoId ?? ""}`} onClose={() => setModalEstornar(false)}>
          <div className="form-grid">
            <div className="form-field"><label>Filial</label><input value={estornarForm.filial} onChange={(e) => setEstornarForm({ ...estornarForm, filial: e.target.value })} /></div>
            <div className="form-field col-span-all"><label>Motivo (opcional)</label><input value={estornarForm.motivo} onChange={(e) => setEstornarForm({ ...estornarForm, motivo: e.target.value })} /></div>
          </div>
          <div className="form-actions">
            <button className="btn" onClick={() => setModalEstornar(false)} disabled={loading}>Voltar</button>
            <button className="btn danger" onClick={onEstornarPedido} disabled={loading}>Estornar</button>
          </div>
        </Modal>
      )}

      {confirmState && (
        <ConfirmDialog
          title={confirmState.title}
          message={confirmState.message}
          danger={confirmState.danger}
          confirmText={confirmState.confirmText}
          loading={loading}
          onClose={() => setConfirmState(null)}
          onConfirm={confirmarAcaoAtual}
        />
      )}
      </div>
    </>
  );
}
