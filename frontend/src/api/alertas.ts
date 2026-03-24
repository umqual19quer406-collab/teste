import { http } from "./http";

export type BackendAlertItem = {
  code: string;
  severity: "critical" | "warning" | "info" | string;
  title: string;
  text: string;
  route?: string | null;
  count?: number | null;
  action_label?: string | null;
  business_context?: string | null;
};

export type BackendAlertSummary = {
  critical: number;
  warning: number;
  info: number;
  total: number;
};

export type BackendAlertsResponse = {
  filial: string;
  usuario: string;
  generated_at: string;
  summary: BackendAlertSummary;
  items: BackendAlertItem[];
};

export function listarAlertas(params: { filial: string }) {
  const query = new URLSearchParams({ filial: params.filial }).toString();
  return http<BackendAlertsResponse>(`/alertas?${query}`);
}
