import { useEffect, useMemo, useState } from "react";
import { useSearchParams } from "react-router-dom";
import { Toolbar } from "../components/Toolbar";
import { DataTable, type Column, type SortDir } from "../components/DataTable";
import { Pager } from "../components/Pager";
import { PageHero } from "../components/PageHero";
import { getFilial, onFilialChange } from "../state/filial";
import categoriesIcon from "../assets/shell-icons/categories.png";
import categoriesBg from "../assets/hero-backgrounds/categories.jpg";
import {
  listarCategorias,
  criarCategoria,
  definirCategoriaMov,
  obterMovimento,
  type Categoria,
  type MovimentoFinanceiro,
} from "../api/financeiro/categorias";

function toNumber(value: unknown, fallback = 0): number {
  const n = Number(value);
  return Number.isFinite(n) ? n : fallback;
}

function toStringValue(value: unknown, fallback = ""): string {
  if (value === null || value === undefined) return fallback;
  const s = String(value).trim();
  return s ? s : fallback;
}

export function FinanceiroCategorias() {
  const [searchParams, setSearchParams] = useSearchParams();
  const [filialView, setFilialView] = useState(getFilial());
  const [ativas, setAtivas] = useState(true);
  const [loading, setLoading] = useState(false);
  const [err, setErr] = useState<string | null>(null);
  const [okMsg, setOkMsg] = useState<string | null>(null);
  const [items, setItems] = useState<Categoria[]>([]);

  const [page, setPage] = useState(1);
  const [pageSize, setPageSize] = useState(10);

  const [nome, setNome] = useState("");
  const [tipo, setTipo] = useState("RECEITA");

  const [movId, setMovId] = useState("");
  const [categId, setCategId] = useState("");
  const [movimento, setMovimento] = useState<MovimentoFinanceiro | null>(null);

  const [sortKey, setSortKey] = useState("nome");
  const [sortDir, setSortDir] = useState<SortDir>("asc");

  function getErrorMessage(error: unknown, fallback: string): string {
    if (error instanceof Error && error.message) return error.message;
    return fallback;
  }

  async function load() {
    setErr(null);
    setLoading(true);
    try {
      const filial = getFilial();
      const data = await listarCategorias({ filial, ativas });
      setItems(data);
      setPage(1);
    } catch (error: unknown) {
      setErr(getErrorMessage(error, "Erro ao carregar categorias"));
    } finally {
      setLoading(false);
    }
  }

  async function saveCategoria() {
    setErr(null);
    setOkMsg(null);
    setLoading(true);
    try {
      if (!nome.trim()) throw new Error("Nome da categoria e obrigatorio.");
      const result = await criarCategoria({ filial: getFilial(), nome: nome.trim(), tipo });
      setNome("");
      if (result.id) {
        setOkMsg(`Categoria criada com sucesso. ID gerado: ${result.id}.`);
      } else {
        setOkMsg("Categoria criada com sucesso.");
      }
      await load();
    } catch (error: unknown) {
      setErr(getErrorMessage(error, "Erro ao criar categoria"));
    } finally {
      setLoading(false);
    }
  }

  async function aplicarCategoria() {
    setErr(null);
    setOkMsg(null);
    setLoading(true);
    try {
      const mid = toNumber(movId);
      if (!mid) throw new Error("Informe o ID do movimento.");
      const cid = categId ? toNumber(categId) : null;
      const result = await definirCategoriaMov({ mov_id: mid, categ_id: cid || null });
      const resultMovId = toNumber((result as Record<string, unknown>).mov_id, mid);
      const resultCategId = (result as Record<string, unknown>).categ_id;
      setOkMsg(
        resultCategId
          ? `Categoria aplicada com sucesso. Movimento ${resultMovId} vinculado a categoria ${resultCategId}.`
          : `Categoria removida com sucesso do movimento ${resultMovId}.`
      );
      setMovimento(await obterMovimento(resultMovId));
      setMovId("");
      setCategId("");
    } catch (error: unknown) {
      setErr(getErrorMessage(error, "Erro ao definir categoria"));
    } finally {
      setLoading(false);
    }
  }

  async function consultarMovimento() {
    setErr(null);
    setOkMsg(null);
    setLoading(true);
    try {
      const mid = toNumber(movId);
      if (!mid) throw new Error("Informe o ID do movimento.");
      setMovimento(await obterMovimento(mid));
      setOkMsg(`Movimento ${mid} consultado com sucesso.`);
    } catch (error: unknown) {
      setMovimento(null);
      setErr(getErrorMessage(error, "Erro ao consultar movimento"));
    } finally {
      setLoading(false);
    }
  }

  useEffect(() => {
    load();

    const unsub = onFilialChange((novaFilial) => {
      setFilialView(novaFilial);
      setErr(null);
      setAtivas(true);
      setPage(1);
      load();
    });
    return unsub;
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  useEffect(() => {
    const movIdParam = searchParams.get("mov_id") ?? "";
    if (!movIdParam) return;
    setMovId(movIdParam);
    setErr(null);
    setOkMsg(null);
    obterMovimento(Number(movIdParam))
      .then((mov) => {
        setMovimento(mov);
        setOkMsg(`Movimento ${movIdParam} carregado a partir da origem financeira.`);
      })
      .catch((error: unknown) => {
        setMovimento(null);
        setErr(getErrorMessage(error, "Erro ao consultar movimento"));
      });
  }, [searchParams]);

  const columns: Column<Categoria>[] = useMemo(
    () => [
      { key: "id", header: "ID", sortable: true, value: (x) => toNumber(x.ID) },
      {
        key: "nome",
        header: "Nome",
        sortable: true,
        value: (x) => toStringValue(x.C5_NOME ?? (x as Record<string, unknown>).nome, "-"),
      },
      {
        key: "tipo",
        header: "Tipo",
        sortable: true,
        value: (x) => toStringValue(x.C5_TIPO ?? (x as Record<string, unknown>).tipo, "-"),
      },
      {
        key: "ativa",
        header: "Ativa",
        sortable: true,
        className: "hide-sm",
        value: (x) => String(x.C5_ATIVA ?? (x as Record<string, unknown>).ativa ?? 0),
      },
    ],
    []
  );

  return (
    <>
      <PageHero
        icon={categoriesIcon}
        backgroundImage={categoriesBg}
        backgroundPosition="center 40%"
        eyebrow="Financeiro"
        title="Categorias financeiras"
        description="Estruture receitas, despesas, custos e transferencias para enriquecer caixa, AR, AP e demonstrativos."
        metrics={[
          { label: "Filial", value: filialView },
          { label: "Categorias", value: String(items.length) },
          { label: "Filtro", value: ativas ? "Ativas" : "Todas" },
        ]}
      />

      <div className="card">
      <Toolbar
        left={
          <div className="hint">
            Filial: <b>{filialView}</b>
          </div>
        }
        right={
          <>
            <select
              className="select"
              value={ativas ? "true" : "false"}
              onChange={(e) => { setAtivas(e.target.value === "true"); setPage(1); }}
            >
              <option value="true">Ativas</option>
              <option value="false">Todas</option>
            </select>
            <button type="button" className="btn" onClick={load} disabled={loading}>
              Aplicar
            </button>
            <button
              type="button"
              className="btn ghost"
              onClick={() => {
                setAtivas(true);
                setNome("");
                setTipo("RECEITA");
                setPage(1);
              }}
              disabled={loading}
            >
              Limpar
            </button>
            <button
              type="button"
              className="btn ghost"
              onClick={() => {
                setMovimento(null);
                setMovId("");
                const next = new URLSearchParams(searchParams);
                next.delete("mov_id");
                setSearchParams(next);
              }}
              disabled={loading || !movimento}
            >
              Limpar consulta
            </button>
          </>
        }
      />

      {okMsg && <div className="alert alert-success mt-12">{okMsg}</div>}
      {err && <div className="alert mt-12">{err}</div>}

      <div className="section-title">Resumo</div>
      <div className="stats-grid">
        <div className="stat-card">
          <div>
            <div className="kpi-label">Categorias</div>
            <div className="kpi">{items.length}</div>
          </div>
          <div className="stat-icon">CT</div>
        </div>
        <div className="stat-card">
          <div>
            <div className="kpi-label">Filtro</div>
            <div className="kpi">{ativas ? "Ativas" : "Todas"}</div>
          </div>
          <div className="stat-icon solid">FL</div>
        </div>
        <div className="stat-card">
          <div>
            <div className="kpi-label">Filial</div>
            <div className="kpi">{filialView}</div>
          </div>
          <div className="stat-icon success">F</div>
        </div>
      </div>

      <div className="form-grid mt-12">
        <div className="form-field">
          <label>Nome</label>
          <input value={nome} onChange={(e) => setNome(e.target.value)} placeholder="Categoria" />
        </div>
        <div className="form-field">
          <label>Tipo</label>
          <select className="select" value={tipo} onChange={(e) => setTipo(e.target.value)}>
            <option value="RECEITA">RECEITA</option>
            <option value="DESPESA">DESPESA</option>
            <option value="CUSTO">CUSTO</option>
            <option value="TRANSFERENCIA">TRANSFERENCIA</option>
            <option value="OUTROS">OUTROS</option>
          </select>
        </div>
        <div className="form-field">
          <label>&nbsp;</label>
          <button type="button" className="btn primary" onClick={saveCategoria} disabled={loading}>
            Criar categoria
          </button>
        </div>
      </div>

      <div className="form-grid mt-12">
        <div className="form-field">
          <label>ID do movimento</label>
          <input value={movId} onChange={(e) => setMovId(e.target.value)} placeholder="Ex: 123" />
        </div>
        <div className="form-field">
          <label>ID da categoria (opcional)</label>
          <input
            value={categId}
            onChange={(e) => setCategId(e.target.value)}
            placeholder="Ex: 5"
          />
        </div>
        <div className="form-field">
          <label>&nbsp;</label>
          <div className="row gap-10">
            <button type="button" className="btn" onClick={aplicarCategoria} disabled={loading}>
              Definir categoria
            </button>
            <button type="button" className="btn ghost" onClick={consultarMovimento} disabled={loading}>
              Consultar movimento
            </button>
          </div>
        </div>
      </div>

      {movimento && (
        <>
          <div className="section-title mt-12">Movimento consultado</div>
          <div className="stats-grid">
            <div className="stat-card">
              <div>
                <div className="kpi-label">Movimento</div>
                <div className="kpi">{toNumber(movimento.ID)}</div>
              </div>
              <div className="stat-icon">MV</div>
            </div>
            <div className="stat-card">
              <div>
                <div className="kpi-label">Categoria atual</div>
                <div className="kpi">
                  {toNumber(movimento.E5_CATEG_ID) > 0
                    ? `${toNumber(movimento.E5_CATEG_ID)} - ${toStringValue(movimento.CATEG_NOME, "-")}`
                    : "Sem categoria"}
                </div>
              </div>
              <div className="stat-icon solid">CT</div>
            </div>
            <div className="stat-card">
              <div>
                <div className="kpi-label">Valor</div>
                <div className="kpi">
                  {toNumber(movimento.E5_VALOR).toLocaleString("pt-BR", {
                    style: "currency",
                    currency: "BRL",
                  })}
                </div>
              </div>
              <div className="stat-icon success">{toStringValue(movimento.E5_TIPO, "-")}</div>
            </div>
          </div>

          <div className="card mt-12">
            <div className="detail-grid">
              <div>
                <div className="kpi-label">Filial</div>
                <div>{toStringValue(movimento.E5_FILIAL, "-")}</div>
              </div>
              <div>
                <div className="kpi-label">Data</div>
                <div>{toStringValue(movimento.E5_DATA, "-")}</div>
              </div>
              <div>
                <div className="kpi-label">Origem</div>
                <div>
                  {toStringValue(movimento.E5_ORIGEM_TIPO, "-")} #{toStringValue(movimento.E5_ORIGEM_ID, "-")}
                </div>
              </div>
              <div>
                <div className="kpi-label">Usuario</div>
                <div>{toStringValue(movimento.E5_USUARIO, "-")}</div>
              </div>
              <div style={{ gridColumn: "1 / -1" }}>
                <div className="kpi-label">Historico</div>
                <div>{toStringValue(movimento.E5_HIST, "-")}</div>
              </div>
              <div>
                <div className="kpi-label">Tipo da categoria</div>
                <div>{toStringValue(movimento.CATEG_TIPO, "-")}</div>
              </div>
            </div>
          </div>
        </>
      )}

      <div className="row-between mt-12">
        <Pager
          page={page}
          totalPages={Math.max(1, Math.ceil(items.length / pageSize))}
          pageSize={pageSize}
          totalItems={items.length}
          onPageChange={setPage}
          onPageSizeChange={(ps) => {
            setPageSize(ps);
            setPage(1);
          }}
          showPageSize
        />
      </div>

      <DataTable
        rows={items.slice((page - 1) * pageSize, (page - 1) * pageSize + pageSize)}
        columns={columns}
        sortKey={sortKey}
        sortDir={sortDir}
        className="compact"
        wrapperClassName="table-scroller"
        onSortChange={(k, d) => {
          setSortKey(k);
          setSortDir(d);
          setPage(1);
        }}
        loading={loading}
        emptyText="Nenhuma categoria encontrada."
      />
      </div>
    </>
  );
}
