from datetime import date 
from app.infra.db import fetchone_dict, fetchall_dict 
 
def dre_simples_tx(cur, filial: str, de: date | None, ate: date | None): 
    filtros = ["C5_FILIAL=?", "(D_E_L_E_T_ IS NULL OR D_E_L_E_T_ <> '*')"] 
    params = [filial] 
    if de: 
        filtros.append("C5_DATA >= ?") 
        params.append(de) 
    if ate: 
        filtros.append("C5_DATA < DATEADD(DAY, 1, ?)") 
        params.append(ate) 
    where_sql = " AND ".join(filtros) 
 
    # Receita + impostos (SC5) 
    cur.execute(f""" 
        SELECT 
          COALESCE(SUM(C5_VALOR_TOTAL),0) AS receita, 
          COALESCE(SUM(C5_ICMS),0) AS icms, 
          COALESCE(SUM(C5_IPI),0)  AS ipi 
        FROM dbo.SC5_PEDIDOS 
        WHERE {where_sql} AND C5_STATUS='FATURADO' 
    """, tuple(params)) 
    r = fetchone_dict(cur) or {"receita": 0, "icms": 0, "ipi": 0} 

    # Impostos adicionais (SF2)
    cur.execute(
        f"""
        SELECT
          COALESCE(SUM(f2.F2_PIS),0) AS pis,
          COALESCE(SUM(f2.F2_COFINS),0) AS cofins,
          COALESCE(SUM(f2.F2_ICMS_ST),0) AS icms_st,
          COALESCE(SUM(f2.F2_DIFAL),0) AS difal
        FROM dbo.SF2_NOTAS f2
        WHERE f2.F2_FILIAL=? 
          AND (f2.D_E_L_E_T_ IS NULL OR f2.D_E_L_E_T_ <> '*')
          AND f2.F2_STATUS='EMITIDA'
          AND (f2.F2_EMISSAO >= COALESCE(?, '19000101'))
          AND (f2.F2_EMISSAO <  DATEADD(DAY,1, COALESCE(?, '29991231')))
        """,
        (filial, de, ate),
    )
    imp = fetchone_dict(cur) or {"pis": 0, "cofins": 0, "icms_st": 0, "difal": 0}
 
    # CMV (SD3 saídas vinculadas a pedido) 
    cur.execute(f""" 
        SELECT COALESCE(SUM(D3_VALOR),0) AS cmv 
        FROM dbo.SD3_MOV 
        WHERE D3_FILIAL=? AND D3_TIPO='S' 
          AND (D_E_L_E_T_ IS NULL OR D_E_L_E_T_ <> '*') 
          AND D3_ORIGEM='RESERVA_FATURADA' 
          AND (D3_DATA >= COALESCE(?, '19000101')) 
          AND (D3_DATA <  DATEADD(DAY,1, COALESCE(?, '29991231'))) 
    """, (filial, de, ate)) 
    c = fetchone_dict(cur) or {"cmv": 0} 
 
    receita = float(r["receita"]) 
    icms = float(r["icms"]) 
    ipi = float(r["ipi"]) 
    cmv = float(c["cmv"]) 
    pis = float(imp["pis"])
    cofins = float(imp["cofins"])
    icms_st = float(imp["icms_st"])
    difal = float(imp["difal"])

    margem_bruta = receita - cmv 
    resultado = receita - cmv - icms - ipi - pis - cofins - icms_st - difal

    return { 
        "filial": filial, 
        "de": de.isoformat() if de else None, 
        "ate": ate.isoformat() if ate else None, 
        "receita": receita, 
        "cmv": cmv, 
        "margem_bruta": margem_bruta, 
        "icms": icms, 
        "ipi": ipi, 
        "pis": pis,
        "cofins": cofins,
        "icms_st": icms_st,
        "difal": difal,
        "resultado": resultado, 
    } 
 
