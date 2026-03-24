from datetime import date, datetime, timedelta

import pyodbc

from app.core.exceptions import BusinessError
from app.infra.db import fetchall_dict, fetchone_dict
from app.infra.repositories.serie_repo import resolve_serie_tx, validar_serie_tx
from app.infra.repositories.sx6_repo import sx6_next_tx


def _obter_maior_numero_serie_tx(cur, tabela_fisica: str, campo_num: str, filial: str, serie: str) -> int:
    cur.execute(
        f"""
        SELECT MAX(TRY_CONVERT(INT, {campo_num})) AS maior_num
        FROM dbo.{tabela_fisica}
        WHERE {"E1_FILIAL" if tabela_fisica == "SE1_AR" else "F1_FILIAL"} = ?
          AND {"E1_SERIE" if tabela_fisica == "SE1_AR" else "F1_SERIE"} = ?
          AND (D_E_L_E_T_ IS NULL OR D_E_L_E_T_ <> '*')
        """,
        (filial, serie),
    )
    row = fetchone_dict(cur) or {}
    valor = row.get("maior_num")
    return int(valor) if valor is not None else 0


def _alinhar_sx6_com_serie_tx(cur, filial: str, serie: str, tabela_seq: str, tabela_fisica: str, campo_num: str) -> None:
    maior_existente = _obter_maior_numero_serie_tx(cur, tabela_fisica=tabela_fisica, campo_num=campo_num, filial=filial, serie=serie)
    cur.execute(
        """
        SELECT TOP 1 ID, X6_SEQ
        FROM dbo.SX6_SEQ WITH (UPDLOCK, ROWLOCK)
        WHERE X6_FILIAL=? AND X6_SERIE=? AND X6_TABELA=?
        """,
        (filial, serie, tabela_seq),
    )
    row = fetchone_dict(cur)
    if row:
        seq_atual = int(row["X6_SEQ"])
        if seq_atual < maior_existente:
            cur.execute("UPDATE dbo.SX6_SEQ SET X6_SEQ=? WHERE ID=?", (maior_existente, int(row["ID"])))
        return

    cur.execute(
        """
        INSERT INTO dbo.SX6_SEQ (X6_FILIAL, X6_SERIE, X6_TABELA, X6_SEQ)
        VALUES (?, ?, ?, ?)
        """,
        (filial, serie, tabela_seq, maior_existente),
    )


def ar_criar_tx(
    cur,
    filial: str,
    cliente: str | None,
    valor: float,
    ref_id: int,
    venc_dias: int,
    cliente_cod: str | None = None,
    serie: str | None = None,
) -> None:
    """Cria título em SE1_AR (Contas a Receber)."""

    data = datetime.now()
    venc: date = (data + timedelta(days=int(venc_dias))).date()

    serie = (serie or resolve_serie_tx(cur, filial=filial, tabela="AR")).strip()
    validar_serie_tx(cur, filial=filial, tabela="AR", serie=serie)
    _alinhar_sx6_com_serie_tx(
        cur,
        filial=filial,
        serie=serie,
        tabela_seq="SE1",
        tabela_fisica="SE1_AR",
        campo_num="E1_NUM",
    )

    for _ in range(5):
        e1_num = str(sx6_next_tx(cur, filial=filial, serie=serie, tabela="SE1")).zfill(9)
        try:
            cur.execute(
                """
                INSERT INTO dbo.SE1_AR
                    (E1_DATA,
                     E1_VENC,
                     E1_CLIENTE,
                     E1_CLIENTE_COD,
                     E1_VALOR,
                     E1_STATUS,
                     E1_REF,
                     E1_NUM,
                     E1_SERIE,
                     E1_FILIAL)
                VALUES (?, ?, ?, ?, ?, 'ABERTO', ?, ?, ?, ?)
                """,
                (
                    data,
                    venc,
                    cliente,
                    cliente_cod,
                    float(valor),
                    str(ref_id),
                    e1_num,
                    serie,
                    filial,
                ),
            )
            break
        except pyodbc.IntegrityError as exc:
            msg = str(exc)
            if "UX_SE1_FILIAL_NUM_SERIE" in msg or "2601" in msg or "2627" in msg:
                continue
            raise
    else:
        raise BusinessError("Falha ao gerar E1_NUM único para SE1_AR")


