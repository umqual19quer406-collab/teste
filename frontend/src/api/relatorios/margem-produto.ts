import { http } from "../http";

export type MargemProdutoRow = {
  produto: string;
  receita: number;
  cmv: number;
  margem: number;
  [k: string]: unknown;
};

function qs(params: Record<string, unknown>) {
  const sp = new URLSearchParams();
  Object.entries(params).forEach(([k, v]) => {
    if (v === undefined || v === null || v === "") return;
    sp.set(k, String(v));
  });
  return sp.toString();
}

export async function obterMargemProduto(params: { filial?: string; de?: string | null; ate?: string | null } = {}) {
  const query = qs(params);
  return http<MargemProdutoRow[]>(`/relatorios/margem-produto${query ? `?${query}` : ""}`);
}