def margem_por_produto_tx(cur, filial: str, de: date | None, ate: date | None): 
    filtros_sc5 = ["p.C5_FILIAL=?","p.C5_STATUS='FATURADO'", "(p.D_E_L_E_T_ IS NULL OR p.D_E_L_E_T_ <> '*')"] 
    params = [filial] 
    if de: 
        filtros_sc5.append("p.C5_DATA >= ?"); params.append(de) 
    if ate: 
        filtros_sc5.append("p.C5_DATA < DATEADD(DAY,1,?)"); params.append(ate) 
    where_sc5 = " AND ".join(filtros_sc5) 
 
    # Receita por produto (SC6) 
    cur.execute(f""" 
      SELECT 
        i.C6_PRODUTO AS produto, 
        SUM(i.C6_TOTAL) AS receita 
      FROM dbo.SC6_ITENS i 
      JOIN dbo.SC5_PEDIDOS p ON p.ID = i.C6_PEDIDO_ID 
      WHERE (i.D_E_L_E_T_ IS NULL OR i.D_E_L_E_T_ <> '*') 
        AND {where_sc5} 
      GROUP BY i.C6_PRODUTO 
      ORDER BY receita DESC 
    """, tuple(params)) 
    rec = fetchall_dict(cur) 
 
    # CMV por produto (SD3) 
    cur.execute(""" 
      SELECT D3_PRODUTO AS produto, SUM(D3_VALOR) AS cmv 
      FROM dbo.SD3_MOV 
      WHERE D3_FILIAL=? AND D3_TIPO='S' AND D3_ORIGEM='RESERVA_FATURADA' 
        AND (D_E_L_E_T_ IS NULL OR D_E_L_E_T_ <> '*') 
        AND (D3_DATA >= COALESCE(?, '19000101')) 
        AND (D3_DATA <  DATEADD(DAY,1, COALESCE(?, '29991231'))) 
      GROUP BY D3_PRODUTO 
    """, (filial, de, ate)) 
    cmv = {row["produto"]: float(row["cmv"]) for row in fetchall_dict(cur)} 
 
    out = [] 
    for r in rec: 
        prod = r["produto"] 
        receita = float(r["receita"]) 
        custo = float(cmv.get(prod, 0)) 
        out.append({ 
            "produto": prod, 
            "receita": receita, 
            "cmv": custo, 
            "margem": receita - custo 
        }) 
    return out