def ap_criar_tx(
    cur,
    filial: str,
    forn: str | None,
    valor: float,
    ref: str,
    venc_dias: int,
    forn_cod: str | None = None,
    serie: str | None = None,
) -> None:
    """Cria título em SF1_AP (Contas a Pagar)."""

    data = datetime.now()
    venc: date = (data + timedelta(days=int(venc_dias))).date()

    serie = (serie or resolve_serie_tx(cur, filial=filial, tabela="AP")).strip()
    validar_serie_tx(cur, filial=filial, tabela="AP", serie=serie)
    _alinhar_sx6_com_serie_tx(
        cur,
        filial=filial,
        serie=serie,
        tabela_seq="SF1",
        tabela_fisica="SF1_AP",
        campo_num="F1_NUM",
    )

    for _ in range(5):
        f1_num = str(sx6_next_tx(cur, filial=filial, serie=serie, tabela="SF1")).zfill(9)
        try:
            cur.execute(
                """
                INSERT INTO dbo.SF1_AP
                    (F1_DATA,
                     F1_VENC,
                     F1_FORN,
                     F1_FORN_COD,
                     F1_VALOR,
                     F1_STATUS,
                     F1_REF,
                     F1_NUM,
                     F1_SERIE,
                     F1_FILIAL)
                VALUES (?, ?, ?, ?, ?, 'ABERTO', ?, ?, ?, ?)
                """,
                (
                    data,
                    venc,
                    forn,
                    forn_cod,
                    float(valor),
                    ref,
                    f1_num,
                    serie,
                    filial,
                ),
            )
            break
        except pyodbc.IntegrityError as exc:
            msg = str(exc)
            if "UX_SF1_FILIAL_NUM_SERIE" in msg or "2601" in msg or "2627" in msg:
                continue
            raise
    else:
        raise BusinessError("Falha ao gerar F1_NUM único para SF1_AP")


def listar_ar_tx(cur, filial: str, status: str):
    cur.execute(
        """
        SELECT *
        FROM dbo.SE1_AR
        WHERE E1_FILIAL = ? AND E1_STATUS = ?
          AND (D_E_L_E_T_ IS NULL OR D_E_L_E_T_ <> '*')
        ORDER BY ID DESC
        """,
        (filial, status),
    )
    return fetchall_dict(cur)


def listar_ap_tx(cur, filial: str, status: str):
    cur.execute(
        """
        SELECT *
        FROM dbo.SF1_AP
        WHERE F1_FILIAL = ? AND F1_STATUS = ?
          AND (D_E_L_E_T_ IS NULL OR D_E_L_E_T_ <> '*')
        ORDER BY ID DESC
        """,
        (filial, status),
    )
    return fetchall_dict(cur)


def _get_ar_for_update(cur, titulo_id: int):
    cur.execute(
        """
        SELECT *
        FROM dbo.SE1_AR WITH (UPDLOCK, ROWLOCK)
        WHERE ID = ?
          AND (D_E_L_E_T_ IS NULL OR D_E_L_E_T_ <> '*')
        """,
        (int(titulo_id),),
    )
    return fetchone_dict(cur)


def _get_ap_for_update(cur, titulo_id: int):
    cur.execute(
        """
        SELECT *
        FROM dbo.SF1_AP WITH (UPDLOCK, ROWLOCK)
        WHERE ID = ?
          AND (D_E_L_E_T_ IS NULL OR D_E_L_E_T_ <> '*')
        """,
        (int(titulo_id),),
    )
    return fetchone_dict(cur)


