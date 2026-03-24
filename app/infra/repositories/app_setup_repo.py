from app.infra.db import fetchone_dict


def ensure_app_setup_state_table_tx(cur) -> None:
    cur.execute(
        """
        IF OBJECT_ID('dbo.APP_SETUP_STATE', 'U') IS NULL
        BEGIN
            CREATE TABLE dbo.APP_SETUP_STATE (
                ID INT IDENTITY(1,1) PRIMARY KEY,
                SETUP_COMPLETED BIT NOT NULL DEFAULT 0,
                COMPLETED_AT DATETIME2 NULL,
                COMPLETED_BY NVARCHAR(100) NULL
            );

            INSERT INTO dbo.APP_SETUP_STATE (SETUP_COMPLETED, COMPLETED_AT, COMPLETED_BY)
            VALUES (0, NULL, NULL);
        END
        """
    )


def app_setup_is_completed_tx(cur) -> bool:
    ensure_app_setup_state_table_tx(cur)
    cur.execute(
        """
        SELECT TOP 1 SETUP_COMPLETED
        FROM dbo.APP_SETUP_STATE
        ORDER BY ID
        """
    )
    row = fetchone_dict(cur)
    return bool(row and row.get("SETUP_COMPLETED"))


def app_setup_status_tx(cur) -> dict:
    ensure_app_setup_state_table_tx(cur)
    cur.execute(
        """
        SELECT TOP 1 SETUP_COMPLETED, COMPLETED_AT, COMPLETED_BY
        FROM dbo.APP_SETUP_STATE
        ORDER BY ID
        """
    )
    row = fetchone_dict(cur) or {}
    return {
        "setup_completed": bool(row.get("SETUP_COMPLETED")),
        "completed_at": row.get("COMPLETED_AT"),
        "completed_by": row.get("COMPLETED_BY"),
    }


def app_setup_mark_completed_tx(cur, login: str) -> None:
    ensure_app_setup_state_table_tx(cur)
    cur.execute(
        """
        UPDATE dbo.APP_SETUP_STATE
        SET SETUP_COMPLETED = 1,
            COMPLETED_AT = SYSDATETIME(),
            COMPLETED_BY = ?
        WHERE ID = (
            SELECT TOP 1 ID
            FROM dbo.APP_SETUP_STATE
            ORDER BY ID
        )
        """,
        (login,),
    )
