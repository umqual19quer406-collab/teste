-- Bloco 8 (ext) - Travar lançamentos por fechamento (NF/AR/AP)
USE ERP_PROTHEUS;
GO

-- SF2_NOTAS: bloqueia INSERT/UPDATE em período fechado
IF OBJECT_ID('dbo.SF2_NOTAS', 'U') IS NOT NULL
BEGIN
    IF OBJECT_ID('dbo.TR_SF2_BLOQ_FECH', 'TR') IS NOT NULL
        DROP TRIGGER dbo.TR_SF2_BLOQ_FECH;
    EXEC('
    CREATE TRIGGER dbo.TR_SF2_BLOQ_FECH
    ON dbo.SF2_NOTAS
    AFTER INSERT, UPDATE
    AS
    BEGIN
        SET NOCOUNT ON;
        IF EXISTS (
            SELECT 1
            FROM inserted i
            WHERE dbo.fn_periodo_fechado(i.F2_FILIAL, CAST(i.F2_EMISSAO AS DATE)) = 1
        )
        BEGIN
            RAISERROR(''Período fechado: bloqueada emissão/alteração de NF (SF2).'',
16, 1);
            ROLLBACK TRANSACTION;
        END
    END
    ');
END
GO

-- SD2_ITENS: bloqueia INSERT/UPDATE em período fechado (usa data da NF)
IF OBJECT_ID('dbo.SD2_ITENS', 'U') IS NOT NULL
BEGIN
    IF OBJECT_ID('dbo.TR_SD2_BLOQ_FECH', 'TR') IS NOT NULL
        DROP TRIGGER dbo.TR_SD2_BLOQ_FECH;
    EXEC('
    CREATE TRIGGER dbo.TR_SD2_BLOQ_FECH
    ON dbo.SD2_ITENS
    AFTER INSERT, UPDATE
    AS
    BEGIN
        SET NOCOUNT ON;
        IF EXISTS (
            SELECT 1
            FROM inserted i
            JOIN dbo.SF2_NOTAS f2 ON f2.ID = i.D2_NF_ID
            WHERE dbo.fn_periodo_fechado(f2.F2_FILIAL, CAST(f2.F2_EMISSAO AS DATE)) = 1
        )
        BEGIN
            RAISERROR(''Período fechado: bloqueada alteração de itens NF (SD2).'', 16, 1);
            ROLLBACK TRANSACTION;
        END
    END
    ');
END
GO

-- SE1_AR: bloqueia INSERT/UPDATE em período fechado
IF OBJECT_ID('dbo.SE1_AR', 'U') IS NOT NULL
BEGIN
    IF OBJECT_ID('dbo.TR_SE1_BLOQ_FECH', 'TR') IS NOT NULL
        DROP TRIGGER dbo.TR_SE1_BLOQ_FECH;
    EXEC('
    CREATE TRIGGER dbo.TR_SE1_BLOQ_FECH
    ON dbo.SE1_AR
    AFTER INSERT, UPDATE
    AS
    BEGIN
        SET NOCOUNT ON;
        IF EXISTS (
            SELECT 1
            FROM inserted i
            WHERE dbo.fn_periodo_fechado(i.E1_FILIAL, CAST(i.E1_DATA AS DATE)) = 1
        )
        BEGIN
            RAISERROR(''Período fechado: bloqueado lançamento AR (SE1).'', 16, 1);
            ROLLBACK TRANSACTION;
        END
    END
    ');
END
GO

-- SF1_AP: bloqueia INSERT/UPDATE em período fechado
IF OBJECT_ID('dbo.SF1_AP', 'U') IS NOT NULL
BEGIN
    IF OBJECT_ID('dbo.TR_SF1_BLOQ_FECH', 'TR') IS NOT NULL
        DROP TRIGGER dbo.TR_SF1_BLOQ_FECH;
    EXEC('
    CREATE TRIGGER dbo.TR_SF1_BLOQ_FECH
    ON dbo.SF1_AP
    AFTER INSERT, UPDATE
    AS
    BEGIN
        SET NOCOUNT ON;
        IF EXISTS (
            SELECT 1
            FROM inserted i
            WHERE dbo.fn_periodo_fechado(i.F1_FILIAL, CAST(i.F1_DATA AS DATE)) = 1
        )
        BEGIN
            RAISERROR(''Período fechado: bloqueado lançamento AP (SF1).'', 16, 1);
            ROLLBACK TRANSACTION;
        END
    END
    ');
END
GO