def criar_mov_caixa_tx(
    cur,
    filial: str,
    conta_id: int,
    tipo: str,
    valor: float,
    origem_tipo: str,
    origem_id: int | None,
    usuario: str | None,
    hist: str | None = None,
) -> None:
    cur.execute(
        """
        INSERT INTO dbo.SE5_MOV
          (E5_FILIAL, E5_CONTA_ID, E5_TIPO, E5_VALOR, E5_HIST, E5_ORIGEM_TIPO, E5_ORIGEM_ID, E5_USUARIO)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """,
        (filial, int(conta_id), tipo, float(valor), hist, origem_tipo, origem_id, usuario),
    )


def baixar_ar_atomico_tx(cur, titulo_id: int) -> None:
    cur.execute(
        """
        UPDATE dbo.SE1_AR
        SET E1_STATUS='BAIXADO'
        WHERE ID=? AND E1_STATUS='ABERTO'
        """,
        (int(titulo_id),),
    )
    if cur.rowcount == 0:
        cur.execute(
            "SELECT E1_STATUS FROM dbo.SE1_AR WHERE ID=? AND (D_E_L_E_T_ IS NULL OR D_E_L_E_T_ <> '*')",
            (int(titulo_id),),
        )
        titulo = fetchone_dict(cur)
        if not titulo:
            raise BusinessError("Título não encontrado")
        raise BusinessError("Título não está em aberto")


def baixar_ap_atomico_tx(cur, titulo_id: int) -> None:
    cur.execute(
        """
        UPDATE dbo.SF1_AP
        SET F1_STATUS='BAIXADO'
        WHERE ID=? AND F1_STATUS='ABERTO'
        """,
        (int(titulo_id),),
    )
    if cur.rowcount == 0:
        cur.execute(
            "SELECT F1_STATUS FROM dbo.SF1_AP WHERE ID=? AND (D_E_L_E_T_ IS NULL OR D_E_L_E_T_ <> '*')",
            (int(titulo_id),),
        )
        titulo = fetchone_dict(cur)
        if not titulo:
            raise BusinessError("Título não encontrado")
        raise BusinessError("Título não está em aberto")


def se5_mov_tx(
    cur,
    filial: str,
    conta_id: int,
    tipo: str,
    valor: float,
    hist: str,
    origem_tipo: str,
    origem_id: int | None,
    usuario: str,
    categ_id: int | None = None,
) -> int:
    cur.execute(
        """
        INSERT INTO dbo.SE5_MOV
          (E5_DATA, E5_FILIAL, E5_CONTA_ID, E5_TIPO, E5_VALOR,
           E5_HIST, E5_ORIGEM_TIPO, E5_ORIGEM_ID, E5_USUARIO, E5_CATEG_ID)
        VALUES (SYSDATETIME(), ?, ?, ?, ?, ?, ?, ?, ?, ?);
        SELECT CAST(SCOPE_IDENTITY() AS INT) AS id;
        """,
        (
            filial,
            int(conta_id),
            tipo,
            float(valor),
            hist,
            origem_tipo,
            int(origem_id) if origem_id is not None else None,
            usuario,
            categ_id,
        ),
    )

    row = fetchone_dict(cur)
    return int(row["id"])


def receber_ar_e_gerar_caixa_tx(
    cur,
    titulo_id: int,
    conta_id: int,
    usuario: str,
    categ_id: int | None = None,
) -> int:
    cur.execute(
        """
        SELECT ID, E1_VALOR, E1_STATUS, E1_FILIAL
        FROM dbo.SE1_AR
        WHERE ID = ?
          AND (D_E_L_E_T_ IS NULL OR D_E_L_E_T_ <> '*')
        """,
        (int(titulo_id),),
    )
    titulo = fetchone_dict(cur)
    if not titulo:
        raise BusinessError("Título AR não encontrado")
    if titulo["E1_STATUS"] != "ABERTO":
        raise BusinessError("Título AR não está em aberto")

    mov_id = se5_mov_tx(
        cur,
        filial=titulo["E1_FILIAL"],
        conta_id=int(conta_id),
        tipo="E",
        valor=float(titulo["E1_VALOR"]),
        hist=f"Recebimento AR {titulo_id}",
        origem_tipo="SE1",
        origem_id=titulo_id,
        usuario=usuario,
        categ_id=categ_id,
    )
    cur.execute(
        """
        SELECT 1
        FROM dbo.SE5_CONTAS
        WHERE ID=? AND E5_FILIAL=? AND E5_ATIVA=1
          AND (D_E_L_E_T_ IS NULL OR D_E_L_E_T_ <> '*')
        """,
        (int(conta_id), titulo["E1_FILIAL"]),
    )
    if cur.fetchone() is None:
        raise BusinessError("Conta de caixa inválida/inativa para esta filial")

    cur.execute(
        """
        UPDATE dbo.SE1_AR
        SET E1_STATUS='BAIXADO',
            E1_SE5_ID=?
        WHERE ID=? AND E1_STATUS='ABERTO'
        """,
        (mov_id, int(titulo_id)),
    )
    if cur.rowcount == 0:
        raise BusinessError("Falha ao baixar AR")

    return mov_id


