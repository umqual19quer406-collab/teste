import { API_BASE_URL } from "../config/env";

export type LoginResponse = {
  access_token: string;
  token_type: string;
};

function isLoginResponse(data: unknown): data is LoginResponse {
  if (!data || typeof data !== "object") return false;
  const value = data as Record<string, unknown>;
  return typeof value.access_token === "string" && typeof value.token_type === "string";
}

export async function login(username: string, password: string): Promise<LoginResponse> {
  const form = new URLSearchParams();
  form.set("username", username);
  form.set("password", password);

  let res: Response;
  try {
    res = await fetch(`${API_BASE_URL}/login`, {
      method: "POST",
      headers: { "Content-Type": "application/x-www-form-urlencoded" },
      body: form.toString(),
    });
  } catch {
    throw new Error("Nao foi possivel conectar ao servidor.");
  }

  const text = await res.text();
  let data: unknown = null;

  try {
    data = text ? JSON.parse(text) : null;
  } catch {
    data = null;
  }

  if (!res.ok) {
    const detail =
      data && typeof data === "object" && typeof (data as Record<string, unknown>).detail === "string"
        ? ((data as Record<string, unknown>).detail as string)
        : "Usuario ou senha invalidos.";
    throw new Error(detail);
  }

  if (!isLoginResponse(data)) {
    throw new Error("Resposta de login invalida.");
  }

  return data;
}
