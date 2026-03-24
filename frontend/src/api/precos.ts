import { http } from "./http";

function qs(params: Record<string, unknown>) {
  const sp = new URLSearchParams();
  Object.entries(params).forEach(([k, v]) => {
    if (v === undefined || v === null || v === "") return;
    sp.set(k, String(v));
  });
  return sp.toString();
}

export type TabelaPreco = {
  id: number;
  filial: string;
  codigo: string;
  descricao: string;
  ativa: boolean;
};

export type ItemPrecoTabela = {
  id: number;
  filial: string;
  tabela_id: number;
  produto: string;
  preco: number;
  dt_ini: string | null;
  dt_fim: string | null;
  vigente: boolean;
};

export async function listarTabelasPreco(params: { filial?: string } = {}) {
  const query = qs(params);
  return http<TabelaPreco[]>(`/precos/tabelas${query ? `?${query}` : ""}`);
}

export async function criarTabelaPreco(payload: { codigo: string; descricao: string; filial?: string }) {
  const { filial, ...body } = payload;
  const query = qs({ filial });
  return http<Record<string, unknown>>(`/precos/tabelas${query ? `?${query}` : ""}`, {
    method: "POST",
    body,
  });
}

export async function listarItensTabelaPreco(tabelaId: number, params: { filial?: string } = {}) {
  const query = qs(params);
  return http<ItemPrecoTabela[]>(`/precos/tabelas/${tabelaId}/itens${query ? `?${query}` : ""}`);
}

export async function definirPrecoTabela(payload: {
  tabela_id: number;
  produto: string;
  preco: number;
  dt_ini: string;
  filial?: string;
}) {
  const { filial, ...body } = payload;
  const query = qs({ filial });
  return http<Record<string, unknown>>(`/precos/definir${query ? `?${query}` : ""}`, {
    method: "POST",
    body,
  });
}

export async function buscarPrecoTabela(params: {
  produto: string;
  tabela_id: number;
  data: string;
  filial?: string;
}) {
  const query = qs(params);
  return http<Record<string, unknown>>(`/precos/buscar${query ? `?${query}` : ""}`);
}