def pagar_ap_e_gerar_caixa_tx(
    cur,
    titulo_id: int,
    conta_id: int,
    usuario: str,
    categ_id: int | None = None,
) -> int:
    cur.execute(
        """
        SELECT ID, F1_VALOR, F1_STATUS, F1_FILIAL
        FROM dbo.SF1_AP
        WHERE ID = ?
          AND (D_E_L_E_T_ IS NULL OR D_E_L_E_T_ <> '*')
        """,
        (int(titulo_id),),
    )
    titulo = fetchone_dict(cur)
    if not titulo:
        raise BusinessError("Título AP não encontrado")
    if titulo["F1_STATUS"] != "ABERTO":
        raise BusinessError("Título AP não está em aberto")

    mov_id = se5_mov_tx(
        cur,
        filial=titulo["F1_FILIAL"],
        conta_id=int(conta_id),
        tipo="S",
        valor=float(titulo["F1_VALOR"]),
        hist=f"Pagamento AP {titulo_id}",
        origem_tipo="SF1",
        origem_id=titulo_id,
        usuario=usuario,
        categ_id=categ_id,
    )
    cur.execute(
        """
        SELECT 1
        FROM dbo.SE5_CONTAS
        WHERE ID=? AND E5_FILIAL=? AND E5_ATIVA=1
          AND (D_E_L_E_T_ IS NULL OR D_E_L_E_T_ <> '*')
        """,
        (int(conta_id), titulo["F1_FILIAL"]),
    )
    if cur.fetchone() is None:
        raise BusinessError("Conta de caixa inválida/inativa para esta filial")

    cur.execute(
        """
        UPDATE dbo.SF1_AP
        SET F1_STATUS='BAIXADO',
            F1_SE5_ID=?
        WHERE ID=? AND F1_STATUS='ABERTO'
        """,
        (mov_id, int(titulo_id)),
    )
    if cur.rowcount == 0:
        raise BusinessError("Falha ao baixar AP")

    return mov_id


def listar_contas_caixa_tx(cur, filial: str):
    cur.execute(
        """
        SELECT ID, E5_FILIAL, E5_NOME, E5_TIPO, E5_ATIVA
        FROM dbo.SE5_CONTAS
        WHERE E5_FILIAL = ?
          AND (D_E_L_E_T_ IS NULL OR D_E_L_E_T_ <> '*')
        ORDER BY E5_ATIVA DESC, E5_NOME ASC
        """,
        (filial,),
    )
    return fetchall_dict(cur)