def conciliacao_nf_financeiro_tx(
    cur,
    filial: str,
    de: date | None,
    ate: date | None,
    tolerancia: float = 0.01,
    limit: int = 200,
):
    filtros_nf = ["f2.F2_FILIAL=?", "(f2.D_E_L_E_T_ IS NULL OR f2.D_E_L_E_T_ <> '*')"]
    params_nf: list = [filial]
    if de:
        filtros_nf.append("f2.F2_EMISSAO >= ?")
        params_nf.append(de)
    if ate:
        filtros_nf.append("f2.F2_EMISSAO < DATEADD(DAY,1,?)")
        params_nf.append(ate)
    where_nf = " AND ".join(filtros_nf)

    # NF sem AR
    cur.execute(
        f"""
        SELECT TOP ({int(limit)})
          'NF_SEM_AR' AS issue,
          f2.ID AS nf_id, f2.F2_DOC AS nf_doc, f2.F2_SERIE AS nf_serie,
          f2.F2_STATUS AS nf_status, f2.F2_VALOR AS nf_valor, f2.F2_EMISSAO AS nf_emissao,
          NULL AS ar_id, NULL AS ar_num, NULL AS ar_serie, NULL AS ar_status, NULL AS ar_valor, NULL AS ar_venc,
          'NF ativa sem título AR' AS info
        FROM dbo.SF2_NOTAS f2
        LEFT JOIN dbo.SE1_AR e1
          ON TRY_CAST(e1.E1_REF AS INT) = f2.ID
         AND (e1.D_E_L_E_T_ IS NULL OR e1.D_E_L_E_T_ <> '*')
        WHERE {where_nf}
          AND f2.F2_STATUS <> 'CANCELADA'
          AND e1.ID IS NULL
        ORDER BY f2.ID DESC
        """,
        tuple(params_nf),
    )
    nf_sem_ar = fetchall_dict(cur)

    # AR sem NF
    filtros_ar = ["e1.E1_FILIAL=?", "(e1.D_E_L_E_T_ IS NULL OR e1.D_E_L_E_T_ <> '*')"]
    params_ar: list = [filial]
    if de:
        filtros_ar.append("e1.E1_DATA >= ?")
        params_ar.append(de)
    if ate:
        filtros_ar.append("e1.E1_DATA < DATEADD(DAY,1,?)")
        params_ar.append(ate)
    where_ar = " AND ".join(filtros_ar)

    cur.execute(
        f"""
        SELECT TOP ({int(limit)})
          'AR_SEM_NF' AS issue,
          NULL AS nf_id, NULL AS nf_doc, NULL AS nf_serie, NULL AS nf_status, NULL AS nf_valor, NULL AS nf_emissao,
          e1.ID AS ar_id, e1.E1_NUM AS ar_num, e1.E1_SERIE AS ar_serie,
          e1.E1_STATUS AS ar_status, e1.E1_VALOR AS ar_valor, e1.E1_VENC AS ar_venc,
          'Título AR sem NF vinculada' AS info
        FROM dbo.SE1_AR e1
        LEFT JOIN dbo.SF2_NOTAS f2 ON f2.ID = TRY_CAST(e1.E1_REF AS INT)
         AND (f2.D_E_L_E_T_ IS NULL OR f2.D_E_L_E_T_ <> '*')
        WHERE {where_ar}
          AND f2.ID IS NULL
        ORDER BY e1.ID DESC
        """,
        tuple(params_ar),
    )
    ar_sem_nf = fetchall_dict(cur)

    # Divergência de valores
    cur.execute(
        f"""
        SELECT TOP ({int(limit)})
          'VALOR_DIVERGENTE' AS issue,
          f2.ID AS nf_id, f2.F2_DOC AS nf_doc, f2.F2_SERIE AS nf_serie,
          f2.F2_STATUS AS nf_status, f2.F2_VALOR AS nf_valor, f2.F2_EMISSAO AS nf_emissao,
          e1.ID AS ar_id, e1.E1_NUM AS ar_num, e1.E1_SERIE AS ar_serie,
          e1.E1_STATUS AS ar_status, e1.E1_VALOR AS ar_valor, e1.E1_VENC AS ar_venc,
          'AR x NF com valor diferente' AS info
        FROM dbo.SF2_NOTAS f2
        JOIN dbo.SE1_AR e1
          ON TRY_CAST(e1.E1_REF AS INT) = f2.ID
         AND (e1.D_E_L_E_T_ IS NULL OR e1.D_E_L_E_T_ <> '*')
        WHERE {where_nf}
          AND ABS(COALESCE(e1.E1_VALOR,0) - COALESCE(f2.F2_VALOR,0)) > ?
        ORDER BY f2.ID DESC
        """,
        tuple(params_nf + [float(tolerancia)]),
    )
    valor_div = fetchall_dict(cur)

    # NF cancelada com AR aberto/baixado
    cur.execute(
        f"""
        SELECT TOP ({int(limit)})
          CASE WHEN e1.E1_STATUS='BAIXADO' THEN 'NF_CANCELADA_AR_BAIXADO' ELSE 'NF_CANCELADA_AR_ABERTO' END AS issue,
          f2.ID AS nf_id, f2.F2_DOC AS nf_doc, f2.F2_SERIE AS nf_serie,
          f2.F2_STATUS AS nf_status, f2.F2_VALOR AS nf_valor, f2.F2_EMISSAO AS nf_emissao,
          e1.ID AS ar_id, e1.E1_NUM AS ar_num, e1.E1_SERIE AS ar_serie,
          e1.E1_STATUS AS ar_status, e1.E1_VALOR AS ar_valor, e1.E1_VENC AS ar_venc,
          'NF cancelada com AR ativo' AS info
        FROM dbo.SF2_NOTAS f2
        JOIN dbo.SE1_AR e1
          ON TRY_CAST(e1.E1_REF AS INT) = f2.ID
         AND (e1.D_E_L_E_T_ IS NULL OR e1.D_E_L_E_T_ <> '*')
        WHERE {where_nf}
          AND f2.F2_STATUS = 'CANCELADA'
          AND e1.E1_STATUS IN ('ABERTO','BAIXADO')
        ORDER BY f2.ID DESC
        """,
        tuple(params_nf),
    )
    nf_cancel_ar = fetchall_dict(cur)

    return {
        "nf_sem_ar": nf_sem_ar,
        "ar_sem_nf": ar_sem_nf,
        "valor_divergente": valor_div,
        "nf_cancelada_ar": nf_cancel_ar,
    }


