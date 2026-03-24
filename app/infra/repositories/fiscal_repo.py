from app.infra.db import fetchone_dict, fetchall_dict
from app.domain.errors import BusinessError
from app.infra.repositories.sx5_repo import sx5_obter_tx, sx5_criar_tx
from app.infra.repositories.fiscal_ncm_repo import ncm_obter_tx


def fiscal_get_tes_tx(cur, filial: str, tes_cod: str) -> dict:
    cur.execute(
        """
        SELECT TOP 1
          F4_COD,
          F4_TIPO,
          F4_CFOP,
          F4_GERA_TIT,
          F4_GERA_EST,
          F4_ICMS,
          F4_IPI,
          F4_PIS,
          F4_COFINS,
          F4_ICMS_ST,
          F4_DIFAL,
          F4_CST_ICMS,
          F4_CSOSN,
          F4_CST_PIS,
          F4_CST_COFINS
        FROM dbo.SF4_FISCAL
        WHERE F4_FILIAL=? AND F4_COD=?
        """,
        (filial, str(tes_cod).strip()),
    )
    row = fetchone_dict(cur)
    if not row:
        raise BusinessError("TES não encontrado para a filial")

    # valida TES no dicionário SX5 (tabela TES)
    if sx5_obter_tx(cur, filial=filial, tabela="TES", chave=str(tes_cod).strip()) is None:
        raise BusinessError("TES não cadastrado no SX5 (tabela TES)")

    # valida CFOP no dicionário SX5 (tabela CFOP)
    cfop = (row.get("F4_CFOP") or "").strip()
    if cfop and sx5_obter_tx(cur, filial=filial, tabela="CFOP", chave=cfop) is None:
        raise BusinessError("CFOP não cadastrado no SX5 (tabela CFOP)")
    return row


def fiscal_get_tx(cur, filial: str, tes_cod: str | None = None) -> dict:
    if tes_cod:
        return fiscal_get_tes_tx(cur, filial, tes_cod)

    cur.execute(
        """
        SELECT TOP 1
          F4_COD,
          F4_TIPO,
          F4_CFOP,
          F4_GERA_TIT,
          F4_GERA_EST,
          F4_ICMS,
          F4_IPI,
          F4_PIS,
          F4_COFINS,
          F4_ICMS_ST,
          F4_DIFAL,
          F4_CST_ICMS,
          F4_CSOSN,
          F4_CST_PIS,
          F4_CST_COFINS
        FROM dbo.SF4_FISCAL
        WHERE F4_FILIAL=?
        ORDER BY F4_COD
        """,
        (filial,),
    )
    row = fetchone_dict(cur)
    if not row:
        raise BusinessError("Parâmetros fiscais não cadastrados para a filial")
    return row


