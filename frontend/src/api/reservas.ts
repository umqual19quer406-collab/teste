import { http } from "./http";

export type ReservaInput = {
  cod: string;
  qtd: number;
  filial?: string;
  cliente_cod?: string | null;
  tabela_cod?: string;
};

export type CancelarInput = {
  reserva_id: number;
};

export type ConfirmarInput = {
  reserva_id: number;
  cliente_cod?: string | null;
  venc_dias?: number;
};

export async function criarReserva(payload: ReservaInput) {
  return http<Record<string, unknown>>("/reserva", { method: "POST", body: payload });
}

export async function cancelarReserva(payload: CancelarInput) {
  return http<Record<string, unknown>>("/reserva/cancelar", { method: "POST", body: payload });
}

export async function confirmarReserva(payload: ConfirmarInput) {
  return http<Record<string, unknown>>("/reserva/confirmar", { method: "POST", body: payload });
}
