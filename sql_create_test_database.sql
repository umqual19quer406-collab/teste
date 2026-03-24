/*
Cria uma base separada para testes de integração, sem tocar na base atual.

Uso no SSMS:
1) Ajuste @source_db e @test_db.
2) Execute conectado na instância SQL Server.
3) Depois aponte TEST_DB_CONN_STR para @test_db.
4) Rode: python tests/init_integration_db.py

Observações:
- Este script NÃO altera a base de origem.
- Ele só cria a base de testes se ela ainda não existir.
- A base criada nasce vazia; o schema mínimo usado pelos testes é inicializado
  pelo script Python tests/init_integration_db.py.
*/

SET NOCOUNT ON;

DECLARE @source_db sysname = N'ERP_PROTHEUS';
DECLARE @test_db   sysname = N'ERP_PROTHEUS_TEST';

IF DB_ID(@source_db) IS NULL
BEGIN
    RAISERROR('Base de origem não encontrada: %s', 16, 1, @source_db);
    RETURN;
END;

IF DB_ID(@test_db) IS NOT NULL
BEGIN
    PRINT 'Base de testes já existe: ' + @test_db;
    RETURN;
END;

DECLARE @data_path nvarchar(4000);
DECLARE @log_path nvarchar(4000);

SELECT TOP 1
    @data_path = LEFT(physical_name, LEN(physical_name) - CHARINDEX('\', REVERSE(physical_name))) + '\'
FROM sys.master_files
WHERE database_id = DB_ID(@source_db)
  AND type = 0
ORDER BY file_id;

SELECT TOP 1
    @log_path = LEFT(physical_name, LEN(physical_name) - CHARINDEX('\', REVERSE(physical_name))) + '\'
FROM sys.master_files
WHERE database_id = DB_ID(@source_db)
  AND type = 1
ORDER BY file_id;

IF @data_path IS NULL OR @log_path IS NULL
BEGIN
    RAISERROR('Não foi possível resolver os caminhos físicos da base de origem.', 16, 1);
    RETURN;
END;

DECLARE @sql nvarchar(max) = N'
CREATE DATABASE [' + REPLACE(@test_db, N']', N']]') + N']
ON PRIMARY
(
    NAME = N''' + REPLACE(@test_db, N'''', N'''''') + N'_data'',
    FILENAME = N''' + REPLACE(@data_path, N'''', N'''''') + REPLACE(@test_db, N'''', N'''''') + N'.mdf'',
    SIZE = 128MB,
    FILEGROWTH = 64MB
)
LOG ON
(
    NAME = N''' + REPLACE(@test_db, N'''', N'''''') + N'_log'',
    FILENAME = N''' + REPLACE(@log_path, N'''', N'''''') + REPLACE(@test_db, N'''', N'''''') + N'_log.ldf'',
    SIZE = 64MB,
    FILEGROWTH = 64MB
);';

EXEC sp_executesql @sql;

PRINT 'Base de testes criada com sucesso: ' + @test_db;
PRINT 'Próximo passo: apontar TEST_DB_CONN_STR para essa base e rodar tests/init_integration_db.py';