def consistencia_fiscal_tx(
    cur,
    filial: str,
    de: date | None,
    ate: date | None,
    limit: int = 200,
):
    filtros_nf = ["f2.F2_FILIAL=?", "(f2.D_E_L_E_T_ IS NULL OR f2.D_E_L_E_T_ <> '*')"]
    params_nf: list = [filial]
    if de:
        filtros_nf.append("f2.F2_EMISSAO >= ?")
        params_nf.append(de)
    if ate:
        filtros_nf.append("f2.F2_EMISSAO < DATEADD(DAY,1,?)")
        params_nf.append(ate)
    where_nf = " AND ".join(filtros_nf)

    # NF sem itens SD2
    cur.execute(
        f"""
        SELECT TOP ({int(limit)})
          'NF_SEM_SD2' AS issue,
          f2.ID AS nf_id, f2.F2_DOC AS nf_doc, f2.F2_SERIE AS nf_serie,
          f2.F2_STATUS AS nf_status, f2.F2_EMISSAO AS nf_emissao
        FROM dbo.SF2_NOTAS f2
        LEFT JOIN dbo.SD2_ITENS d2
          ON d2.D2_NF_ID = f2.ID
         AND (d2.D_E_L_E_T_ IS NULL OR d2.D_E_L_E_T_ <> '*')
        WHERE {where_nf}
          AND d2.ID IS NULL
        ORDER BY f2.ID DESC
        """,
        tuple(params_nf),
    )
    nf_sem_sd2 = fetchall_dict(cur)

    # SD2 sem NF
    cur.execute(
        f"""
        SELECT TOP ({int(limit)})
          'SD2_SEM_NF' AS issue,
          d2.ID AS sd2_id, d2.D2_NF_ID AS nf_id, d2.D2_DOC AS nf_doc, d2.D2_SERIE AS nf_serie,
          d2.D2_PRODUTO AS produto, d2.D2_QTD AS qtd
        FROM dbo.SD2_ITENS d2
        LEFT JOIN dbo.SF2_NOTAS f2 ON f2.ID = d2.D2_NF_ID
         AND (f2.D_E_L_E_T_ IS NULL OR f2.D_E_L_E_T_ <> '*')
        WHERE (d2.D_E_L_E_T_ IS NULL OR d2.D_E_L_E_T_ <> '*')
          AND f2.ID IS NULL
        ORDER BY d2.ID DESC
        """,
        tuple(),
    )
    sd2_sem_nf = fetchall_dict(cur)

    # NF cancelada com SD2 ativo
    cur.execute(
        f"""
        SELECT TOP ({int(limit)})
          'NF_CANCELADA_SD2_ATIVO' AS issue,
          f2.ID AS nf_id, f2.F2_DOC AS nf_doc, f2.F2_SERIE AS nf_serie,
          f2.F2_STATUS AS nf_status, f2.F2_EMISSAO AS nf_emissao,
          d2.ID AS sd2_id, d2.D2_PRODUTO AS produto
        FROM dbo.SF2_NOTAS f2
        JOIN dbo.SD2_ITENS d2 ON d2.D2_NF_ID = f2.ID
         AND (d2.D_E_L_E_T_ IS NULL OR d2.D_E_L_E_T_ <> '*')
        WHERE {where_nf}
          AND f2.F2_STATUS = 'CANCELADA'
          AND (d2.D2_STATUS IS NULL OR d2.D2_STATUS <> 'CANCELADO')
        ORDER BY f2.ID DESC
        """,
        tuple(params_nf),
    )
    nf_cancel_sd2 = fetchall_dict(cur)

    return {
        "nf_sem_sd2": nf_sem_sd2,
        "sd2_sem_nf": sd2_sem_nf,
        "nf_cancelada_sd2": nf_cancel_sd2,
    }
