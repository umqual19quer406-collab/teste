import { http } from "../http";

export type DreLinha = {
  grupo?: string | null;
  valor?: number | null;
  [k: string]: unknown;
};

export type DreResponse = {
  filial: string;
  de?: string | null;
  ate?: string | null;
  linhas: DreLinha[];
  total: number;
};

function qs(params: Record<string, unknown>) {
  const sp = new URLSearchParams();
  Object.entries(params).forEach(([k, v]) => {
    if (v === undefined || v === null || v === "") return;
    sp.set(k, String(v));
  });
  return sp.toString();
}

export async function obterDre(params: { filial?: string; de?: string | null; ate?: string | null } = {}) {
  const query = qs(params);
  return http<DreResponse>(`/financeiro/relatorios/dre${query ? `?${query}` : ""}`);
}
