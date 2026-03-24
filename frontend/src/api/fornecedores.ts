import { http } from "./http";

export type Fornecedor = {
  cod: string;
  nome: string;
  doc?: string | null;
  email?: string | null;
  fone?: string | null;
  filial?: string;
  ativo_sn?: "S" | "N";
};

type RawRecord = Record<string, unknown>;

function asRecord(value: unknown): RawRecord {
  return value && typeof value === "object" ? (value as RawRecord) : {};
}

function asString(value: unknown): string | undefined {
  return typeof value === "string" ? value : undefined;
}

function normalizeFornecedor(value: unknown): Fornecedor {
  const r = asRecord(value);
  const ativo = asString(r.ativo_sn) ?? asString(r.A2_ATIVO_SN) ?? asString(r.a2_ativo_sn) ?? "S";

  return {
    cod: asString(r.cod) ?? asString(r.A2_COD) ?? asString(r.a2_cod) ?? "",
    nome: asString(r.nome) ?? asString(r.A2_NOME) ?? asString(r.a2_nome) ?? "",
    doc: asString(r.doc) ?? asString(r.A2_DOC) ?? asString(r.a2_doc) ?? null,
    email: asString(r.email) ?? asString(r.A2_EMAIL) ?? asString(r.a2_email) ?? null,
    fone: asString(r.fone) ?? asString(r.A2_FONE) ?? asString(r.a2_fone) ?? null,
    filial: asString(r.filial) ?? asString(r.A2_FILIAL) ?? asString(r.a2_filial),
    ativo_sn: ativo === "N" ? "N" : "S",
  };
}

export async function listFornecedores(params: { ativos: boolean; filial: string }) {
  const qs = new URLSearchParams({
    ativos: String(params.ativos),
    filial: params.filial,
  });

  const data = await http<unknown[]>(`/fornecedores?${qs.toString()}`);
  return data.map(normalizeFornecedor);
}

export async function buscarFornecedores(params: { q: string; filial: string }) {
  const qs = new URLSearchParams({ q: params.q, filial: params.filial });

  const data = await http<unknown[]>(`/fornecedores/buscar?${qs.toString()}`);
  return data.map(normalizeFornecedor);
}

export async function createFornecedor(payload: {
  filial: string;
  cod: string;
  nome: string;
  doc?: string | null;
  email?: string | null;
  fone?: string | null;
}) {
  const created = await http<unknown>("/fornecedores", { method: "POST", body: payload });
  return normalizeFornecedor(created);
}

export async function updateFornecedor(
  cod: string,
  payload: { filial: string; nome?: string; doc?: string | null; email?: string | null; fone?: string | null }
) {
  const updated = await http<unknown>(`/fornecedores/${encodeURIComponent(cod)}`, {
    method: "PUT",
    body: payload,
  });
  return normalizeFornecedor(updated);
}

export async function setFornecedorAtivo(cod: string, payload: { ativo: boolean; filial: string }) {
  return http<{ ok: true }>(`/fornecedores/${encodeURIComponent(cod)}/ativo`, {
    method: "POST",
    body: payload,
  });
}
