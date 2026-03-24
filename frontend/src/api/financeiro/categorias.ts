import { http } from "../http";

export type Categoria = {
  ID: number;
  C5_FILIAL?: string | null;
  C5_NOME?: string | null;
  C5_TIPO?: string | null;
  C5_ATIVA?: number | boolean | null;
  [k: string]: unknown;
};

export type CategoriaCreateInput = {
  nome: string;
  tipo: string;
};

export type MovSetCategoriaInput = {
  mov_id: number;
  categ_id?: number | null;
};

export type MovimentoFinanceiro = {
  ID: number;
  E5_FILIAL?: string | null;
  E5_DATA?: string | null;
  E5_TIPO?: string | null;
  E5_VALOR?: number | null;
  E5_HIST?: string | null;
  E5_ORIGEM_TIPO?: string | null;
  E5_ORIGEM_ID?: number | null;
  E5_USUARIO?: string | null;
  E5_CATEG_ID?: number | null;
  CATEG_NOME?: string | null;
  CATEG_TIPO?: string | null;
  [k: string]: unknown;
};

function qs(params: Record<string, unknown>) {
  const sp = new URLSearchParams();
  Object.entries(params).forEach(([k, v]) => {
    if (v === undefined || v === null || v === "") return;
    sp.set(k, String(v));
  });
  return sp.toString();
}

export async function listarCategorias(params: { filial?: string; ativas?: boolean } = {}) {
  const query = qs(params);
  return http<Categoria[]>(`/financeiro/categorias${query ? `?${query}` : ""}`);
}

export async function criarCategoria(payload: CategoriaCreateInput & { filial?: string }) {
  const { filial, ...rest } = payload;
  const query = qs({ filial });
  return http<{ id?: number }>(`/financeiro/categorias${query ? `?${query}` : ""}`, {
    method: "POST",
    body: rest,
  });
}

export async function definirCategoriaMov(payload: MovSetCategoriaInput) {
  return http<Record<string, unknown>>("/financeiro/movimentos/categoria", {
    method: "POST",
    body: payload,
  });
}

export async function obterMovimento(movId: number) {
  return http<MovimentoFinanceiro>(`/financeiro/movimentos/${movId}`);
}
