import { API_BASE_URL } from "../config/env";

type HttpMethod = "GET" | "POST" | "PUT" | "PATCH" | "DELETE";
type JsonObject = Record<string, unknown>;
type HttpOptions = { method?: HttpMethod; body?: unknown; headers?: Record<string, string> };

function forceLogout() {
  localStorage.removeItem("token");
  if (window.location.pathname !== "/login") {
    window.location.assign("/login");
  }
}

function normalizeFastApiError(data: unknown, fallback: string) {
  const obj = data && typeof data === "object" ? (data as JsonObject) : null;
  const detailOrMessage = obj?.detail ?? obj?.message;

  if (typeof detailOrMessage === "string" && detailOrMessage.trim()) return detailOrMessage;

  if (Array.isArray(detailOrMessage) && detailOrMessage.length > 0) {
    const first = detailOrMessage[0];
    if (typeof first === "string") return first;
    if (first && typeof first === "object" && "msg" in first) {
      const msg = (first as JsonObject).msg;
      if (typeof msg === "string") return msg;
    }
    return JSON.stringify(detailOrMessage);
  }

  if (typeof obj?.error === "string" && obj.error.trim()) return obj.error;
  return fallback;
}

async function safeReadBody(res: Response): Promise<{ text: string; data: unknown | null }> {
  const text = await res.text();
  if (!text) return { text: "", data: null };

  try {
    return { text, data: JSON.parse(text) };
  } catch {
    return { text, data: null };
  }
}

export async function http<T>(path: string, opts: HttpOptions = {}): Promise<T> {
  const method = opts.method ?? "GET";
  const headers: Record<string, string> = { ...(opts.headers ?? {}) };

  const token = localStorage.getItem("token");
  if (token) headers.Authorization = `Bearer ${token}`;

  const hasBody = opts.body !== undefined && opts.body !== null;
  if (hasBody) headers["Content-Type"] = headers["Content-Type"] ?? "application/json";

  let res: Response;
  try {
    res = await fetch(`${API_BASE_URL}${path}`, {
      method,
      headers,
      body: hasBody ? JSON.stringify(opts.body) : undefined,
    });
  } catch {
    throw new Error("Falha de conexao com o servidor (backend). Verifique se o uvicorn esta rodando.");
  }

  if (res.status === 401) {
    forceLogout();
    throw new Error("Sessao expirada. Faca login novamente.");
  }

  const { text, data } = await safeReadBody(res);

  if (res.ok && (!text || res.status === 204)) {
    return null as T;
  }

  if (!res.ok) {
    const msg = normalizeFastApiError(data ?? { message: text }, `HTTP ${res.status}`);
    throw new Error(msg);
  }

  if (data !== null) return data as T;
  return text as unknown as T;
}
