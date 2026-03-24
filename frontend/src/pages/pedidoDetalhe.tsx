import { DataTable, type Column } from "../components/DataTable";

type ItemResumo = {
  id: number;
  pedidoId: number;
  produto: string;
  qtd: number;
  total: number;
  precoUnit: number;
  cmvUnit: number;
  ativo: string;
};

type ItemRow = Record<string, unknown>;

type Props = {
  selectedPedidoId: number | null;
  loading: boolean;
  pedidoDetalhe: Record<string, unknown> | null;
  arResumo: Record<string, unknown> | null;
  itens: ItemResumo[];
  onRecalcularPedido: () => void;
  onAbrirFaturar: () => void;
  onAbrirCancelar: () => void;
  onAbrirEstornar: () => void;
  onAbrirAddItem: () => void;
  onAbrirEditItem: (itemId: number, row: ItemRow) => void;
  onConfirmarExcluirItem: (itemId: number) => void;
  onAbrirCustoItem: (produtoCod: string) => void;
};

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

export function PedidoDetalhePanel({
  selectedPedidoId,
  loading,
  pedidoDetalhe,
  arResumo,
  itens,
  onRecalcularPedido,
  onAbrirFaturar,
  onAbrirCancelar,
  onAbrirEstornar,
  onAbrirAddItem,
  onAbrirEditItem,
  onConfirmarExcluirItem,
  onAbrirCustoItem,
}: Props) {
  const itemColumns: Column<ItemRow>[] = [
    { key: "id", header: "Item ID", sortable: true },
    { key: "produto", header: "Produto", sortable: true },
    { key: "qtd", header: "Qtd", sortable: true },
    {
      key: "total",
      header: "Total",
      sortable: true,
      render: (r) => toNumber(r.total).toLocaleString("pt-BR", { style: "currency", currency: "BRL" }),
    },
    {
      key: "precoUnit",
      header: "Preco Unit",
      sortable: true,
      className: "hide-sm",
      render: (r) => toNumber(r.precoUnit).toLocaleString("pt-BR", { style: "currency", currency: "BRL" }),
    },
    {
      key: "cmvUnit",
      header: "CMV Unit",
      sortable: true,
      className: "hide-sm",
      render: (r) => toNumber(r.cmvUnit).toLocaleString("pt-BR", { style: "currency", currency: "BRL" }),
    },
    {
      key: "acoes",
      header: "Acoes",
      width: 320,
      render: (r) => {
        const itemId = toNumber(r.id);
        const produtoCod = toStringValue(r.produto, "");
        return (
          <div className="row gap-10">
            <button className="btn" onClick={() => onAbrirEditItem(itemId, r)}>Editar</button>
            <button className="btn" onClick={() => onAbrirCustoItem(produtoCod)}>Custo</button>
            <button className="btn danger" onClick={() => onConfirmarExcluirItem(itemId)}>Excluir</button>
          </div>
        );
      },
    },
  ];

  return (
    <div className="card mt-12">
      <div className="row-between">
        <div>
          <div style={{ fontWeight: 700 }}>Detalhe do pedido</div>
          <div className="hint">{selectedPedidoId ? `Pedido selecionado: ${selectedPedidoId}` : "Selecione um pedido na tabela"}</div>
        </div>
        <div className="row gap-10">
          <button className="btn" disabled={!selectedPedidoId || loading} onClick={onRecalcularPedido}>Recalcular</button>
          <button className="btn" disabled={!selectedPedidoId || loading} onClick={onAbrirFaturar}>Faturar</button>
          <button className="btn danger" disabled={!selectedPedidoId || loading} onClick={onAbrirCancelar}>Cancelar</button>
          <button className="btn danger" disabled={!selectedPedidoId || loading} onClick={onAbrirEstornar}>Estornar</button>
        </div>
      </div>

      {pedidoDetalhe && (
        <div className="mt-12">
          <div className="hint">Status: <b>{toStringValue(pedidoDetalhe.C5_STATUS, "-")}</b> | Origem: <b>{toStringValue(pedidoDetalhe.C5_ORIGEM, "-")}</b></div>
          <div className="hint">Filial: <b>{toStringValue(pedidoDetalhe.C5_FILIAL, "-")}</b> | Total: <b>{toNumber(pedidoDetalhe.C5_VALOR_TOTAL).toLocaleString("pt-BR", { style: "currency", currency: "BRL" })}</b></div>
          {arResumo && <div className="hint">AR: <b>{toStringValue(arResumo.status, "-")}</b> | Valor: <b>{toNumber(arResumo.valor).toLocaleString("pt-BR", { style: "currency", currency: "BRL" })}</b></div>}
        </div>
      )}

      <div className="section-title">Resumo</div>
      <div className="stats-grid">
        <div className="stat-card">
          <div>
            <div className="kpi-label">Itens</div>
            <div className="kpi">{itens.length}</div>
          </div>
          <div className="stat-icon">IT</div>
        </div>
        <div className="stat-card">
          <div>
            <div className="kpi-label">Total dos itens</div>
            <div className="kpi">
              {itens.reduce((acc, x) => acc + toNumber(x.total, 0), 0).toLocaleString("pt-BR", { style: "currency", currency: "BRL" })}
            </div>
          </div>
          <div className="stat-icon success">R$</div>
        </div>
        <div className="stat-card">
          <div>
            <div className="kpi-label">Status</div>
            <div className="kpi">{toStringValue(pedidoDetalhe?.C5_STATUS ?? "-", "-")}</div>
          </div>
          <div className="stat-icon solid">ST</div>
        </div>
      </div>

      <div className="row-between mt-12">
        <div style={{ fontWeight: 700 }}>Itens do pedido</div>
        <button className="btn primary" disabled={!selectedPedidoId || loading} onClick={onAbrirAddItem}>Adicionar item</button>
      </div>

      <DataTable
        rows={itens as unknown as ItemRow[]}
        columns={itemColumns}
        sortKey="id"
        sortDir="asc"
        className="compact"
        wrapperClassName="table-scroller"
        onSortChange={() => undefined}
        loading={loading}
        emptyText="Sem itens."
      />
    </div>
  );
}
