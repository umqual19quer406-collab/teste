-- Bloco 6.3 - Correções automáticas (consistência)
-- Execute no ERP_PROTHEUS. Script conservador (não mexe em AR baixado).

SET NOCOUNT ON;

-- 1) Preencher C6_ITEM faltante (por pedido) - dinâmico
EXEC('
;WITH ItensOrdenados AS (
    SELECT ID, C6_PEDIDO_ID,
           ROW_NUMBER() OVER (PARTITION BY C6_PEDIDO_ID ORDER BY ID ASC) AS rn
    FROM dbo.SC6_ITENS
    WHERE C6_ITEM IS NULL
)
UPDATE i SET C6_ITEM = rn
FROM ItensOrdenados i;
');

-- 2) Preencher D2_ITEM_NUM faltante (por NF) - dinâmico
EXEC('
;WITH ItensNF AS (
    SELECT ID, D2_NF_ID,
           ROW_NUMBER() OVER (PARTITION BY D2_NF_ID ORDER BY ID ASC) AS rn
    FROM dbo.SD2_ITENS
    WHERE D2_ITEM_NUM IS NULL
)
UPDATE d
SET D2_ITEM_NUM = RIGHT(''0000'' + CAST(rn AS VARCHAR(4)), 4)
FROM ItensNF d;
');

-- 3) Se NF cancelada, marca SD2 como cancelado (somente ativos)
UPDATE d
SET d.D2_STATUS='CANCELADO',
    d.D2_DATA_CANCEL=COALESCE(d.D2_DATA_CANCEL, SYSDATETIME()),
    d.D2_MOTIVO_CANCEL=COALESCE(d.D2_MOTIVO_CANCEL, 'AUTO: NF cancelada'),
    d.D_E_L_E_T_='*',
    d.R_E_C_D_E_L_=COALESCE(d.R_E_C_D_E_L_, d.R_E_C_N_O_)
FROM dbo.SD2_ITENS d
JOIN dbo.SF2_NOTAS f2 ON f2.ID = d.D2_NF_ID
WHERE f2.F2_STATUS='CANCELADA'
  AND (d.D2_STATUS IS NULL OR d.D2_STATUS <> 'CANCELADO');

-- 4) Se NF cancelada, cancela AR aberto vinculado (não mexe em BAIXADO)
UPDATE e1
SET e1.E1_STATUS='CANCELADO',
    e1.D_E_L_E_T_='*',
    e1.R_E_C_D_E_L_=COALESCE(e1.R_E_C_D_E_L_, e1.R_E_C_N_O_)
FROM dbo.SE1_AR e1
JOIN dbo.SF2_NOTAS f2 ON f2.ID = TRY_CAST(e1.E1_REF AS INT)
WHERE f2.F2_STATUS='CANCELADA'
  AND e1.E1_STATUS='ABERTO';

-- 5) Se pedido cancelado, cancela liberações SC9
UPDATE s
SET s.C9_STATUS='CANCELADO',
    s.C9_DATA_CANCEL=COALESCE(s.C9_DATA_CANCEL, SYSDATETIME()),
    s.D_E_L_E_T_='*',
    s.R_E_C_D_E_L_=COALESCE(s.R_E_C_D_E_L_, s.R_E_C_N_O_)
FROM dbo.SC9_LIBERACAO s
JOIN dbo.SC5_PEDIDOS p ON p.ID = s.C9_PEDIDO_ID
WHERE p.C5_STATUS='CANCELADO'
  AND (s.C9_STATUS IS NULL OR s.C9_STATUS <> 'CANCELADO');
