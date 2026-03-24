-- Bloco 4.1 - Índices e chaves únicas críticas (Protheus-like)
-- Execute no banco ERP_PROTHEUS

-- NF (SF2): doc/serie por filial
IF NOT EXISTS (
    SELECT 1 FROM sys.indexes
    WHERE name = 'UX_SF2_FILIAL_DOC_SERIE'
      AND object_id = OBJECT_ID('dbo.SF2_NOTAS')
)
BEGIN
    CREATE UNIQUE INDEX UX_SF2_FILIAL_DOC_SERIE
    ON dbo.SF2_NOTAS (F2_FILIAL, F2_DOC, F2_SERIE)
    WHERE D_E_L_E_T_ IS NULL;
END

-- AR (SE1): num/serie por filial
IF NOT EXISTS (
    SELECT 1 FROM sys.indexes
    WHERE name = 'UX_SE1_FILIAL_NUM_SERIE'
      AND object_id = OBJECT_ID('dbo.SE1_AR')
)
BEGIN
    CREATE UNIQUE INDEX UX_SE1_FILIAL_NUM_SERIE
    ON dbo.SE1_AR (E1_FILIAL, E1_NUM, E1_SERIE)
    WHERE D_E_L_E_T_ IS NULL;
END

-- AP (SF1): num/serie por filial
IF NOT EXISTS (
    SELECT 1 FROM sys.indexes
    WHERE name = 'UX_SF1_FILIAL_NUM_SERIE'
      AND object_id = OBJECT_ID('dbo.SF1_AP')
)
BEGIN
    CREATE UNIQUE INDEX UX_SF1_FILIAL_NUM_SERIE
    ON dbo.SF1_AP (F1_FILIAL, F1_NUM, F1_SERIE)
    WHERE D_E_L_E_T_ IS NULL;
END

-- Índices de status/data
IF NOT EXISTS (
    SELECT 1 FROM sys.indexes
    WHERE name = 'IX_SF2_STATUS_EMISSAO'
      AND object_id = OBJECT_ID('dbo.SF2_NOTAS')
)
BEGIN
    CREATE INDEX IX_SF2_STATUS_EMISSAO
    ON dbo.SF2_NOTAS (F2_STATUS, F2_EMISSAO, F2_FILIAL);
END

IF NOT EXISTS (
    SELECT 1 FROM sys.indexes
    WHERE name = 'IX_SE1_STATUS_DATA'
      AND object_id = OBJECT_ID('dbo.SE1_AR')
)
BEGIN
    CREATE INDEX IX_SE1_STATUS_DATA
    ON dbo.SE1_AR (E1_STATUS, E1_DATA, E1_FILIAL);
END

IF NOT EXISTS (
    SELECT 1 FROM sys.indexes
    WHERE name = 'IX_SF1_STATUS_DATA'
      AND object_id = OBJECT_ID('dbo.SF1_AP')
)
BEGIN
    CREATE INDEX IX_SF1_STATUS_DATA
    ON dbo.SF1_AP (F1_STATUS, F1_DATA, F1_FILIAL);
END
