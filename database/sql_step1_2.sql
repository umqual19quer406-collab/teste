-- Patch 1 e 2 (Protheus-like)
-- 1) Garantir colunas de cancelamento/soft delete (D_E_L_E_T_, R_E_C_N_O_, R_E_C_D_E_L_)
-- 2) Criar sequences RECNO e preencher R_E_C_N_O_ onde estiver NULL
-- Observação: script idempotente (pode rodar mais de uma vez).

SET NOCOUNT ON;

DECLARE @tables TABLE (name sysname);
INSERT INTO @tables (name)
VALUES
 ('SC5_PEDIDOS'),
 ('SC6_ITENS'),
 ('SF2_NOTAS'),
 ('SD2_ITENS'),
 ('SE1_AR'),
 ('SF1_AP'),
 ('SD3_MOV'),
 ('SB1_PRODUTOS'),
 ('SA1_CLIENTES'),
 ('SA2_FORNECEDORES'),
 ('SE5_CONTAS'),
 ('SE5_CATEG'),
 ('SE5_MOV'),
 ('SZ0_RESERVA');

DECLARE @t sysname;
DECLARE table_cursor CURSOR FOR SELECT name FROM @tables;
OPEN table_cursor;
FETCH NEXT FROM table_cursor INTO @t;

WHILE @@FETCH_STATUS = 0
BEGIN
    -- D_E_L_E_T_
    IF COL_LENGTH('dbo.' + @t, 'D_E_L_E_T_') IS NULL
    BEGIN
        EXEC('ALTER TABLE dbo.' + @t + ' ADD D_E_L_E_T_ CHAR(1) NULL');
    END

    -- R_E_C_N_O_
    IF COL_LENGTH('dbo.' + @t, 'R_E_C_N_O_') IS NULL
    BEGIN
        EXEC('ALTER TABLE dbo.' + @t + ' ADD R_E_C_N_O_ INT NULL');
    END

    -- R_E_C_D_E_L_
    IF COL_LENGTH('dbo.' + @t, 'R_E_C_D_E_L_') IS NULL
    BEGIN
        EXEC('ALTER TABLE dbo.' + @t + ' ADD R_E_C_D_E_L_ INT NULL');
    END

    -- Sequence RECNO por tabela
    DECLARE @seq sysname = 'SEQ_' + @t + '_RECNO';
    IF OBJECT_ID('dbo.' + @seq, 'SO') IS NULL
    BEGIN
        EXEC('CREATE SEQUENCE dbo.' + @seq + ' AS INT START WITH 1 INCREMENT BY 1');
    END

    -- Preenche R_E_C_N_O_ faltante
    EXEC('UPDATE dbo.' + @t + ' SET R_E_C_N_O_ = NEXT VALUE FOR dbo.' + @seq + ' WHERE R_E_C_N_O_ IS NULL');

    FETCH NEXT FROM table_cursor INTO @t;
END

CLOSE table_cursor;
DEALLOCATE table_cursor;

-- Campos de cancelamento mínimos (SD2/SF2)
IF COL_LENGTH('dbo.SD2_ITENS', 'D2_STATUS') IS NULL
    ALTER TABLE dbo.SD2_ITENS ADD D2_STATUS NVARCHAR(20) NULL;
IF COL_LENGTH('dbo.SD2_ITENS', 'D2_DATA_CANCEL') IS NULL
    ALTER TABLE dbo.SD2_ITENS ADD D2_DATA_CANCEL DATETIME2(0) NULL;
IF COL_LENGTH('dbo.SD2_ITENS', 'D2_USUARIO_CANCEL') IS NULL
    ALTER TABLE dbo.SD2_ITENS ADD D2_USUARIO_CANCEL NVARCHAR(50) NULL;
IF COL_LENGTH('dbo.SD2_ITENS', 'D2_MOTIVO_CANCEL') IS NULL
    ALTER TABLE dbo.SD2_ITENS ADD D2_MOTIVO_CANCEL NVARCHAR(200) NULL;

IF COL_LENGTH('dbo.SF2_NOTAS', 'F2_STATUS') IS NULL
    ALTER TABLE dbo.SF2_NOTAS ADD F2_STATUS NVARCHAR(20) NULL;
IF COL_LENGTH('dbo.SF2_NOTAS', 'F2_DATA_CANCEL') IS NULL
    ALTER TABLE dbo.SF2_NOTAS ADD F2_DATA_CANCEL DATETIME2(0) NULL;
IF COL_LENGTH('dbo.SF2_NOTAS', 'F2_USUARIO_CANCEL') IS NULL
    ALTER TABLE dbo.SF2_NOTAS ADD F2_USUARIO_CANCEL NVARCHAR(50) NULL;
IF COL_LENGTH('dbo.SF2_NOTAS', 'F2_MOTIVO_CANCEL') IS NULL
    ALTER TABLE dbo.SF2_NOTAS ADD F2_MOTIVO_CANCEL NVARCHAR(200) NULL;

-- Ajustes de item Protheus-like
IF COL_LENGTH('dbo.SC6_ITENS', 'C6_ITEM') IS NULL
    ALTER TABLE dbo.SC6_ITENS ADD C6_ITEM INT NULL;
IF COL_LENGTH('dbo.SD2_ITENS', 'D2_ITEM_NUM') IS NULL
    ALTER TABLE dbo.SD2_ITENS ADD D2_ITEM_NUM CHAR(4) NULL;
