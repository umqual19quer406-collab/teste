from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Iterable


ROOT = Path(__file__).resolve().parent
OUTPUT = ROOT / "mini_protheus_codigo_fonte.pdf"

INCLUDE_EXTENSIONS = {
    ".py",
    ".sql",
    ".ts",
    ".tsx",
    ".js",
    ".jsx",
    ".css",
    ".html",
    ".json",
    ".md",
    ".txt",
    ".yml",
    ".yaml",
}

INCLUDE_FILENAMES = {
    ".env.example",
    ".gitignore",
}

EXCLUDED_DIRS = {
    ".git",
    ".pytest_cache",
    ".vscode",
    "__pycache__",
    "node_modules",
    "dist",
    "build",
}

EXCLUDED_SUFFIXES = {
    ".pyc",
    ".ico",
    ".svg",
    ".png",
    ".jpg",
    ".jpeg",
    ".gif",
    ".map",
    ".node",
    ".pdf",
}

MOJIBAKE_MARKERS = ("Ã", "Â", "Æ", "�")


@dataclass
class PdfObject:
    number: int
    content: bytes


def escape_pdf_text(value: str) -> str:
    return value.replace("\\", "\\\\").replace("(", "\\(").replace(")", "\\)")


def normalize_text(value: str) -> str:
    return value.encode("cp1252", "replace").decode("cp1252")


def maybe_fix_mojibake(value: str) -> str:
    if not any(marker in value for marker in MOJIBAKE_MARKERS):
        return value

    repaired = value
    for _ in range(2):
        try:
            candidate = repaired.encode("latin-1").decode("utf-8")
        except UnicodeError:
            break
        if candidate == repaired:
            break
        old_hits = sum(repaired.count(marker) for marker in MOJIBAKE_MARKERS)
        new_hits = sum(candidate.count(marker) for marker in MOJIBAKE_MARKERS)
        if new_hits >= old_hits:
            break
        repaired = candidate
    return repaired


def discover_files(root: Path) -> list[Path]:
    files: list[Path] = []
    for path in sorted(root.rglob("*")):
        if not path.is_file():
            continue
        relative = path.relative_to(root)
        if any(part in EXCLUDED_DIRS for part in relative.parts):
            continue
        if path.suffix.lower() in EXCLUDED_SUFFIXES:
            continue
        if path.name in INCLUDE_FILENAMES or path.suffix.lower() in INCLUDE_EXTENSIONS:
            files.append(path)
    return files


def read_source(path: Path) -> str:
    data = path.read_bytes()
    for encoding in ("utf-8-sig", "utf-8", "cp1252", "latin-1"):
        try:
            text = data.decode(encoding)
            break
        except UnicodeDecodeError:
            continue
    else:
        text = data.decode("utf-8", errors="replace")

    text = maybe_fix_mojibake(text)
    text = text.replace("\r\n", "\n").replace("\r", "\n")
    if not text.endswith("\n"):
        text += "\n"
    return text


def build_document_lines(files: Iterable[Path], root: Path) -> list[str]:
    lines = [
        "MINI PROTHEUS - Codigo fonte do projeto",
        "",
        "Documento gerado automaticamente com os arquivos relevantes do repositorio.",
        "Exclusoes aplicadas: node_modules, dist, __pycache__, caches e binarios.",
        "",
    ]
    for path in files:
        relative = path.relative_to(root).as_posix()
        lines.append("=" * 100)
        lines.append(f"ARQUIVO: {relative}")
        lines.append("=" * 100)
        source = read_source(path)
        source_lines = source.split("\n")
        for idx, raw_line in enumerate(source_lines, start=1):
            if idx == len(source_lines) and raw_line == "":
                continue
            lines.append(f"{idx:04d}: {raw_line}")
        lines.append("")
    return lines


def split_pages(lines: list[str], max_lines: int = 54) -> list[list[str]]:
    pages: list[list[str]] = []
    current: list[str] = []
    line_count = 0
    for line in lines:
        wrapped = wrap_line(line, width=100)
        if line_count + len(wrapped) > max_lines and current:
            pages.append(current)
            current = []
            line_count = 0
        current.extend(wrapped)
        line_count += len(wrapped)
    if current:
        pages.append(current)
    return pages


