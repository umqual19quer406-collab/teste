import { http } from "./http";
import { getFilial } from "../state/filial";

export type Cliente = {
  id?: number;
  cod: string;
  nome: string;
  doc?: string | null;
  email?: string | null;
  fone?: string | null;
  filial: string;
  ativo_sn: "S" | "N";
  criado_em?: string;
};

export type ClienteCreateInput = {
  cod: string;
  nome: string;
  doc?: string | null;
  email?: string | null;
  fone?: string | null;
  filial?: string;
};

export type ClienteUpdateInput = {
  nome?: string | null;
  doc?: string | null;
  email?: string | null;
  fone?: string | null;
  filial?: string;
};

type RawRecord = Record<string, unknown>;

function asRecord(value: unknown): RawRecord {
  return value && typeof value === "object" ? (value as RawRecord) : {};
}

function asString(value: unknown): string | undefined {
  return typeof value === "string" ? value : undefined;
}

function asNumber(value: unknown): number | undefined {
  return typeof value === "number" ? value : undefined;
}

function normalizeCliente(value: unknown): Cliente {
  const x = asRecord(value);
  const ativoRaw = x.A1_ATIVO ?? x.ativo ?? false;

  return {
    id: asNumber(x.ID),
    filial: asString(x.A1_FILIAL) ?? asString(x.filial) ?? getFilial(),
    cod: asString(x.A1_COD) ?? asString(x.cod) ?? "",
    nome: asString(x.A1_NOME) ?? asString(x.nome) ?? "",
    doc: asString(x.A1_DOC) ?? asString(x.doc) ?? null,
    email: asString(x.A1_EMAIL) ?? asString(x.email) ?? null,
    fone: asString(x.A1_FONE) ?? asString(x.A1_TEL) ?? asString(x.fone) ?? null,
    ativo_sn: ativoRaw ? "S" : "N",
    criado_em: asString(x.A1_CRIADO_EM) ?? asString(x.criado_em),
  };
}

export async function listClientes(params: { ativos: boolean; filial?: string }) {
  const filial = params.filial ?? getFilial();
  const qs = new URLSearchParams({
    ativos: params.ativos ? "true" : "false",
    filial,
  });

  const data = await http<unknown[]>(`/clientes?${qs.toString()}`);
  return data.map(normalizeCliente);
}

export async function buscarClientes(params: { q: string; filial?: string }) {
  const filial = params.filial ?? getFilial();
  const qs = new URLSearchParams({ q: params.q, filial });

  const data = await http<unknown[]>(`/clientes/buscar?${qs.toString()}`);
  return data.map(normalizeCliente);
}

export async function createCliente(payload: ClienteCreateInput) {
  const body = { ...payload, filial: payload.filial ?? getFilial() };
  return http(`/clientes`, { method: "POST", body });
}

export async function updateCliente(cod: string, payload: ClienteUpdateInput) {
  const body = { ...payload, filial: payload.filial ?? getFilial() };
  return http(`/clientes/${encodeURIComponent(cod)}`, { method: "PUT", body });
}

export async function setClienteAtivo(cod: string, payload: { ativo: boolean; filial?: string }) {
  const body = { ativo: payload.ativo, filial: payload.filial ?? getFilial() };
  return http(`/clientes/${encodeURIComponent(cod)}/ativo`, { method: "POST", body });
}
