import { http } from "../http";

export type ApTitulo = {
  ID: number;
  F1_FORN?: string | null;
  F1_FORN_COD?: string | null;
  F1_VALOR?: number | null;
  F1_STATUS?: string | null;
  F1_VENC?: string | null;
  F1_DATA?: string | null;
  F1_REF?: string | null;
  F1_FILIAL?: string | null;
  F1_SE5_ID?: number | null;
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

export async function listarAP(params: { filial?: string; status?: string } = {}) {
  const query = qs(params);
  return http<ApTitulo[]>(`/financeiro/ap${query ? `?${query}` : ""}`);
}

export async function baixarAP(payload: LiquidarInput) {
  return http<{ mov_id?: number; se5_id?: number }>("/financeiro/ap/baixar", { method: "POST", body: payload });
}

export async function pagarAP(payload: LiquidarInput) {
  return http<{ mov_id?: number; se5_id?: number }>("/financeiro/ap/pagar", { method: "POST", body: payload });
}
