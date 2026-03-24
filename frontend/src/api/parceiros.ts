import { http } from "./http";

type ClienteInput = {
  cod: string;
  nome: string;
  doc?: string | null;
  email?: string | null;
  tel?: string | null;
  end?: string | null;
  mun?: string | null;
  uf?: string | null;
  cep?: string | null;
  tabela_id?: number | null;
};

type FornecedorInput = {
  cod: string;
  nome: string;
  doc?: string | null;
  email?: string | null;
  tel?: string | null;
  end?: string | null;
  mun?: string | null;
  uf?: string | null;
  cep?: string | null;
};

function qs(params: Record<string, unknown>) {
  const sp = new URLSearchParams();
  Object.entries(params).forEach(([k, v]) => {
    if (v === undefined || v === null || v === "") return;
    sp.set(k, String(v));
  });
  return sp.toString();
}

export async function listarSa1Clientes(params: { filial?: string; ativo?: boolean; q?: string } = {}) {
  const query = qs(params);
  return http<Record<string, unknown>[]>(`/parceiros/sa1/clientes${query ? `?${query}` : ""}`);
}

export async function obterSa1Cliente(cod: string, params: { filial?: string } = {}) {
  const query = qs(params);
  return http<Record<string, unknown>>(
    `/parceiros/sa1/clientes/${encodeURIComponent(cod)}${query ? `?${query}` : ""}`
  );
}

export async function criarSa1Cliente(payload: ClienteInput & { filial?: string }) {
  const { filial, ...body } = payload;
  const query = qs({ filial });
  return http<Record<string, unknown>>(
    `/parceiros/sa1/clientes${query ? `?${query}` : ""}`,
    { method: "POST", body }
  );
}

export async function inativarSa1Cliente(cod: string, params: { filial?: string } = {}) {
  const query = qs(params);
  return http<Record<string, unknown>>(
    `/parceiros/sa1/clientes/${encodeURIComponent(cod)}${query ? `?${query}` : ""}`,
    { method: "DELETE" }
  );
}

export async function setTabelaSa1Cliente(payload: { cod: string; tabela_id?: number | null; filial?: string }) {
  const { filial, ...body } = payload;
  const query = qs({ filial });
  return http<Record<string, unknown>>(
    `/parceiros/sa1/clientes/set-tabela${query ? `?${query}` : ""}`,
    { method: "POST", body }
  );
}

export async function listarSa2Fornecedores(params: { filial?: string; ativo?: boolean; q?: string } = {}) {
  const query = qs(params);
  return http<Record<string, unknown>[]>(`/parceiros/sa2/fornecedores${query ? `?${query}` : ""}`);
}

export async function obterSa2Fornecedor(cod: string, params: { filial?: string } = {}) {
  const query = qs(params);
  return http<Record<string, unknown>>(
    `/parceiros/sa2/fornecedores/${encodeURIComponent(cod)}${query ? `?${query}` : ""}`
  );
}

export async function criarSa2Fornecedor(payload: FornecedorInput & { filial?: string }) {
  const { filial, ...body } = payload;
  const query = qs({ filial });
  return http<Record<string, unknown>>(
    `/parceiros/sa2/fornecedores${query ? `?${query}` : ""}`,
    { method: "POST", body }
  );
}

export async function inativarSa2Fornecedor(cod: string, params: { filial?: string } = {}) {
  const query = qs(params);
  return http<Record<string, unknown>>(
    `/parceiros/sa2/fornecedores/${encodeURIComponent(cod)}${query ? `?${query}` : ""}`,
    { method: "DELETE" }
  );
}
