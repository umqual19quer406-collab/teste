import { http } from "./http";

export type LogItem = {
  ID: number;
  L_USUARIO?: string | null;
  L_ACAO?: string | null;
  L_DATA?: string | null;
  [k: string]: unknown;
};

export async function listarAuditoria() {
  return http<LogItem[]>("/auditoria");
}