def fiscal_upsert_tx(
    cur,
    filial: str,
    tes_cod: str,
    cfop: str,
    icms: float,
    ipi: float,
    pis: float = 0.0,
    cofins: float = 0.0,
    icms_st: float = 0.0,
    difal: float = 0.0,
    cst_icms: str | None = None,
    csosn: str | None = None,
    cst_pis: str | None = None,
    cst_cofins: str | None = None,
    tipo: str = "S",
    gera_tit: bool = True,
    gera_est: bool = True,
    descr: str | None = None,
) -> None:
    tes_cod = (tes_cod or "").strip()
    cfop = (cfop or "").strip()
    tipo = (tipo or "S").strip().upper()

    if not tes_cod:
        raise BusinessError("TES é obrigatório")
    if not cfop:
        raise BusinessError("CFOP é obrigatório")
    if tipo not in {"S", "E"}:
        raise BusinessError("Tipo TES inválido (S/E)")

    # garante SX5 (TES/CFOP)
    if sx5_obter_tx(cur, filial=filial, tabela="TES", chave=tes_cod) is None:
        sx5_criar_tx(cur, filial=filial, tabela="TES", chave=tes_cod, descr=(descr or f"TES {tes_cod}"), ativo=True)
    if sx5_obter_tx(cur, filial=filial, tabela="CFOP", chave=cfop) is None:
        sx5_criar_tx(cur, filial=filial, tabela="CFOP", chave=cfop, descr=(f"CFOP {cfop}"), ativo=True)

    # upsert SF4
    cur.execute(
        """
        SELECT ID
        FROM dbo.SF4_FISCAL
        WHERE F4_FILIAL=? AND F4_COD=?
        """,
        (filial, tes_cod),
    )
    row = cur.fetchone()
    if row:
        cur.execute(
            """
            UPDATE dbo.SF4_FISCAL
            SET F4_CFOP=?, F4_TIPO=?, F4_GERA_TIT=?, F4_GERA_EST=?, F4_ICMS=?, F4_IPI=?,
                F4_PIS=?, F4_COFINS=?, F4_ICMS_ST=?, F4_DIFAL=?,
                F4_CST_ICMS=?, F4_CSOSN=?, F4_CST_PIS=?, F4_CST_COFINS=?,
                F4_DESC=?
            WHERE F4_FILIAL=? AND F4_COD=?
            """,
            (
                cfop,
                tipo,
                1 if gera_tit else 0,
                1 if gera_est else 0,
                float(icms),
                float(ipi),
                float(pis),
                float(cofins),
                float(icms_st),
                float(difal),
                cst_icms,
                csosn,
                cst_pis,
                cst_cofins,
                descr,
                filial,
                tes_cod,
            ),
        )
        return

    cur.execute(
        """
        INSERT INTO dbo.SF4_FISCAL
          (F4_FILIAL, F4_COD, F4_TIPO, F4_CFOP, F4_GERA_TIT, F4_GERA_EST, F4_ICMS, F4_IPI,
           F4_PIS, F4_COFINS, F4_ICMS_ST, F4_DIFAL, F4_CST_ICMS, F4_CSOSN, F4_CST_PIS, F4_CST_COFINS, F4_DESC)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
        (
            filial,
            tes_cod,
            tipo,
            cfop,
            1 if gera_tit else 0,
            1 if gera_est else 0,
            float(icms),
            float(ipi),
            float(pis),
            float(cofins),
            float(icms_st),
            float(difal),
            cst_icms,
            csosn,
            cst_pis,
            cst_cofins,
            descr,
        ),
    )


def fiscal_listar_tx(cur, filial: str, ativo: bool = True):
    sql = """
        SELECT *
        FROM dbo.SF4_FISCAL
        WHERE F4_FILIAL=?
          AND (D_E_L_E_T_ IS NULL OR D_E_L_E_T_ <> '*')
    """
    params: list = [filial]
    if ativo:
        sql += " AND F4_ATIVO=1"
    sql += " ORDER BY F4_COD"
    cur.execute(sql, tuple(params))
    return fetchall_dict(cur)


def fiscal_inativar_tx(cur, filial: str, tes_cod: str, usuario: str | None = None):
    cur.execute(
        """
        UPDATE dbo.SF4_FISCAL
        SET F4_ATIVO=0,
            D_E_L_E_T_='*',
            R_E_C_D_E_L_=COALESCE(R_E_C_D_E_L_, R_E_C_N_O_)
        WHERE F4_FILIAL=? AND F4_COD=?
        """,
        (filial, tes_cod),
    )
    if cur.rowcount == 0:
        raise BusinessError("TES não encontrado para inativação")


def fiscal_regra_match_tx(
    cur,
    filial: str,
    tes_cod: str,
    cliente_cod: str | None,
    produto: str | None,
) -> dict | None:
    cur.execute(
        """
        SELECT TOP 1 *
        FROM dbo.SF5_FISCAL_REGRAS
        WHERE F5_FILIAL=? AND F5_TES=? AND F5_ATIVO=1
          AND (F5_CLIENTE_COD IS NULL OR F5_CLIENTE_COD=?)
          AND (F5_PRODUTO IS NULL OR F5_PRODUTO=?)
          AND (D_E_L_E_T_ IS NULL OR D_E_L_E_T_ <> '*')
        ORDER BY
          (CASE WHEN F5_CLIENTE_COD IS NULL THEN 0 ELSE 1 END +
           CASE WHEN F5_PRODUTO IS NULL THEN 0 ELSE 1 END) DESC,
          F5_PRIORIDADE DESC,
          ID DESC
        """,
        (filial, str(tes_cod).strip(), cliente_cod, produto),
    )
    return fetchone_dict(cur)


def fiscal_resolver_item_tx(
    cur,
    filial: str,
    tes_cod: str,
    cliente_cod: str | None,
    produto: str | None,
) -> dict:
    base = fiscal_get_tes_tx(cur, filial=filial, tes_cod=tes_cod)
    ncm_row = None
    if produto:
        cur.execute(
            """
            SELECT B1_NCM
            FROM dbo.SB1_PRODUTOS
            WHERE B1_COD=? AND B1_FILIAL=?
              AND (D_E_L_E_T_ IS NULL OR D_E_L_E_T_ <> '*')
            """,
            (produto, filial),
        )
        r = fetchone_dict(cur)
        if r:
            ncm = (r.get("B1_NCM") or "").strip()
            if ncm:
                ncm_row = ncm_obter_tx(cur, filial=filial, ncm=ncm)
    regra = fiscal_regra_match_tx(
        cur,
        filial=filial,
        tes_cod=tes_cod,
        cliente_cod=cliente_cod,
        produto=produto,
    )

    cfop = (
        (regra.get("F5_CFOP") if regra and regra.get("F5_CFOP") is not None else None)
        or (ncm_row.get("F8_CFOP") if ncm_row and ncm_row.get("F8_CFOP") is not None else None)
        or base.get("F4_CFOP")
        or ""
    )
    icms = float(regra["F5_ICMS"]) if regra and regra.get("F5_ICMS") is not None else (
        float(ncm_row["F8_ICMS"]) if ncm_row and ncm_row.get("F8_ICMS") is not None else float(base["F4_ICMS"])
    )
    ipi = float(regra["F5_IPI"]) if regra and regra.get("F5_IPI") is not None else (
        float(ncm_row["F8_IPI"]) if ncm_row and ncm_row.get("F8_IPI") is not None else float(base["F4_IPI"])
    )
    pis = float(regra["F5_PIS"]) if regra and regra.get("F5_PIS") is not None else float(base.get("F4_PIS") or 0)
    cofins = float(regra["F5_COFINS"]) if regra and regra.get("F5_COFINS") is not None else float(base.get("F4_COFINS") or 0)
    icms_st = float(regra["F5_ICMS_ST"]) if regra and regra.get("F5_ICMS_ST") is not None else float(base.get("F4_ICMS_ST") or 0)
    difal = float(regra["F5_DIFAL"]) if regra and regra.get("F5_DIFAL") is not None else float(base.get("F4_DIFAL") or 0)
    cst_icms = (regra.get("F5_CST_ICMS") if regra and regra.get("F5_CST_ICMS") is not None else base.get("F4_CST_ICMS"))
    csosn = (regra.get("F5_CSOSN") if regra and regra.get("F5_CSOSN") is not None else base.get("F4_CSOSN"))
    cst_pis = (regra.get("F5_CST_PIS") if regra and regra.get("F5_CST_PIS") is not None else base.get("F4_CST_PIS"))
    cst_cofins = (regra.get("F5_CST_COFINS") if regra and regra.get("F5_CST_COFINS") is not None else base.get("F4_CST_COFINS"))
    gera_tit = bool(regra["F5_GERA_TIT"]) if regra and regra.get("F5_GERA_TIT") is not None else bool(base.get("F4_GERA_TIT"))
    gera_est = bool(regra["F5_GERA_EST"]) if regra and regra.get("F5_GERA_EST") is not None else bool(base.get("F4_GERA_EST"))

    if not str(cfop).strip():
        raise BusinessError("CFOP n??o definido para o item (TES/regra)")
    if sx5_obter_tx(cur, filial=filial, tabela="CFOP", chave=str(cfop).strip()) is None:
        raise BusinessError("CFOP n??o cadastrado no SX5 (tabela CFOP)")
    return {
        "tes_cod": str(base.get("F4_COD") or tes_cod).strip(),
        "tes_tipo": str(base.get("F4_TIPO") or "").strip().upper(),
        "cfop": str(cfop).strip(),
        "icms": float(icms),
        "ipi": float(ipi),
        "pis": float(pis),
        "cofins": float(cofins),
        "icms_st": float(icms_st),
        "difal": float(difal),
        "cst_icms": (str(cst_icms).strip() if cst_icms is not None else None),
        "csosn": (str(csosn).strip() if csosn is not None else None),
        "cst_pis": (str(cst_pis).strip() if cst_pis is not None else None),
        "cst_cofins": (str(cst_cofins).strip() if cst_cofins is not None else None),
        "gera_tit": bool(gera_tit),
        "gera_est": bool(gera_est),
        "regra_id": int(regra["ID"]) if regra else None,
    }


def fiscal_regra_listar_tx(
    cur,
    filial: str,
    tes_cod: str | None = None,
    cliente_cod: str | None = None,
    produto: str | None = None,
    ativos: bool = True,
):
    sql = """
        SELECT *
        FROM dbo.SF5_FISCAL_REGRAS
        WHERE F5_FILIAL=?
          AND (D_E_L_E_T_ IS NULL OR D_E_L_E_T_ <> '*')
    """
    params: list = [filial]
    if tes_cod:
        sql += " AND F5_TES=?"
        params.append(str(tes_cod).strip())
    if cliente_cod:
        sql += " AND F5_CLIENTE_COD=?"
        params.append(str(cliente_cod).strip())
    if produto:
        sql += " AND F5_PRODUTO=?"
        params.append(str(produto).strip())
    if ativos:
        sql += " AND F5_ATIVO=1"
    sql += " ORDER BY F5_PRIORIDADE DESC, ID DESC"
    cur.execute(sql, tuple(params))
    return fetchall_dict(cur)


def fiscal_regra_upsert_tx(
    cur,
    filial: str,
    tes_cod: str,
    cliente_cod: str | None,
    produto: str | None,
    cfop: str | None,
    icms: float | None,
    ipi: float | None,
    pis: float | None = None,
    cofins: float | None = None,
    icms_st: float | None = None,
    difal: float | None = None,
    cst_icms: str | None = None,
    csosn: str | None = None,
    cst_pis: str | None = None,
    cst_cofins: str | None = None,
    gera_tit: bool | None = None,
    gera_est: bool | None = None,
    prioridade: int = 0,
    ativo: bool = True,
    regra_id: int | None = None,
) -> int:
    tes_cod = (tes_cod or "").strip()
    if not tes_cod:
        raise BusinessError("TES é obrigatório")

    if cfop:
        if sx5_obter_tx(cur, filial=filial, tabela="CFOP", chave=str(cfop).strip()) is None:
            raise BusinessError("CFOP não cadastrado no SX5 (tabela CFOP)")

    if regra_id:
        cur.execute(
            """
            UPDATE dbo.SF5_FISCAL_REGRAS
            SET F5_TES=?,
                F5_CLIENTE_COD=?,
                F5_PRODUTO=?,
                F5_CFOP=?,
                F5_ICMS=?,
                F5_IPI=?,
                F5_PIS=?,
                F5_COFINS=?,
                F5_ICMS_ST=?,
                F5_DIFAL=?,
                F5_CST_ICMS=?,
                F5_CSOSN=?,
                F5_CST_PIS=?,
                F5_CST_COFINS=?,
                F5_GERA_TIT=?,
                F5_GERA_EST=?,
                F5_PRIORIDADE=?,
                F5_ATIVO=?
            WHERE ID=? AND F5_FILIAL=?
            """,
            (
                tes_cod,
                cliente_cod,
                produto,
                cfop,
                icms,
                ipi,
                pis,
                cofins,
                icms_st,
                difal,
                cst_icms,
                csosn,
                cst_pis,
                cst_cofins,
                1 if gera_tit is True else (0 if gera_tit is False else None),
                1 if gera_est is True else (0 if gera_est is False else None),
                int(prioridade),
                1 if ativo else 0,
                int(regra_id),
                filial,
            ),
        )
        if cur.rowcount == 0:
            raise BusinessError("Regra fiscal não encontrada")
        return int(regra_id)

    cur.execute(
        """
        INSERT INTO dbo.SF5_FISCAL_REGRAS
          (F5_FILIAL, F5_TES, F5_CLIENTE_COD, F5_PRODUTO, F5_CFOP, F5_ICMS, F5_IPI,
           F5_PIS, F5_COFINS, F5_ICMS_ST, F5_DIFAL, F5_CST_ICMS, F5_CSOSN, F5_CST_PIS, F5_CST_COFINS,
           F5_GERA_TIT, F5_GERA_EST, F5_PRIORIDADE, F5_ATIVO)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?);
        SELECT CAST(SCOPE_IDENTITY() AS INT) AS id;
        """,
        (
            filial,
            tes_cod,
            cliente_cod,
            produto,
            cfop,
            icms,
            ipi,
            pis,
            cofins,
            icms_st,
            difal,
            cst_icms,
            csosn,
            cst_pis,
            cst_cofins,
            1 if gera_tit is True else (0 if gera_tit is False else None),
            1 if gera_est is True else (0 if gera_est is False else None),
            int(prioridade),
            1 if ativo else 0,
        ),
    )
    row = fetchone_dict(cur)
    return int(row["id"])


def fiscal_regra_inativar_tx(cur, regra_id: int):
    cur.execute(
        """
        UPDATE dbo.SF5_FISCAL_REGRAS
        SET F5_ATIVO=0,
            D_E_L_E_T_='*',
            R_E_C_D_E_L_=COALESCE(R_E_C_D_E_L_, R_E_C_N_O_)
        WHERE ID=?
        """,
        (int(regra_id),),
    )
    if cur.rowcount == 0:
        raise BusinessError("Regra fiscal não encontrada")