def wrap_line(text: str, width: int) -> list[str]:
    normalized = normalize_text(text)
    if len(normalized) <= width:
        return [normalized]
    parts = []
    remaining = normalized
    while len(remaining) > width:
        parts.append(remaining[:width])
        remaining = remaining[width:]
    if remaining:
        parts.append(remaining)
    return parts


def make_stream(page_lines: list[str], page_number: int, total_pages: int) -> bytes:
    commands = ["BT", "/F1 9 Tf", "50 790 Td", "12 TL"]
    for line in page_lines:
        commands.append(f"({escape_pdf_text(line)}) Tj")
        commands.append("T*")
    commands.append("T*")
    commands.append(f"(Pagina {page_number}/{total_pages}) Tj")
    commands.append("ET")
    body = "\n".join(commands).encode("cp1252", "replace")
    return f"<< /Length {len(body)} >>\nstream\n".encode("ascii") + body + b"\nendstream"


def build_pdf(pages: list[list[str]], output: Path) -> None:
    objects: list[PdfObject] = []
    font_id = 1
    pages_id = 2
    total_pages = len(pages)

    objects.append(
        PdfObject(font_id, b"<< /Type /Font /Subtype /Type1 /BaseFont /Courier /Encoding /WinAnsiEncoding >>")
    )

    page_ids: list[int] = []
    next_id = 3
    for _ in pages:
        content_id = next_id
        page_id = next_id + 1
        page_ids.append(page_id)
        next_id += 2

    kids = " ".join(f"{page_id} 0 R" for page_id in page_ids)
    objects.append(PdfObject(pages_id, f"<< /Type /Pages /Kids [{kids}] /Count {total_pages} >>".encode("ascii")))

    next_id = 3
    for index, page in enumerate(pages, start=1):
        content_id = next_id
        page_id = next_id + 1
        objects.append(PdfObject(content_id, make_stream(page, index, total_pages)))
        page_content = (
            f"<< /Type /Page /Parent {pages_id} 0 R /MediaBox [0 0 612 842] "
            f"/Resources << /Font << /F1 {font_id} 0 R >> >> /Contents {content_id} 0 R >>"
        ).encode("ascii")
        objects.append(PdfObject(page_id, page_content))
        next_id += 2

    catalog_id = next_id
    objects.append(PdfObject(catalog_id, f"<< /Type /Catalog /Pages {pages_id} 0 R >>".encode("ascii")))

    xref_positions: list[int] = [0]
    chunks = [b"%PDF-1.4\n%\xe2\xe3\xcf\xd3\n"]
    current_offset = len(chunks[0])
    for obj in objects:
        xref_positions.append(current_offset)
        obj_header = f"{obj.number} 0 obj\n".encode("ascii")
        obj_footer = b"\nendobj\n"
        chunk = obj_header + obj.content + obj_footer
        chunks.append(chunk)
        current_offset += len(chunk)

    xref_offset = current_offset
    xref = [f"xref\n0 {len(objects) + 1}\n".encode("ascii"), b"0000000000 65535 f \n"]
    for position in xref_positions[1:]:
        xref.append(f"{position:010d} 00000 n \n".encode("ascii"))
    trailer = (
        f"trailer\n<< /Size {len(objects) + 1} /Root {catalog_id} 0 R >>\n"
        f"startxref\n{xref_offset}\n%%EOF\n"
    ).encode("ascii")

    output.write_bytes(b"".join(chunks + xref + [trailer]))


def main() -> None:
    files = discover_files(ROOT)
    lines = build_document_lines(files, ROOT)
    pages = split_pages(lines)
    build_pdf(pages, OUTPUT)
    print(f"PDF gerado: {OUTPUT}")
    print(f"Arquivos incluidos: {len(files)}")
    print(f"Paginas: {len(pages)}")


if __name__ == "__main__":
    main()