def extrato_caixa_tx(cur, filial: str, conta_id: int, de: date | None, ate: date | None):
    filtros = ["m.E5_FILIAL = ?", "m.E5_CONTA_ID = ?"]
    params = [filial, int(conta_id)]

    if de is not None:
        filtros.append("m.E5_DATA >= ?")
        params.append(de)

    if ate is not None:
        filtros.append("m.E5_DATA < DATEADD(DAY, 1, ?)")
        params.append(ate)

    where_sql = " AND ".join(filtros)

    cur.execute(
        f"""
        WITH Mov AS (
          SELECT
            m.ID,
            m.E5_DATA,
            m.E5_FILIAL,
            m.E5_CONTA_ID,
            m.E5_TIPO,
            m.E5_VALOR,
            CASE WHEN m.E5_TIPO='E' THEN m.E5_VALOR ELSE -m.E5_VALOR END AS E5_VALOR_ASSINADO,
            m.E5_HIST,
            m.E5_ORIGEM_TIPO,
            m.E5_ORIGEM_ID,
            m.E5_USUARIO,
            m.E5_CATEG_ID,
            SUM(CASE WHEN m.E5_TIPO='E' THEN m.E5_VALOR ELSE -m.E5_VALOR END)
              OVER (ORDER BY m.E5_DATA ASC, m.ID ASC ROWS UNBOUNDED PRECEDING) AS E5_SALDO_ACUMULADO
          FROM dbo.SE5_MOV m
          WHERE {where_sql}
            AND (m.D_E_L_E_T_ IS NULL OR m.D_E_L_E_T_ <> '*')
        )
        SELECT
          mv.*,
          c.C5_NOME AS CATEG_NOME,
          c.C5_TIPO AS CATEG_TIPO
        FROM Mov mv
        LEFT JOIN dbo.SE5_CATEG c ON c.ID = mv.E5_CATEG_ID
         AND (c.D_E_L_E_T_ IS NULL OR c.D_E_L_E_T_ <> '*')
        ORDER BY mv.E5_DATA DESC, mv.ID DESC
        """,
        tuple(params),
    )
    return fetchall_dict(cur)


def saldo_caixa_simples_tx(cur, filial: str, conta_id: int, ate: date | None):
    filtros = ["E5_FILIAL = ?", "E5_CONTA_ID = ?"]
    params = [filial, int(conta_id)]

    if ate is not None:
        filtros.append("E5_DATA < DATEADD(DAY, 1, ?)")
        params.append(ate)

    where_sql = " AND ".join(filtros)

    cur.execute(
        f"""
        SELECT
          COALESCE(SUM(CASE WHEN E5_TIPO='E' THEN E5_VALOR ELSE 0 END), 0) AS entradas,
          COALESCE(SUM(CASE WHEN E5_TIPO='S' THEN E5_VALOR ELSE 0 END), 0) AS saidas,
          COALESCE(SUM(CASE WHEN E5_TIPO='E' THEN E5_VALOR ELSE -E5_VALOR END), 0) AS saldo
        FROM dbo.SE5_MOV
        WHERE {where_sql}
          AND (D_E_L_E_T_ IS NULL OR D_E_L_E_T_ <> '*')
        """,
        tuple(params),
    )
    return fetchone_dict(cur) or {"entradas": 0, "saidas": 0, "saldo": 0}


def listar_categorias_tx(cur, filial: str, ativas: bool = True):
    if ativas:
        cur.execute(
            """
            SELECT ID, C5_FILIAL, C5_NOME, C5_TIPO, C5_ATIVA
            FROM dbo.SE5_CATEG
            WHERE C5_FILIAL=? AND C5_ATIVA=1
              AND (D_E_L_E_T_ IS NULL OR D_E_L_E_T_ <> '*')
            ORDER BY C5_TIPO, C5_NOME
            """,
            (filial,),
        )
    else:
        cur.execute(
            """
            SELECT ID, C5_FILIAL, C5_NOME, C5_TIPO, C5_ATIVA
            FROM dbo.SE5_CATEG
            WHERE C5_FILIAL=?
              AND (D_E_L_E_T_ IS NULL OR D_E_L_E_T_ <> '*')
            ORDER BY C5_ATIVA DESC, C5_TIPO, C5_NOME
            """,
            (filial,),
        )
    return fetchall_dict(cur)


def criar_categoria_tx(cur, filial: str, nome: str, tipo: str) -> int:
    cur.execute(
        """
        INSERT INTO dbo.SE5_CATEG (C5_FILIAL, C5_NOME, C5_TIPO, C5_ATIVA)
        VALUES (?, ?, ?, 1);
        SELECT CAST(SCOPE_IDENTITY() AS INT) AS id;
        """,
        (filial, nome, tipo),
    )
    row = fetchone_dict(cur)
    return int(row["id"])


