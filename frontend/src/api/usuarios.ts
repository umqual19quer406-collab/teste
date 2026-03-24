import { http } from "./http";

export type BootstrapInput = {
  login: string;
  senha: string;
};

export type UsuarioCreateInput = {
  login: string;
  senha: string;
  perfil: string;
};

export async function bootstrapAdmin(payload: BootstrapInput) {
  return http<{ status: string; login: string }>("/bootstrap", { method: "POST", body: payload });
}

export async function criarUsuario(payload: UsuarioCreateInput) {
  return http<{ status: string; login: string }>("/usuarios", { method: "POST", body: payload });
}
