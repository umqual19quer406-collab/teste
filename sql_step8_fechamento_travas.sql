-- Bloco 8 - Travar lançamentos por fechamento (estoque + financeiro)
-- Trigger simples para bloquear SD3 e SE5 em período fechado

-- Função auxiliar: verifica período fechado
IF OBJECT_ID('dbo.fn_periodo_fechado', 'FN') IS NOT NULL
    DROP FUNCTION dbo.fn_periodo_fechado;
GO
CREATE FUNCTION dbo.fn_periodo_fechado (@filial NVARCHAR(10), @data DATE)
RETURNS BIT
AS
BEGIN
    DECLARE @fechado BIT = 0;
    SELECT TOP 1 @fechado = F7_FECHADO
    FROM dbo.SF7_FECHAMENTO
    WHERE F7_FILIAL=@filial
      AND F7_ANO=YEAR(@data)
      AND F7_MES=MONTH(@data)
      AND (D_E_L_E_T_ IS NULL OR D_E_L_E_T_ <> '*');
    RETURN ISNULL(@fechado, 0);
END
GO

-- SD3_MOV: bloqueia inserção em período fechado
IF OBJECT_ID('dbo.TR_SD3_BLOQ_FECH', 'TR') IS NOT NULL
    DROP TRIGGER dbo.TR_SD3_BLOQ_FECH;
GO
CREATE TRIGGER dbo.TR_SD3_BLOQ_FECH
ON dbo.SD3_MOV
AFTER INSERT
AS
BEGIN
    SET NOCOUNT ON;
    IF EXISTS (
        SELECT 1
        FROM inserted i
        WHERE dbo.fn_periodo_fechado(i.D3_FILIAL, CAST(i.D3_DATA AS DATE)) = 1
    )
    BEGIN
        RAISERROR('Período fechado: bloqueado lançamento de estoque (SD3).', 16, 1);
        ROLLBACK TRANSACTION;
    END
END
GO

-- SE5_MOV: bloqueia inserção em período fechado (caixa)
IF OBJECT_ID('dbo.TR_SE5_BLOQ_FECH', 'TR') IS NOT NULL
    DROP TRIGGER dbo.TR_SE5_BLOQ_FECH;
GO
CREATE TRIGGER dbo.TR_SE5_BLOQ_FECH
ON dbo.SE5_MOV
AFTER INSERT
AS
BEGIN
    SET NOCOUNT ON;
    IF EXISTS (
        SELECT 1
        FROM inserted i
        WHERE dbo.fn_periodo_fechado(i.E5_FILIAL, CAST(i.E5_DATA AS DATE)) = 1
    )
    BEGIN
        RAISERROR('Período fechado: bloqueado lançamento financeiro (SE5).', 16, 1);
        ROLLBACK TRANSACTION;
    END
END
GO