def definir_categoria_mov_tx(cur, mov_id: int, categ_id: int | None):
    cur.execute(
        """
        UPDATE dbo.SE5_MOV
        SET E5_CATEG_ID = ?
        WHERE ID = ?
        """,
        (categ_id, int(mov_id)),
    )
    if cur.rowcount == 0:
        raise BusinessError("Movimento não encontrado")


def obter_movimento_tx(cur, mov_id: int):
    cur.execute(
        """
        SELECT
          m.ID,
          m.E5_FILIAL,
          m.E5_DATA,
          m.E5_TIPO,
          m.E5_VALOR,
          m.E5_HIST,
          m.E5_ORIGEM_TIPO,
          m.E5_ORIGEM_ID,
          m.E5_USUARIO,
          m.E5_CATEG_ID,
          c.C5_NOME AS CATEG_NOME,
          c.C5_TIPO AS CATEG_TIPO
        FROM dbo.SE5_MOV m
        LEFT JOIN dbo.SE5_CATEG c
          ON c.ID = m.E5_CATEG_ID
         AND (c.D_E_L_E_T_ IS NULL OR c.D_E_L_E_T_ <> '*')
        WHERE m.ID = ?
          AND (m.D_E_L_E_T_ IS NULL OR m.D_E_L_E_T_ <> '*')
        """,
        (int(mov_id),),
    )
    return fetchone_dict(cur)


def dre_simples_tx(cur, filial: str, de: date | None, ate: date | None):
    filtros = ["m.E5_FILIAL = ?"]
    params = [filial]

    if de is not None:
        filtros.append("m.E5_DATA >= ?")
        params.append(de)
    if ate is not None:
        filtros.append("m.E5_DATA < DATEADD(DAY, 1, ?)")
        params.append(ate)

    where_sql = " AND ".join(filtros)

    cur.execute(
        f"""
        SELECT
          c.C5_TIPO AS grupo,
          COALESCE(SUM(CASE WHEN m.E5_TIPO='E' THEN m.E5_VALOR ELSE -m.E5_VALOR END), 0) AS valor
        FROM dbo.SE5_MOV m
        LEFT JOIN dbo.SE5_CATEG c ON c.ID = m.E5_CATEG_ID
         AND (c.D_E_L_E_T_ IS NULL OR c.D_E_L_E_T_ <> '*')
        WHERE {where_sql}
          AND (m.D_E_L_E_T_ IS NULL OR m.D_E_L_E_T_ <> '*')
        GROUP BY c.C5_TIPO
        ORDER BY c.C5_TIPO
        """,
        tuple(params),
    )
    rows = fetchall_dict(cur)

    cur.execute(
        f"""
        SELECT
          COALESCE(SUM(CASE WHEN m.E5_TIPO='E' THEN m.E5_VALOR ELSE -m.E5_VALOR END), 0) AS total
        FROM dbo.SE5_MOV m
        WHERE {where_sql}
          AND (m.D_E_L_E_T_ IS NULL OR m.D_E_L_E_T_ <> '*')
        """,
        tuple(params),
    )
    total = fetchone_dict(cur) or {"total": 0}

    return {"filial": filial, "de": de, "ate": ate, "linhas": rows, "total": total["total"]}


def cancelar_ar_por_ref_tx(cur, filial: str, pedido_id: int) -> int:
    """Cancela títulos AR abertos vinculados às NFs do pedido."""

    cur.execute(
        """
        SELECT ID
        FROM dbo.SF2_NOTAS
        WHERE F2_FILIAL=? AND F2_PEDIDO_ID=?
        """,
        (filial, int(pedido_id)),
    )
    nf_ids = [str(row[0]) for row in cur.fetchall()]
    if not nf_ids:
        return 0

    cur.execute(
        f"""
        SELECT TOP 1 ID
        FROM dbo.SE1_AR
        WHERE E1_FILIAL=? AND E1_REF IN ({",".join(["?"] * len(nf_ids))})
          AND E1_STATUS='BAIXADO'
          AND (D_E_L_E_T_ IS NULL OR D_E_L_E_T_ <> '*')
        """,
        tuple([filial] + nf_ids),
    )
    if cur.fetchone() is not None:
        raise BusinessError("Não é possível cancelar: AR já está baixado (recebido)")

    cur.execute(
        f"""
        UPDATE dbo.SE1_AR
        SET E1_STATUS='CANCELADO',
            D_E_L_E_T_='*',
            R_E_C_D_E_L_=COALESCE(R_E_C_D_E_L_, R_E_C_N_O_)
        WHERE E1_FILIAL=? AND E1_REF IN ({",".join(["?"] * len(nf_ids))})
          AND E1_STATUS='ABERTO'
        """,
        tuple([filial] + nf_ids),
    )
    return int(cur.rowcount or 0)


