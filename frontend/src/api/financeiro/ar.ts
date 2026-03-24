import { http } from "../http";

export type ArTitulo = {
  ID: number;
  E1_CLIENTE?: string | null;
  E1_CLIENTE_COD?: string | null;
  E1_VALOR?: number | null;
  E1_STATUS?: string | null;
  E1_VENC?: string | null;
  E1_DATA?: string | null;
  E1_REF?: string | null;
  E1_FILIAL?: string | null;
  E1_SE5_ID?: number | null;
  [k: string]: unknown;
};

export type LiquidarInput = {
  titulo_id: number;
  conta_id: number;
};

function qs(params: Record<string, unknown>) {
  const sp = new URLSearchParams();
  Object.entries(params).forEach(([k, v]) => {
    if (v === undefined || v === null || v === "") return;
    sp.set(k, String(v));
  });
  return sp.toString();
}

export async function listarAR(params: { filial?: string; status?: string } = {}) {
  const query = qs(params);
  return http<ArTitulo[]>(`/financeiro/ar${query ? `?${query}` : ""}`);
}

export async function baixarAR(payload: LiquidarInput) {
  return http<{ mov_id?: number; se5_id?: number }>("/financeiro/ar/baixar", { method: "POST", body: payload });
}

export async function receberAR(payload: LiquidarInput) {
  return http<{ mov_id?: number; se5_id?: number }>("/financeiro/ar/receber", { method: "POST", body: payload });
}
