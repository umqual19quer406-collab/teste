import { http } from "./http";

export type PedidoStatus = "ABERTO" | "RESERVA_CRIADA" | "RESERVA_FATURADA" | "CANCELADO";

export type Pedido = {
  id: number;
  filial: string;
  cliente_cod?: string | null;
  status?: PedidoStatus | string;
  origem?: string | null;
  total?: number | null;
  total_bruto?: number | null;
  icms?: number | null;
  ipi?: number | null;
  criado_em?: string | null;
  atualizado_em?: string | null;
  [k: string]: unknown;
};

export type PedidoEnriquecido = Pedido & {
  cliente_nome?: string | null;
  itens?: ItemPedido[];
  [k: string]: unknown;
};

export type ItemPedido = {
  id: number;
  pedido_id: number;
  filial: string;
  produto: string;
  qtd: number;
  total: number;
  preco_unit?: number | null;
  cmv_unit?: number | null;
  status?: string;
  ativo_sn?: "S" | "N";
  [k: string]: unknown;
};

export type PedidoCriarInput = {
  filial: string;
  valor_total: number;
  status?: string;
  icms?: number | null;
  ipi?: number | null;
  total_bruto?: number | null;
};

export type ItemCriarInput = {
  filial: string;
  produto: string;
  qtd: number;
  total: number;
  preco_unit?: number | null;
  cmv_unit?: number | null;
};

export type FaturarPedidoInput = {
  filial: string;
  cliente_cod?: string | null;
  venc_dias?: number;
};

export type CancelarPedidoInput = {
  filial: string;
  modo?: "AUTO" | "MANUAL" | string;
  reativar_reserva?: boolean;
};

export type RecalcularPedidoInput = {
  forcar?: boolean;
};

export type EditarItemInput = {
  filial: string;
  qtd: number;
  total: number;
  preco_unit?: number | null;
  cmv_unit?: number | null;
};

export type ExcluirItemInput = {
  filial: string;
};

export type EstornarPedidoInput = {
  filial: string;
  motivo?: string | null;
};

export type PagedResponse<T> = {
  total: number;
  limit: number;
  offset: number;
  items: T[];
};

function qs(params: Record<string, unknown>) {
  const sp = new URLSearchParams();
  Object.entries(params).forEach(([k, v]) => {
    if (v === undefined || v === null || v === "") return;
    sp.set(k, String(v));
  });
  return sp.toString();
}

export async function criarPedido(payload: PedidoCriarInput) {
  return http<Pedido>("/vendas/pedidos", { method: "POST", body: payload });
}

export async function listarPedidos(
  params: {
    filial?: string;
    status?: string;
    origem?: string;
    de?: string;
    ate?: string;
    limit?: number;
    offset?: number;
  } = {}
) {
  const query = qs(params);
  return http<PagedResponse<Pedido>>(`/vendas/pedidos${query ? `?${query}` : ""}`);
}

export async function listarPedidosEnriquecido(
  params: {
    filial?: string;
    status?: string;
    origem?: string;
    de?: string;
    ate?: string;
    limit?: number;
    offset?: number;
  } = {}
) {
  const query = qs(params);
  return http<PagedResponse<PedidoEnriquecido>>(`/vendas/pedidos/enriquecido${query ? `?${query}` : ""}`);
}

export async function obterPedido(pedidoId: number) {
  return http<PedidoEnriquecido | Pedido>(`/vendas/pedidos/${encodeURIComponent(String(pedidoId))}`);
}

export async function adicionarItem(pedidoId: number, payload: ItemCriarInput) {
  return http<{ pedido_id: number; item_id: number; novo_total?: number; qtd_itens?: number }>(
    `/vendas/pedidos/${encodeURIComponent(String(pedidoId))}/itens`,
    { method: "POST", body: payload }
  );
}

export async function editarItem(itemId: number, payload: EditarItemInput) {
  return http<{ pedido_id: number; item_id: number; novo_total?: number; qtd_itens?: number }>(
    `/vendas/itens/${encodeURIComponent(String(itemId))}`,
    { method: "PUT", body: payload }
  );
}

export async function excluirItem(itemId: number, payload: ExcluirItemInput) {
  return http<{ pedido_id: number; item_id: number; novo_total?: number; qtd_itens?: number }>(
    `/vendas/itens/${encodeURIComponent(String(itemId))}`,
    { method: "DELETE", body: payload }
  );
}

export async function recalcularPedido(pedidoId: number, payload: RecalcularPedidoInput = {}) {
  return http<{ pedido_id: number; novo_total?: number; qtd_itens?: number }>(
    `/vendas/pedidos/${encodeURIComponent(String(pedidoId))}/recalcular`,
    { method: "POST", body: payload }
  );
}

export async function faturarPedido(pedidoId: number, payload: FaturarPedidoInput) {
  return http<Record<string, unknown>>(
    `/vendas/pedidos/${encodeURIComponent(String(pedidoId))}/faturar`,
    { method: "POST", body: payload }
  );
}

export async function cancelarPedido(pedidoId: number, payload: CancelarPedidoInput) {
  return http<Record<string, unknown>>(
    `/vendas/pedidos/${encodeURIComponent(String(pedidoId))}/cancelar`,
    { method: "POST", body: payload }
  );
}

export async function estornarPedido(pedidoId: number, payload: EstornarPedidoInput) {
  return http<Record<string, unknown>>(
    `/vendas/pedidos/${encodeURIComponent(String(pedidoId))}/estornar`,
    { method: "POST", body: payload }
  );
}