def cancelar_ar_por_nf_tx(cur, filial: str, nf_id: int) -> int:
    """Cancela títulos AR abertos vinculados a uma NF específica."""

    cur.execute(
        """
        SELECT TOP 1 ID
        FROM dbo.SE1_AR
        WHERE E1_FILIAL=? AND E1_REF=? AND E1_STATUS='BAIXADO'
          AND (D_E_L_E_T_ IS NULL OR D_E_L_E_T_ <> '*')
        """,
        (filial, str(nf_id)),
    )
    if cur.fetchone() is not None:
        raise BusinessError("Não é possível cancelar: AR já está baixado (recebido)")

    cur.execute(
        """
        UPDATE dbo.SE1_AR
        SET E1_STATUS='CANCELADO',
            D_E_L_E_T_='*',
            R_E_C_D_E_L_=COALESCE(R_E_C_D_E_L_, R_E_C_N_O_)
        WHERE E1_FILIAL=? AND E1_REF=? AND E1_STATUS='ABERTO'
        """,
        (filial, str(nf_id)),
    )
    return int(cur.rowcount or 0)


def ar_listar_por_pedido_tx(cur, pedido_id: int) -> list[dict]:
    cur.execute(
        """
        SELECT e1.*
        FROM dbo.SE1_AR e1
        INNER JOIN dbo.SF2_NOTAS f2 ON f2.ID = TRY_CAST(e1.E1_REF AS INT)
        WHERE f2.F2_PEDIDO_ID = ?
          AND (e1.D_E_L_E_T_ IS NULL OR e1.D_E_L_E_T_ <> '*')
        ORDER BY e1.ID DESC
        """,
        (int(pedido_id),),
    )
    return fetchall_dict(cur)


def ar_ultimo_por_pedido_tx(cur, pedido_id: int) -> dict | None:
    cur.execute(
        """
        SELECT TOP 1 e1.*
        FROM dbo.SE1_AR e1
        INNER JOIN dbo.SF2_NOTAS f2 ON f2.ID = TRY_CAST(e1.E1_REF AS INT)
        WHERE f2.F2_PEDIDO_ID = ?
          AND (e1.D_E_L_E_T_ IS NULL OR e1.D_E_L_E_T_ <> '*')
        ORDER BY e1.ID DESC
        """,
        (int(pedido_id),),
    )
    return fetchone_dict(cur)


def ar_cancelar_atomico_tx(cur, titulo_id: int) -> None:
    cur.execute(
        """
        UPDATE dbo.SE1_AR
        SET E1_STATUS='CANCELADO',
            D_E_L_E_T_='*',
            R_E_C_D_E_L_=COALESCE(R_E_C_D_E_L_, R_E_C_N_O_)
        WHERE ID=? AND E1_STATUS='ABERTO'
        """,
        (int(titulo_id),),
    )
    if cur.rowcount == 0:
        cur.execute(
            "SELECT E1_STATUS FROM dbo.SE1_AR WHERE ID=? AND (D_E_L_E_T_ IS NULL OR D_E_L_E_T_ <> '*')",
            (int(titulo_id),),
        )
        titulo = fetchone_dict(cur)
        if not titulo:
            raise BusinessError("Título AR não encontrado")
        raise BusinessError("Título AR não está em aberto")
