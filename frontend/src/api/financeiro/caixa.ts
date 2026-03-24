import { http } from "../http";

export type CaixaConta = {
  ID: number;
  E5_FILIAL?: string | null;
  E5_NOME?: string | null;
  E5_TIPO?: string | null;
  E5_ATIVA?: number | boolean | null;
  [k: string]: unknown;
};

export type CaixaMovimento = {
  ID: number;
  E5_DATA?: string | null;
  E5_FILIAL?: string | null;
  E5_CONTA_ID?: number | null;
  E5_TIPO?: string | null;
  E5_VALOR?: number | null;
  E5_VALOR_ASSINADO?: number | null;
  E5_SALDO_ACUMULADO?: number | null;
  E5_HIST?: string | null;
  E5_ORIGEM_TIPO?: string | null;
  E5_ORIGEM_ID?: number | null;
  E5_USUARIO?: string | null;
  E5_CATEG_ID?: number | null;
  CATEG_NOME?: string | null;
  CATEG_TIPO?: string | null;
  [k: string]: unknown;
};

export type CaixaSaldo = {
  entradas: number;
  saidas: number;
  saldo: number;
};

function qs(params: Record<string, unknown>) {
  const sp = new URLSearchParams();
  Object.entries(params).forEach(([k, v]) => {
    if (v === undefined || v === null || v === "") return;
    sp.set(k, String(v));
  });
  return sp.toString();
}

export async function listarContasCaixa(params: { filial?: string } = {}) {
  const query = qs(params);
  return http<CaixaConta[]>(`/financeiro/caixa/contas${query ? `?${query}` : ""}`);
}

export async function extratoCaixa(params: {
  filial?: string;
  conta_id: number;
  de?: string | null;
  ate?: string | null;
}) {
  const query = qs(params);
  return http<CaixaMovimento[]>(`/financeiro/caixa/extrato${query ? `?${query}` : ""}`);
}

export async function saldoCaixa(params: {
  filial?: string;
  conta_id: number;
  ate?: string | null;
}) {
  const query = qs(params);
  return http<CaixaSaldo>(`/financeiro/caixa/saldo${query ? `?${query}` : ""}`);
}
