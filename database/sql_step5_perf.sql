-- Bloco 5.1 - Performance (índices adicionais)

-- SC6: pedido + produto
IF NOT EXISTS (
    SELECT 1 FROM sys.indexes
    WHERE name = 'IX_SC6_PEDIDO_PRODUTO'
      AND object_id = OBJECT_ID('dbo.SC6_ITENS')
)
BEGIN
    CREATE INDEX IX_SC6_PEDIDO_PRODUTO
    ON dbo.SC6_ITENS (C6_PEDIDO_ID, C6_PRODUTO);
END

-- SD2: NF + produto
IF NOT EXISTS (
    SELECT 1 FROM sys.indexes
    WHERE name = 'IX_SD2_NF_PRODUTO'
      AND object_id = OBJECT_ID('dbo.SD2_ITENS')
)
BEGIN
    CREATE INDEX IX_SD2_NF_PRODUTO
    ON dbo.SD2_ITENS (D2_NF_ID, D2_PRODUTO);
END

-- SC9: pedido + item
IF NOT EXISTS (
    SELECT 1 FROM sys.indexes
    WHERE name = 'IX_SC9_PEDIDO_ITEM'
      AND object_id = OBJECT_ID('dbo.SC9_LIBERACAO')
)
BEGIN
    CREATE INDEX IX_SC9_PEDIDO_ITEM
    ON dbo.SC9_LIBERACAO (C9_PEDIDO_ID, C9_ITEM);
END

-- SD3: produto + data
IF NOT EXISTS (
    SELECT 1 FROM sys.indexes
    WHERE name = 'IX_SD3_PRODUTO_DATA'
      AND object_id = OBJECT_ID('dbo.SD3_MOV')
)
BEGIN
    CREATE INDEX IX_SD3_PRODUTO_DATA
    ON dbo.SD3_MOV (D3_PRODUTO, D3_DATA, D3_FILIAL);
END

-- LOGS: usuario + data
IF NOT EXISTS (
    SELECT 1 FROM sys.indexes
    WHERE name = 'IX_LOGS_USUARIO_DATA'
      AND object_id = OBJECT_ID('dbo.LOGS')
)
BEGIN
    CREATE INDEX IX_LOGS_USUARIO_DATA
    ON dbo.LOGS (L_USUARIO, L_DATA);
END
