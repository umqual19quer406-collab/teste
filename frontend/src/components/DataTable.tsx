import { isValidElement, useMemo, type ReactNode } from "react";

export type SortDir = "asc" | "desc";

export type Column<Row extends Record<string, unknown>> = {
  key: string;
  header: string | ReactNode;
  sortable?: boolean;
  width?: number | string;
  align?: "left" | "center" | "right";
  className?: string;
  value?: (row: Row) => unknown;
  render?: (row: Row) => ReactNode;
};

type Props<Row extends Record<string, unknown>> = {
  rows: Row[];
  columns: Column<Row>[];
  sortKey: string;
  sortDir: SortDir;
  onSortChange: (key: string, dir: SortDir) => void;
  emptyText?: string;
  loading?: boolean;
  className?: string;
  wrapperClassName?: string;
};

function normalize(v: unknown) {
  if (v === null || v === undefined) return "";
  if (typeof v === "boolean") return v ? "1" : "0";
  if (typeof v === "number") return String(v).padStart(20, "0");
  return String(v).toLowerCase().trim();
}

function toReactNode(value: unknown): ReactNode {
  if (value === null || value === undefined) return "";
  if (typeof value === "string" || typeof value === "number") return value;
  if (typeof value === "boolean") return value ? "true" : "false";
  if (isValidElement(value)) return value;
  return String(value);
}

export function DataTable<Row extends Record<string, unknown>>({
  rows,
  columns,
  sortKey,
  sortDir,
  onSortChange,
  emptyText = "Nenhum registro encontrado.",
  loading = false,
  className,
  wrapperClassName,
}: Props<Row>) {
  const sortedRows = useMemo(() => {
    const col = columns.find((c) => c.key === sortKey);
    const valueFn = col?.value ?? ((r: Row) => r[sortKey]);

    const copy = [...rows];
    copy.sort((a, b) => {
      const va = normalize(valueFn(a));
      const vb = normalize(valueFn(b));
      if (va < vb) return sortDir === "asc" ? -1 : 1;
      if (va > vb) return sortDir === "asc" ? 1 : -1;
      return 0;
    });
    return copy;
  }, [rows, columns, sortKey, sortDir]);

  function toggleSort(key: string) {
    if (sortKey === key) {
      onSortChange(key, sortDir === "asc" ? "desc" : "asc");
    } else {
      onSortChange(key, "asc");
    }
  }

  function indicator(key: string) {
    if (sortKey !== key) return "";
    return sortDir === "asc" ? " ▲" : " ▼";
  }

  const table = (
    <table className={`table mt-12 ${className ?? ""}`.trim()}>
      <thead>
        <tr>
          {columns.map((c) => {
            const clickable = !!c.sortable;
            return (
              <th
                key={c.key}
                onClick={clickable ? () => toggleSort(c.key) : undefined}
                style={{
                  cursor: clickable ? "pointer" : undefined,
                  width: c.width,
                  textAlign: c.align ?? "left",
                }}
                className={c.className}
                aria-sort={
                  sortKey === c.key ? (sortDir === "asc" ? "ascending" : "descending") : "none"
                }
              >
                {c.header}
                {clickable ? indicator(c.key) : ""}
              </th>
            );
          })}
        </tr>
      </thead>

      <tbody>
        {sortedRows.length === 0 ? (
          <tr>
            <td colSpan={columns.length} className="p-14">
              {loading ? "Carregando..." : emptyText}
            </td>
          </tr>
        ) : (
          sortedRows.map((row, idx) => (
            <tr key={idx}>
              {columns.map((c) => {
                const raw = c.render?.(row) ?? (c.value ? c.value(row) : row[c.key] ?? "");
                const content = toReactNode(raw);
                return (
                  <td key={c.key} style={{ textAlign: c.align ?? "left" }} className={c.className}>
                    {content}
                  </td>
                );
              })}
            </tr>
          ))
        )}
      </tbody>
    </table>
  );

  if (wrapperClassName) {
    return <div className={wrapperClassName}>{table}</div>;
  }

  return table;
}
