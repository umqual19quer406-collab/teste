from __future__ import annotations

import os
import re
import time

import pyodbc


def _require_env(name: str) -> str:
    value = os.getenv(name, "").strip()
    if not value:
        raise RuntimeError(f"Environment variable {name} is required")
    return value


def _extract_database_name(conn_str: str) -> str:
    match = re.search(r"(?:DATABASE|Initial Catalog)\s*=\s*([^;]+)", conn_str, flags=re.IGNORECASE)
    if not match:
        raise RuntimeError("Could not extract database name from TEST_DB_CONN_STR")
    return match.group(1).strip()


def _connect_with_retry(conn_str: str, attempts: int = 30, sleep_seconds: int = 2, autocommit: bool = False):
    last_error: Exception | None = None
    for _ in range(attempts):
        try:
            return pyodbc.connect(conn_str, timeout=5, autocommit=autocommit)
        except Exception as exc:  # pragma: no cover - infra bootstrap
            last_error = exc
            time.sleep(sleep_seconds)
    raise RuntimeError(f"Could not connect to SQL Server after retries: {last_error}") from last_error


SCHEMA_STATEMENTS = [
    """
    IF OBJECT_ID('dbo.USUARIOS', 'U') IS NULL
    BEGIN
        CREATE TABLE dbo.USUARIOS (
            ID INT IDENTITY(1,1) NOT NULL PRIMARY KEY,
            U_LOGIN NVARCHAR(50) NOT NULL,
            U_SENHA_HASH NVARCHAR(255) NOT NULL,
            U_PERFIL NVARCHAR(20) NOT NULL,
            D_E_L_E_T_ CHAR(1) NULL,
            R_E_C_N_O_ INT NULL,
            R_E_C_D_E_L_ INT NULL
        );
        CREATE UNIQUE INDEX UX_USUARIOS_LOGIN ON dbo.USUARIOS (U_LOGIN);
    END
    """,
    """
    IF OBJECT_ID('dbo.LOGS', 'U') IS NULL
    BEGIN
        CREATE TABLE dbo.LOGS (
            ID INT IDENTITY(1,1) NOT NULL PRIMARY KEY,
            L_USUARIO NVARCHAR(50) NOT NULL,
            L_ACAO NVARCHAR(1000) NOT NULL,
            L_DATA DATETIME2(0) NOT NULL
        );
    END
    """,
    """
    IF OBJECT_ID('dbo.SM0_EMPRESA', 'U') IS NULL
    BEGIN
        CREATE TABLE dbo.SM0_EMPRESA (
            ID INT IDENTITY(1,1) NOT NULL PRIMARY KEY,
            M0_FILIAL NVARCHAR(10) NOT NULL,
            M0_SERIE_NF NVARCHAR(10) NULL,
            M0_SERIE_AR NVARCHAR(10) NULL,
            M0_SERIE_AP NVARCHAR(10) NULL,
            D_E_L_E_T_ CHAR(1) NULL,
            R_E_C_N_O_ INT NULL,
            R_E_C_D_E_L_ INT NULL
        );
        CREATE UNIQUE INDEX UX_SM0_FILIAL ON dbo.SM0_EMPRESA (M0_FILIAL) WHERE D_E_L_E_T_ IS NULL;
    END
    """,
    """
    IF OBJECT_ID('dbo.SX5_TABELAS', 'U') IS NULL
    BEGIN
        CREATE TABLE dbo.SX5_TABELAS (
            ID INT IDENTITY(1,1) NOT NULL PRIMARY KEY,
            X5_FILIAL NVARCHAR(10) NOT NULL,
            X5_TABELA NVARCHAR(20) NOT NULL,
            X5_CHAVE NVARCHAR(30) NOT NULL,
            X5_DESCR NVARCHAR(100) NULL,
            X5_ATIVO BIT NOT NULL DEFAULT (1),
            D_E_L_E_T_ CHAR(1) NULL,
            R_E_C_N_O_ INT NULL,
            R_E_C_D_E_L_ INT NULL
        );
        CREATE UNIQUE INDEX UX_SX5_FILIAL_TABELA_CHAVE ON dbo.SX5_TABELAS (X5_FILIAL, X5_TABELA, X5_CHAVE);
    END
    """,
    """
    IF OBJECT_ID('dbo.SX6_SEQ', 'U') IS NULL
    BEGIN
        CREATE TABLE dbo.SX6_SEQ (
            ID INT IDENTITY(1,1) NOT NULL PRIMARY KEY,
            X6_FILIAL NVARCHAR(10) NOT NULL,
            X6_SERIE NVARCHAR(10) NOT NULL,
            X6_TABELA NVARCHAR(20) NOT NULL,
            X6_SEQ INT NOT NULL
        );
        CREATE UNIQUE INDEX UX_SX6_FILIAL_SERIE_TABELA ON dbo.SX6_SEQ (X6_FILIAL, X6_SERIE, X6_TABELA);
    END
    """,
    """
    IF OBJECT_ID('dbo.SA1_CLIENTES', 'U') IS NULL
    BEGIN
        CREATE TABLE dbo.SA1_CLIENTES (
            ID INT IDENTITY(1,1) NOT NULL PRIMARY KEY,
            A1_COD NVARCHAR(20) NOT NULL,
            A1_FILIAL NVARCHAR(10) NOT NULL,
            A1_NOME NVARCHAR(120) NOT NULL,
            A1_DOC NVARCHAR(30) NULL,
            A1_EMAIL NVARCHAR(120) NULL,
            A1_FONE NVARCHAR(30) NULL,
            A1_TABELA_ID INT NULL,
            A1_ATIVO BIT NOT NULL DEFAULT (1),
            D_E_L_E_T_ CHAR(1) NULL,
            R_E_C_N_O_ INT NULL,
            R_E_C_D_E_L_ INT NULL
        );
        CREATE UNIQUE INDEX UX_SA1_FILIAL_COD ON dbo.SA1_CLIENTES (A1_FILIAL, A1_COD);
    END
    """,
    """
    IF OBJECT_ID('dbo.SA2_FORNECEDORES', 'U') IS NULL
    BEGIN
        CREATE TABLE dbo.SA2_FORNECEDORES (
            ID INT IDENTITY(1,1) NOT NULL PRIMARY KEY,
            A2_COD NVARCHAR(20) NOT NULL,
            A2_FILIAL NVARCHAR(10) NOT NULL,
            A2_NOME NVARCHAR(120) NOT NULL,
            A2_DOC NVARCHAR(30) NULL,
            A2_EMAIL NVARCHAR(120) NULL,
            A2_FONE NVARCHAR(30) NULL,
            A2_ATIVO BIT NOT NULL DEFAULT (1),
            D_E_L_E_T_ CHAR(1) NULL,
            R_E_C_N_O_ INT NULL,
            R_E_C_D_E_L_ INT NULL
        );
        CREATE UNIQUE INDEX UX_SA2_FILIAL_COD ON dbo.SA2_FORNECEDORES (A2_FILIAL, A2_COD);
    END
    """,
    """
    IF OBJECT_ID('dbo.SB1_PRODUTOS', 'U') IS NULL
    BEGIN
        CREATE TABLE dbo.SB1_PRODUTOS (
            ID INT IDENTITY(1,1) NOT NULL PRIMARY KEY,
            B1_COD NVARCHAR(50) NOT NULL,
            B1_DESC NVARCHAR(120) NOT NULL,
            B1_PRECO DECIMAL(18,2) NOT NULL DEFAULT (0),
            B1_ESTOQUE INT NOT NULL DEFAULT (0),
            B1_RESERVADO INT NOT NULL DEFAULT (0),
            B1_CM DECIMAL(18,2) NOT NULL DEFAULT (0),
            B1_FILIAL NVARCHAR(10) NOT NULL,
            B1_NCM NVARCHAR(20) NULL,
            D_E_L_E_T_ CHAR(1) NULL,
            R_E_C_N_O_ INT NULL,
            R_E_C_D_E_L_ INT NULL
        );
        CREATE UNIQUE INDEX UX_SB1_FILIAL_COD ON dbo.SB1_PRODUTOS (B1_FILIAL, B1_COD);
    END
    """,
    """
    IF OBJECT_ID('dbo.PR0_TABELA', 'U') IS NULL
    BEGIN
        CREATE TABLE dbo.PR0_TABELA (
            ID INT IDENTITY(1,1) NOT NULL PRIMARY KEY,
            P0_FILIAL NVARCHAR(10) NOT NULL,
            P0_COD NVARCHAR(20) NOT NULL,
            P0_DESC NVARCHAR(120) NOT NULL,
            P0_ATIVA BIT NOT NULL DEFAULT (1),
            D_E_L_E_T_ CHAR(1) NULL,
            R_E_C_N_O_ INT NULL,
            R_E_C_D_E_L_ INT NULL
        );
        CREATE UNIQUE INDEX UX_PR0_FILIAL_COD ON dbo.PR0_TABELA (P0_FILIAL, P0_COD);
    END
    """,
    """
    IF OBJECT_ID('dbo.PR1_PRECO', 'U') IS NULL
    BEGIN
        CREATE TABLE dbo.PR1_PRECO (
            ID INT IDENTITY(1,1) NOT NULL PRIMARY KEY,
            P1_FILIAL NVARCHAR(10) NOT NULL,
            P1_TABELA_ID INT NOT NULL,
            P1_PRODUTO NVARCHAR(50) NOT NULL,
            P1_PRECO DECIMAL(18,2) NOT NULL,
            P1_DTINI DATE NOT NULL,
            P1_DTFIM DATE NULL,
            D_E_L_E_T_ CHAR(1) NULL,
            R_E_C_N_O_ INT NULL,
            R_E_C_D_E_L_ INT NULL
        );
        CREATE INDEX IX_PR1_LOOKUP ON dbo.PR1_PRECO (P1_FILIAL, P1_TABELA_ID, P1_PRODUTO, P1_DTINI);
    END
    """,
    """
    IF OBJECT_ID('dbo.SF4_FISCAL', 'U') IS NULL
    BEGIN
        CREATE TABLE dbo.SF4_FISCAL (
            ID INT IDENTITY(1,1) NOT NULL PRIMARY KEY,
            F4_FILIAL NVARCHAR(10) NOT NULL,
            F4_COD NVARCHAR(10) NOT NULL,
            F4_TIPO NVARCHAR(5) NOT NULL,
            F4_CFOP NVARCHAR(10) NOT NULL,
            F4_GERA_TIT BIT NOT NULL DEFAULT (1),
            F4_GERA_EST BIT NOT NULL DEFAULT (1),
            F4_ICMS DECIMAL(18,4) NOT NULL DEFAULT (0),
            F4_IPI DECIMAL(18,4) NOT NULL DEFAULT (0),
            F4_PIS DECIMAL(18,4) NOT NULL DEFAULT (0),
            F4_COFINS DECIMAL(18,4) NOT NULL DEFAULT (0),
            F4_ICMS_ST DECIMAL(18,4) NOT NULL DEFAULT (0),
            F4_DIFAL DECIMAL(18,4) NOT NULL DEFAULT (0),
            F4_CST_ICMS NVARCHAR(10) NULL,
            F4_CSOSN NVARCHAR(10) NULL,
            F4_CST_PIS NVARCHAR(10) NULL,
            F4_CST_COFINS NVARCHAR(10) NULL,
            F4_DESC NVARCHAR(120) NULL,
            F4_ATIVO BIT NOT NULL DEFAULT (1),
            D_E_L_E_T_ CHAR(1) NULL,
            R_E_C_N_O_ INT NULL,
            R_E_C_D_E_L_ INT NULL
        );
        CREATE UNIQUE INDEX UX_SF4_FILIAL_COD ON dbo.SF4_FISCAL (F4_FILIAL, F4_COD);
    END
    """,
    """
    IF OBJECT_ID('dbo.SF5_FISCAL_REGRAS', 'U') IS NULL
    BEGIN
        CREATE TABLE dbo.SF5_FISCAL_REGRAS (
            ID INT IDENTITY(1,1) NOT NULL PRIMARY KEY,
            F5_FILIAL NVARCHAR(10) NOT NULL,
            F5_TES NVARCHAR(10) NOT NULL,
            F5_CLIENTE_COD NVARCHAR(20) NULL,
            F5_PRODUTO NVARCHAR(50) NULL,
            F5_CFOP NVARCHAR(10) NULL,
            F5_ICMS DECIMAL(18,4) NULL,
            F5_IPI DECIMAL(18,4) NULL,
            F5_PIS DECIMAL(18,4) NULL,
            F5_COFINS DECIMAL(18,4) NULL,
            F5_ICMS_ST DECIMAL(18,4) NULL,
            F5_DIFAL DECIMAL(18,4) NULL,
            F5_CST_ICMS NVARCHAR(10) NULL,
            F5_CSOSN NVARCHAR(10) NULL,
            F5_CST_PIS NVARCHAR(10) NULL,
            F5_CST_COFINS NVARCHAR(10) NULL,
            F5_GERA_TIT BIT NULL,
            F5_GERA_EST BIT NULL,
            F5_PRIORIDADE INT NOT NULL DEFAULT (0),
            F5_ATIVO BIT NOT NULL DEFAULT (1),
            D_E_L_E_T_ CHAR(1) NULL,
            R_E_C_N_O_ INT NULL,
            R_E_C_D_E_L_ INT NULL
        );
    END
    """,
    """
    IF OBJECT_ID('dbo.SF8_FISCAL_NCM', 'U') IS NULL
    BEGIN
        CREATE TABLE dbo.SF8_FISCAL_NCM (
            ID INT IDENTITY(1,1) NOT NULL PRIMARY KEY,
            F8_FILIAL NVARCHAR(10) NOT NULL,
            F8_NCM NVARCHAR(20) NOT NULL,
            F8_CFOP NVARCHAR(10) NOT NULL,
            F8_ICMS DECIMAL(18,4) NULL,
            F8_IPI DECIMAL(18,4) NULL,
            F8_ATIVO BIT NOT NULL DEFAULT (1),
            D_E_L_E_T_ CHAR(1) NULL,
            R_E_C_N_O_ INT NULL,
            R_E_C_D_E_L_ INT NULL
        );
    END
    """,
    """
    IF OBJECT_ID('dbo.SC5_PEDIDOS', 'U') IS NULL
    BEGIN
        CREATE TABLE dbo.SC5_PEDIDOS (
            ID INT IDENTITY(1,1) NOT NULL PRIMARY KEY,
            C5_DATA DATETIME2(0) NOT NULL,
            C5_FILIAL NVARCHAR(10) NOT NULL,
            C5_NUM NVARCHAR(20) NULL,
            C5_VALOR_TOTAL DECIMAL(18,2) NOT NULL DEFAULT (0),
            C5_USUARIO NVARCHAR(50) NOT NULL,
            C5_STATUS NVARCHAR(20) NOT NULL,
            C5_ICMS DECIMAL(18,2) NULL,
            C5_IPI DECIMAL(18,2) NULL,
            C5_TOTAL_BRUTO DECIMAL(18,2) NULL,
            C5_ORIGEM NVARCHAR(20) NULL,
            C5_MOTIVO_CANCEL NVARCHAR(200) NULL,
            C5_DATA_CANCEL DATETIME2(0) NULL,
            C5_USUARIO_CANCEL NVARCHAR(50) NULL,
            D_E_L_E_T_ CHAR(1) NULL,
            R_E_C_N_O_ INT NULL,
            R_E_C_D_E_L_ INT NULL
        );
        CREATE INDEX IX_SC5_FILIAL_DATA_STATUS ON dbo.SC5_PEDIDOS (C5_FILIAL, C5_DATA, C5_STATUS);
    END
    """,
    """
    IF OBJECT_ID('dbo.SC6_ITENS', 'U') IS NULL
    BEGIN
        CREATE TABLE dbo.SC6_ITENS (
            ID INT IDENTITY(1,1) NOT NULL PRIMARY KEY,
            C6_PEDIDO_ID INT NOT NULL,
            C6_ITEM INT NULL,
            C6_PRODUTO NVARCHAR(50) NOT NULL,
            C6_QTD INT NOT NULL,
            C6_VALOR DECIMAL(18,2) NOT NULL,
            C6_PRECO_UNIT DECIMAL(18,2) NULL,
            C6_TOTAL DECIMAL(18,2) NULL,
            D_E_L_E_T_ CHAR(1) NULL,
            R_E_C_N_O_ INT NULL,
            R_E_C_D_E_L_ INT NULL
        );
        CREATE INDEX IX_SC6_PEDIDO ON dbo.SC6_ITENS (C6_PEDIDO_ID, C6_ITEM);
    END
    """,
    """
    IF OBJECT_ID('dbo.SC9_LIBERACAO', 'U') IS NULL
    BEGIN
        CREATE TABLE dbo.SC9_LIBERACAO (
            ID INT IDENTITY(1,1) NOT NULL PRIMARY KEY,
            C9_PEDIDO_ID INT NOT NULL,
            C9_FILIAL NVARCHAR(10) NOT NULL,
            C9_PRODUTO NVARCHAR(50) NOT NULL,
            C9_QTD INT NOT NULL,
            C9_STATUS NVARCHAR(20) NOT NULL,
            C9_USUARIO NVARCHAR(50) NOT NULL,
            C9_DATA DATETIME2(0) NOT NULL,
            C9_ITEM INT NULL,
            C9_USUARIO_CANCEL NVARCHAR(50) NULL,
            C9_DATA_CANCEL DATETIME2(0) NULL,
            D_E_L_E_T_ CHAR(1) NULL,
            R_E_C_N_O_ INT NULL,
            R_E_C_D_E_L_ INT NULL
        );
        CREATE INDEX IX_SC9_PEDIDO_STATUS ON dbo.SC9_LIBERACAO (C9_PEDIDO_ID, C9_STATUS, C9_ITEM);
    END
    """,
    """
    IF OBJECT_ID('dbo.SF2_NOTAS', 'U') IS NULL
    BEGIN
        CREATE TABLE dbo.SF2_NOTAS (
            ID INT IDENTITY(1,1) NOT NULL PRIMARY KEY,
            F2_DOC NVARCHAR(20) NOT NULL,
            F2_SERIE NVARCHAR(10) NOT NULL,
            F2_EMISSAO DATETIME2(0) NOT NULL,
            F2_FILIAL NVARCHAR(10) NOT NULL,
            F2_CLIENTE NVARCHAR(120) NULL,
            F2_CLIENTE_COD NVARCHAR(20) NULL,
            F2_VALOR DECIMAL(18,2) NOT NULL,
            F2_ICMS DECIMAL(18,2) NULL,
            F2_IPI DECIMAL(18,2) NULL,
            F2_PIS DECIMAL(18,2) NULL,
            F2_COFINS DECIMAL(18,2) NULL,
            F2_ICMS_ST DECIMAL(18,2) NULL,
            F2_DIFAL DECIMAL(18,2) NULL,
            F2_TOTAL_BRUTO DECIMAL(18,2) NULL,
            F2_STATUS NVARCHAR(20) NOT NULL,
            F2_PEDIDO_ID INT NULL,
            F2_TES NVARCHAR(10) NULL,
            F2_CFOP NVARCHAR(10) NULL,
            F2_ORIGEM NVARCHAR(20) NULL,
            F2_DATA_CANCEL DATETIME2(0) NULL,
            F2_USUARIO_CANCEL NVARCHAR(50) NULL,
            F2_MOTIVO_CANCEL NVARCHAR(200) NULL,
            D_E_L_E_T_ CHAR(1) NULL,
            R_E_C_N_O_ INT NULL,
            R_E_C_D_E_L_ INT NULL
        );
        CREATE UNIQUE INDEX UX_SF2_FILIAL_DOC_SERIE ON dbo.SF2_NOTAS (F2_FILIAL, F2_DOC, F2_SERIE);
    END
    """,
    """
    IF OBJECT_ID('dbo.SD2_ITENS', 'U') IS NULL
    BEGIN
        CREATE TABLE dbo.SD2_ITENS (
            ID INT IDENTITY(1,1) NOT NULL PRIMARY KEY,
            D2_NF_ID INT NOT NULL,
            D2_DOC NVARCHAR(20) NOT NULL,
            D2_SERIE NVARCHAR(10) NOT NULL,
            D2_ITEM INT NOT NULL,
            D2_FILIAL NVARCHAR(10) NOT NULL,
            D2_PEDIDO_ID INT NULL,
            D2_PRODUTO NVARCHAR(50) NOT NULL,
            D2_QTD INT NOT NULL,
            D2_PRECO_UNIT DECIMAL(18,2) NULL,
            D2_TOTAL DECIMAL(18,2) NOT NULL,
            D2_ICMS DECIMAL(18,2) NULL,
            D2_IPI DECIMAL(18,2) NULL,
            D2_PIS DECIMAL(18,2) NULL,
            D2_COFINS DECIMAL(18,2) NULL,
            D2_ICMS_ST DECIMAL(18,2) NULL,
            D2_DIFAL DECIMAL(18,2) NULL,
            D2_CST_ICMS NVARCHAR(10) NULL,
            D2_CSOSN NVARCHAR(10) NULL,
            D2_CST_PIS NVARCHAR(10) NULL,
            D2_CST_COFINS NVARCHAR(10) NULL,
            D2_TES NVARCHAR(10) NULL,
            D2_CFOP NVARCHAR(10) NULL,
            D2_ITEM_NUM CHAR(4) NULL,
            D2_STATUS NVARCHAR(20) NULL,
            D2_DATA_CANCEL DATETIME2(0) NULL,
            D2_USUARIO_CANCEL NVARCHAR(50) NULL,
            D2_MOTIVO_CANCEL NVARCHAR(200) NULL,
            D_E_L_E_T_ CHAR(1) NULL,
            R_E_C_N_O_ INT NULL,
            R_E_C_D_E_L_ INT NULL
        );
        CREATE INDEX IX_SD2_NF ON dbo.SD2_ITENS (D2_NF_ID, D2_ITEM);
    END
    """,
    """
    IF OBJECT_ID('dbo.SE1_AR', 'U') IS NULL
    BEGIN
        CREATE TABLE dbo.SE1_AR (
            ID INT IDENTITY(1,1) NOT NULL PRIMARY KEY,
            E1_DATA DATETIME2(0) NOT NULL,
            E1_VENC DATE NOT NULL,
            E1_CLIENTE NVARCHAR(120) NULL,
            E1_CLIENTE_COD NVARCHAR(20) NULL,
            E1_VALOR DECIMAL(18,2) NOT NULL,
            E1_STATUS NVARCHAR(20) NOT NULL,
            E1_REF NVARCHAR(30) NULL,
            E1_NUM NVARCHAR(20) NOT NULL,
            E1_SERIE NVARCHAR(10) NOT NULL,
            E1_FILIAL NVARCHAR(10) NOT NULL,
            E1_SE5_ID INT NULL,
            D_E_L_E_T_ CHAR(1) NULL,
            R_E_C_N_O_ INT NULL,
            R_E_C_D_E_L_ INT NULL
        );
        CREATE UNIQUE INDEX UX_SE1_FILIAL_NUM_SERIE ON dbo.SE1_AR (E1_FILIAL, E1_NUM, E1_SERIE);
    END
    """,
    """
    IF OBJECT_ID('dbo.SF1_AP', 'U') IS NULL
    BEGIN
        CREATE TABLE dbo.SF1_AP (
            ID INT IDENTITY(1,1) NOT NULL PRIMARY KEY,
            F1_DATA DATETIME2(0) NOT NULL,
            F1_VENC DATE NOT NULL,
            F1_FORN NVARCHAR(120) NULL,
            F1_FORN_COD NVARCHAR(20) NULL,
            F1_VALOR DECIMAL(18,2) NOT NULL,
            F1_STATUS NVARCHAR(20) NOT NULL,
            F1_REF NVARCHAR(50) NULL,
            F1_NUM NVARCHAR(20) NOT NULL,
            F1_SERIE NVARCHAR(10) NOT NULL,
            F1_FILIAL NVARCHAR(10) NOT NULL,
            F1_SE5_ID INT NULL,
            D_E_L_E_T_ CHAR(1) NULL,
            R_E_C_N_O_ INT NULL,
            R_E_C_D_E_L_ INT NULL
        );
        CREATE UNIQUE INDEX UX_SF1_FILIAL_NUM_SERIE ON dbo.SF1_AP (F1_FILIAL, F1_NUM, F1_SERIE);
    END
    """,
    """
    IF OBJECT_ID('dbo.SE5_CONTAS', 'U') IS NULL
    BEGIN
        CREATE TABLE dbo.SE5_CONTAS (
            ID INT IDENTITY(1,1) NOT NULL PRIMARY KEY,
            E5_FILIAL NVARCHAR(10) NOT NULL,
            E5_NOME NVARCHAR(120) NOT NULL,
            E5_TIPO NVARCHAR(20) NOT NULL,
            E5_ATIVA BIT NOT NULL DEFAULT (1),
            D_E_L_E_T_ CHAR(1) NULL,
            R_E_C_N_O_ INT NULL,
            R_E_C_D_E_L_ INT NULL
        );
    END
    """,
    """
    IF OBJECT_ID('dbo.SE5_CATEG', 'U') IS NULL
    BEGIN
        CREATE TABLE dbo.SE5_CATEG (
            ID INT IDENTITY(1,1) NOT NULL PRIMARY KEY,
            C5_FILIAL NVARCHAR(10) NOT NULL,
            C5_NOME NVARCHAR(120) NOT NULL,
            C5_TIPO NVARCHAR(30) NOT NULL,
            C5_ATIVA BIT NOT NULL DEFAULT (1),
            D_E_L_E_T_ CHAR(1) NULL,
            R_E_C_N_O_ INT NULL,
            R_E_C_D_E_L_ INT NULL
        );
    END
    """,
    """
    IF OBJECT_ID('dbo.SE5_MOV', 'U') IS NULL
    BEGIN
        CREATE TABLE dbo.SE5_MOV (
            ID INT IDENTITY(1,1) NOT NULL PRIMARY KEY,
            E5_DATA DATETIME2(0) NOT NULL DEFAULT (SYSDATETIME()),
            E5_FILIAL NVARCHAR(10) NOT NULL,
            E5_CONTA_ID INT NOT NULL,
            E5_TIPO NVARCHAR(1) NOT NULL,
            E5_VALOR DECIMAL(18,2) NOT NULL,
            E5_HIST NVARCHAR(255) NULL,
            E5_ORIGEM_TIPO NVARCHAR(20) NULL,
            E5_ORIGEM_ID INT NULL,
            E5_USUARIO NVARCHAR(50) NULL,
            E5_CATEG_ID INT NULL,
            D_E_L_E_T_ CHAR(1) NULL,
            R_E_C_N_O_ INT NULL,
            R_E_C_D_E_L_ INT NULL
        );
        CREATE INDEX IX_SE5_FILIAL_CONTA_DATA ON dbo.SE5_MOV (E5_FILIAL, E5_CONTA_ID, E5_DATA, ID);
    END
    """,
    """
    IF OBJECT_ID('dbo.SD3_MOV', 'U') IS NULL
    BEGIN
        CREATE TABLE dbo.SD3_MOV (
            ID INT IDENTITY(1,1) NOT NULL PRIMARY KEY,
            D3_DATA DATETIME2(0) NOT NULL,
            D3_FILIAL NVARCHAR(10) NOT NULL,
            D3_PRODUTO NVARCHAR(50) NOT NULL,
            D3_TIPO NVARCHAR(1) NOT NULL,
            D3_QTD INT NOT NULL,
            D3_CUSTO_UNIT DECIMAL(18,2) NOT NULL,
            D3_VALOR DECIMAL(18,2) NOT NULL,
            D3_ORIGEM NVARCHAR(30) NULL,
            D3_REF NVARCHAR(50) NULL,
            D3_USUARIO NVARCHAR(50) NULL,
            D_E_L_E_T_ CHAR(1) NULL,
            R_E_C_N_O_ INT NULL,
            R_E_C_D_E_L_ INT NULL
        );
        CREATE INDEX IX_SD3_FILIAL_PRODUTO_DATA ON dbo.SD3_MOV (D3_FILIAL, D3_PRODUTO, D3_DATA);
    END
    """,
    """
    IF OBJECT_ID('dbo.SZ0_RESERVA', 'U') IS NULL
    BEGIN
        CREATE TABLE dbo.SZ0_RESERVA (
            ID INT IDENTITY(1,1) NOT NULL PRIMARY KEY,
            Z0_DATA DATETIME2(0) NOT NULL,
            Z0_FILIAL NVARCHAR(10) NOT NULL,
            Z0_PRODUTO NVARCHAR(50) NOT NULL,
            Z0_QTD INT NOT NULL,
            Z0_USUARIO NVARCHAR(50) NOT NULL,
            Z0_STATUS NVARCHAR(20) NOT NULL,
            Z0_CLIENTE_COD NVARCHAR(20) NULL,
            Z0_TABELA_ID INT NULL,
            Z0_PRECO_UNIT DECIMAL(18,2) NULL,
            Z0_TOTAL DECIMAL(18,2) NULL,
            Z0_PEDIDO_ID INT NULL,
            D_E_L_E_T_ CHAR(1) NULL,
            R_E_C_N_O_ INT NULL,
            R_E_C_D_E_L_ INT NULL
        );
        CREATE INDEX IX_SZ0_FILIAL_STATUS ON dbo.SZ0_RESERVA (Z0_FILIAL, Z0_STATUS);
    END
    """,
    """
    IF OBJECT_ID('dbo.SF7_FECHAMENTO', 'U') IS NULL
    BEGIN
        CREATE TABLE dbo.SF7_FECHAMENTO (
            ID INT IDENTITY(1,1) NOT NULL PRIMARY KEY,
            F7_FILIAL NVARCHAR(10) NOT NULL,
            F7_ANO INT NOT NULL,
            F7_MES INT NOT NULL,
            F7_FECHADO BIT NOT NULL DEFAULT (1),
            F7_DATA DATETIME2(0) NOT NULL DEFAULT (SYSDATETIME()),
            F7_USUARIO NVARCHAR(50) NULL,
            D_E_L_E_T_ CHAR(1) NULL,
            R_E_C_N_O_ INT NULL,
            R_E_C_D_E_L_ INT NULL
        );
        CREATE UNIQUE INDEX UX_SF7_FILIAL_ANO_MES ON dbo.SF7_FECHAMENTO (F7_FILIAL, F7_ANO, F7_MES) WHERE D_E_L_E_T_ IS NULL;
    END
    """,
]


def _ensure_database(admin_conn_str: str, db_name: str) -> None:
    with _connect_with_retry(admin_conn_str, autocommit=True) as conn:
        cur = conn.cursor()
        cur.execute(
            f"""
            IF DB_ID(N'{db_name}') IS NULL
            BEGIN
                CREATE DATABASE [{db_name}];
            END
            """
        )


def _ensure_schema(test_conn_str: str) -> None:
    with _connect_with_retry(test_conn_str, autocommit=True) as conn:
        cur = conn.cursor()
        cur.execute("SET NOCOUNT ON")
        for statement in SCHEMA_STATEMENTS:
            cur.execute(statement)


def main() -> None:
    admin_conn_str = _require_env("TEST_DB_ADMIN_CONN_STR")
    test_conn_str = _require_env("TEST_DB_CONN_STR")
    db_name = _extract_database_name(test_conn_str)
    _ensure_database(admin_conn_str, db_name)
    _ensure_schema(test_conn_str)
    print(f"Integration database ready: {db_name}")


if __name__ == "__main__":
    main()
