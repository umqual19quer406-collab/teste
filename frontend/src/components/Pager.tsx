type Props = {
  page: number;
  totalPages: number;
  pageSize: number;
  totalItems: number;

  onPageChange: (page: number) => void;
  onPageSizeChange: (pageSize: number) => void;

  showPageSize?: boolean; // topo: true, rodapé: false
};

export function Pager({
  page,
  totalPages,
  pageSize,
  totalItems,
  onPageChange,
  onPageSizeChange,
  showPageSize = false,
}: Props) {
  const safePage = Math.min(Math.max(1, page), Math.max(1, totalPages));

  return (
    <div className="row-between mt-12">
      <div className="hint">
        Página <b>{safePage}</b> de <b>{Math.max(1, totalPages)}</b>
        {showPageSize ? (
          <>
            {" "}
            — {totalItems} registros
          </>
        ) : null}
      </div>

      <div className="row gap-10">
        {showPageSize && (
          <select
            className="select"
            value={pageSize}
            onChange={(e) => onPageSizeChange(Number(e.target.value))}
            aria-label="Itens por página"
          >
            <option value={10}>10</option>
            <option value={20}>20</option>
            <option value={50}>50</option>
          </select>
        )}

        <button
          className="btn"
          disabled={safePage <= 1}
          onClick={() => onPageChange(Math.max(1, safePage - 1))}
        >
          Anterior
        </button>

        <button
          className="btn"
          disabled={safePage >= totalPages}
          onClick={() => onPageChange(Math.min(totalPages, safePage + 1))}
        >
          Próxima
        </button>
      </div>
    </div>
  );
}