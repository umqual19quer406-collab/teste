import { http } from "./http";

export type ProdutoInput = {
  cod: string;
  desc: string;
  preco: number;
  filial?: string;
};

export type ProdutoResumo = {
  cod: string;
  desc: string;
  preco: number;
  estoque: number;
  reservado: number;
  cm: number;
  filial?: string;
  ncm?: string | null;
};

type RawRecord = Record<string, unknown>;

function asRecord(value: unknown): RawRecord {
  return value && typeof value === "object" ? (value as RawRecord) : {};
}

function asString(value: unknown): string {
  return typeof value === "string" ? value : "";
}

function asNumber(value: unknown): number {
  const n = Number(value);
  return Number.isFinite(n) ? n : 0;
}

function normalizeProduto(value: unknown): ProdutoResumo {
  const r = asRecord(value);
  return {
    cod: asString(r.cod) || asString(r.B1_COD),
    desc: asString(r.desc) || asString(r.B1_DESC),
    preco: asNumber(r.preco ?? r.B1_PRECO),
    estoque: asNumber(r.estoque ?? r.B1_ESTOQUE),
    reservado: asNumber(r.reservado ?? r.B1_RESERVADO),
    cm: asNumber(r.cm ?? r.B1_CM),
    filial: asString(r.filial) || asString(r.B1_FILIAL),
    ncm: asString(r.ncm) || asString(r.B1_NCM) || null,
  };
}

export async function upsertProduto(payload: ProdutoInput) {
  return http<Record<string, unknown>>("/produto", { method: "POST", body: payload });
}

export async function buscarProdutos(params: { q: string; filial: string; limite?: number }) {
  const qs = new URLSearchParams({
    q: params.q,
    filial: params.filial,
    limite: String(params.limite ?? 10),
  });
  const data = await http<unknown[]>(`/produtos/buscar?${qs.toString()}`);
  return data.map(normalizeProduto);
}
