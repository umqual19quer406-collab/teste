from app.core.exceptions import BusinessError
from app.infra.db import fetchone_dict, fetchall_dict


def sb1_get_tx(cur, produto: str, filial: str) -> dict:
    cur.execute(
        """
        SELECT B1_COD, B1_DESC, B1_PRECO, B1_ESTOQUE, B1_RESERVADO, B1_CM, B1_FILIAL, B1_NCM
        FROM SB1_PRODUTOS
        WHERE B1_COD=? AND B1_FILIAL=?
          AND (D_E_L_E_T_ IS NULL OR D_E_L_E_T_ <> '*')
        """,
        (produto, filial),
    )
    row = fetchone_dict(cur)
    if not row:
        raise BusinessError("Produto não encontrado na filial")
    return row


def sb1_upsert_tx(cur, cod: str, desc: str, preco: float, filial: str) -> None:
    cur.execute(
        "SELECT 1 FROM SB1_PRODUTOS WHERE B1_COD=? AND B1_FILIAL=? AND (D_E_L_E_T_ IS NULL OR D_E_L_E_T_ <> '*')",
        (cod, filial),
    )
    existe = cur.fetchone() is not None
    if existe:
        cur.execute(
            "UPDATE SB1_PRODUTOS SET B1_DESC=?, B1_PRECO=? WHERE B1_COD=? AND B1_FILIAL=?",
            (desc, float(preco), cod, filial),
        )
    else:
        cur.execute(
            """
            INSERT INTO SB1_PRODUTOS (B1_COD, B1_DESC, B1_PRECO, B1_ESTOQUE, B1_RESERVADO, B1_CM, B1_FILIAL)
            VALUES (?, ?, ?, 0, 0, 0, ?)
            """,
            (cod, desc, float(preco), filial),
        )


def sb1_atualizar_cm_tx(cur, produto: str, filial: str, cm_novo: float) -> None:
    cur.execute(
        "UPDATE SB1_PRODUTOS SET B1_CM=? WHERE B1_COD=? AND B1_FILIAL=?",
        (float(cm_novo), produto, filial),
    )


def sb1_entrada_tx(cur, produto: str, filial: str, qtd: int) -> None:
    cur.execute(
        "UPDATE SB1_PRODUTOS SET B1_ESTOQUE = B1_ESTOQUE + ? WHERE B1_COD=? AND B1_FILIAL=?",
        (int(qtd), produto, filial),
    )


def sb1_reservar_atomico_tx(cur, produto: str, filial: str, qtd: int) -> None:
    cur.execute(
        """
        UPDATE SB1_PRODUTOS
        SET B1_RESERVADO = B1_RESERVADO + ?
        WHERE B1_COD=? AND B1_FILIAL=?
          AND (B1_ESTOQUE - B1_RESERVADO) >= ?
        """,
        (int(qtd), produto, filial, int(qtd)),
    )
    if cur.rowcount == 0:
        raise BusinessError("Saldo disponível insuficiente para reservar")


def sb1_cancelar_reserva_atomico_tx(cur, produto: str, filial: str, qtd: int) -> None:
    cur.execute(
        """
        UPDATE SB1_PRODUTOS
        SET B1_RESERVADO = B1_RESERVADO - ?
        WHERE B1_COD=? AND B1_FILIAL=?
          AND B1_RESERVADO >= ?
        """,
        (int(qtd), produto, filial, int(qtd)),
    )
    if cur.rowcount == 0:
        raise BusinessError("Não foi possível desreservar (reservado insuficiente)")


def sb1_baixar_e_desreservar_atomico_tx(cur, produto: str, filial: str, qtd: int) -> None:
    cur.execute(
        """
        UPDATE SB1_PRODUTOS
        SET B1_ESTOQUE = B1_ESTOQUE - ?,
            B1_RESERVADO = B1_RESERVADO - ?
        WHERE B1_COD=? AND B1_FILIAL=?
          AND B1_ESTOQUE >= ?
          AND B1_RESERVADO >= ?
        """,
        (int(qtd), int(qtd), produto, filial, int(qtd), int(qtd)),
    )
    if cur.rowcount == 0:
        raise BusinessError("Estoque/reservado insuficiente para confirmar")


def sb1_baixar_atomico_tx(cur, produto: str, filial: str, qtd: int) -> None:
    cur.execute(
        """
        UPDATE SB1_PRODUTOS
        SET B1_ESTOQUE = B1_ESTOQUE - ?
        WHERE B1_COD=? AND B1_FILIAL=?
          AND B1_ESTOQUE - B1_RESERVADO >= ?
        """,
        (int(qtd), produto, filial, int(qtd)),
    )
    if cur.rowcount == 0:
        raise BusinessError("Saldo disponível insuficiente")


def sb1_buscar_tx(cur, filial: str, q: str, limite: int = 20) -> list[dict]:
    termo = (q or "").strip()
    if not termo:
        return []

    like = f"%{termo}%"
    cur.execute(
        """
        SELECT TOP (?) B1_COD, B1_DESC, B1_PRECO, B1_ESTOQUE, B1_RESERVADO, B1_CM, B1_FILIAL, B1_NCM
        FROM SB1_PRODUTOS
        WHERE B1_FILIAL=?
          AND (D_E_L_E_T_ IS NULL OR D_E_L_E_T_ <> '*')
          AND (
            B1_COD LIKE ?
            OR B1_DESC LIKE ?
          )
        ORDER BY B1_COD ASC
        """,
        (int(limite), filial, like, like),
    )
    return fetchall_dict(cur)
