-- Passo 1/2 (complemento)
-- Backfill C6_ITEM por pedido e D2_ITEM_NUM por NF
-- Idempotente (recalcula apenas NULL)

SET NOCOUNT ON;
GO

-- Garantir colunas (evita erro de compilação)
IF NOT EXISTS (
    SELECT 1 FROM sys.columns
    WHERE object_id = OBJECT_ID('dbo.SC6_ITENS') AND name = 'C6_ITEM'
)
BEGIN
    ALTER TABLE dbo.SC6_ITENS ADD C6_ITEM INT NULL;
END

IF NOT EXISTS (
    SELECT 1 FROM sys.columns
    WHERE object_id = OBJECT_ID('dbo.SD2_ITENS') AND name = 'D2_ITEM_NUM'
)
BEGIN
    ALTER TABLE dbo.SD2_ITENS ADD D2_ITEM_NUM CHAR(4) NULL;
END
GO

-- 1) C6_ITEM: numeração sequencial por pedido (1..n)
IF EXISTS (
    SELECT 1 FROM sys.columns
    WHERE object_id = OBJECT_ID('dbo.SC6_ITENS') AND name = 'C6_ITEM'
)
BEGIN
    EXEC('
    ;WITH ItensOrdenados AS (
        SELECT
            ID,
            C6_PEDIDO_ID,
            ROW_NUMBER() OVER (PARTITION BY C6_PEDIDO_ID ORDER BY ID ASC) AS rn
        FROM dbo.SC6_ITENS
        WHERE C6_ITEM IS NULL
    )
    UPDATE i
    SET C6_ITEM = rn
    FROM ItensOrdenados i;
    ');
END

-- 2) D2_ITEM_NUM: 0001, 0002... por NF
IF EXISTS (
    SELECT 1 FROM sys.columns
    WHERE object_id = OBJECT_ID('dbo.SD2_ITENS') AND name = 'D2_ITEM_NUM'
)
BEGIN
    EXEC('
    ;WITH ItensNF AS (
        SELECT
            ID,
            D2_NF_ID,
            ROW_NUMBER() OVER (PARTITION BY D2_NF_ID ORDER BY ID ASC) AS rn
        FROM dbo.SD2_ITENS
        WHERE D2_ITEM_NUM IS NULL
    )
    UPDATE d
    SET D2_ITEM_NUM = RIGHT(''0000'' + CAST(rn AS VARCHAR(4)), 4)
    FROM ItensNF d;
    ');
END
