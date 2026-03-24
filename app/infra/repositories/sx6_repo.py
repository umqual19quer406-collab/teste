from __future__ import annotations

from app.infra.db import fetchone_dict
from app.core.exceptions import BusinessError


def sx6_next_tx(cur, filial: str, serie: str, tabela: str) -> int:
    filial = (filial or "01").strip()
    serie = (serie or "").strip()
    tabela = (tabela or "").strip().upper()
    if not tabela:
        raise BusinessError("Tabela SX6 inválida")

    # lock row for update
    cur.execute(
        """
        SELECT TOP 1 ID, X6_SEQ
        FROM dbo.SX6_SEQ WITH (UPDLOCK, ROWLOCK)
        WHERE X6_FILIAL=? AND X6_SERIE=? AND X6_TABELA=?
        """,
        (filial, serie, tabela),
    )
    row = fetchone_dict(cur)
    if row:
        seq = int(row["X6_SEQ"]) + 1
        cur.execute(
            "UPDATE dbo.SX6_SEQ SET X6_SEQ=? WHERE ID=?",
            (seq, int(row["ID"])),
        )
        return seq

    # create first
    cur.execute(
        """
        INSERT INTO dbo.SX6_SEQ (X6_FILIAL, X6_SERIE, X6_TABELA, X6_SEQ)
        VALUES (?, ?, ?, 1);
        SELECT CAST(SCOPE_IDENTITY() AS INT) AS id;
        """,
        (filial, serie, tabela),
    )
    return 1
