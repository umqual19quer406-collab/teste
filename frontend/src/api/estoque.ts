import { http } from "./http";

export type EstoqueSnapshot = {
  B1_COD: string;
  B1_DESC: string;
  B1_PRECO: number;
  B1_ESTOQUE: number;
  B1_RESERVADO: number;
  B1_CM: number;
  B1_FILIAL: string;
  B1_NCM?: string | null;
  DISPONIVEL?: number;
  saldo_sd3?: number;
};

export type EntradaEstoqueInput = {
  cod: string;
  qtd: number;
  filial?: string;
  custo_unit: number;
  forn?: string | null;
  venc_dias?: number;
};

export type Sd3Movimento = {
  ID: number;
  D3_DATA: string;
  D3_TIPO: string;
  D3_QTD: number;
  D3_CUSTO_UNIT: number;
  D3_VALOR: number;
  D3_ORIGEM: string;
  D3_REF?: string | null;
  D3_USUARIO?: string | null;
};

export async function consultarEstoque(params: { cod: string; filial: string }) {
  const qs = new URLSearchParams({ filial: params.filial });
  return http<EstoqueSnapshot>(`/estoque/${encodeURIComponent(params.cod)}?${qs.toString()}`);
}

export async function entradaEstoque(payload: EntradaEstoqueInput) {
  return http<EstoqueSnapshot>("/estoque/entrada", {
    method: "POST",
    body: payload,
  });
}

export async function extratoEstoque(params: { cod: string; filial: string; limite?: number }) {
  const qs = new URLSearchParams({
    filial: params.filial,
    limite: String(params.limite ?? 20),
  });
  return http<Sd3Movimento[]>(`/estoque/extrato/${encodeURIComponent(params.cod)}?${qs.toString()}`);
}
