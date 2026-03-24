from datetime import date

from app.core.exceptions import BusinessError
from app.infra.db import fetchone_dict


def fechamento_periodo_aberto_tx(cur, filial: str, data_ref: date) -> bool:
    cur.execute(
        """
        SELECT TOP 1 F7_FECHADO
        FROM dbo.SF7_FECHAMENTO
        WHERE F7_FILIAL=? AND F7_ANO=? AND F7_MES=?
          AND (D_E_L_E_T_ IS NULL OR D_E_L_E_T_ <> '*')
        """,
        (filial, int(data_ref.year), int(data_ref.month)),
    )
    row = fetchone_dict(cur)
    if not row:
        return True
    return not bool(row["F7_FECHADO"])


def fechamento_validar_periodo_tx(cur, filial: str, data_ref: date) -> None:
    if not fechamento_periodo_aberto_tx(cur, filial, data_ref):
        raise BusinessError("Período fechado para esta filial")


def fechamento_fechar_tx(cur, filial: str, ano: int, mes: int, usuario: str | None):
    cur.execute(
        """
        SELECT ID FROM dbo.SF7_FECHAMENTO
        WHERE F7_FILIAL=? AND F7_ANO=? AND F7_MES=?
          AND (D_E_L_E_T_ IS NULL OR D_E_L_E_T_ <> '*')
        """,
        (filial, int(ano), int(mes)),
    )
    row = cur.fetchone()
    if row:
        cur.execute(
            """
            UPDATE dbo.SF7_FECHAMENTO
            SET F7_FECHADO=1, F7_USUARIO=?, F7_DATA=SYSDATETIME()
            WHERE F7_FILIAL=? AND F7_ANO=? AND F7_MES=?
            """,
            (usuario, filial, int(ano), int(mes)),
        )
        return
    cur.execute(
        """
        INSERT INTO dbo.SF7_FECHAMENTO (F7_FILIAL, F7_ANO, F7_MES, F7_FECHADO, F7_USUARIO)
        VALUES (?, ?, ?, 1, ?)
        """,
        (filial, int(ano), int(mes), usuario),
    )


def fechamento_abrir_tx(cur, filial: str, ano: int, mes: int, usuario: str | None):
    cur.execute(
        """
        UPDATE dbo.SF7_FECHAMENTO
        SET F7_FECHADO=0, F7_USUARIO=?, F7_DATA=SYSDATETIME()
        WHERE F7_FILIAL=? AND F7_ANO=? AND F7_MES=?
          AND (D_E_L_E_T_ IS NULL OR D_E_L_E_T_ <> '*')
        """,
        (usuario, filial, int(ano), int(mes)),
    )
