import pandas as pd
import sqlalchemy as sa

sqlite_engine = sa.create_engine("sqlite:///protheus.db")

mssql_engine = sa.create_engine(
    "mssql+pyodbc://@localhost/ERP_PROTHEUS"
    "?driver=ODBC+Driver+18+for+SQL+Server"
    "&Trusted_Connection=yes"
    "&Encrypt=yes"
    "&TrustServerCertificate=yes",
    fast_executemany=True
)

tables = pd.read_sql(
    "SELECT name FROM sqlite_master WHERE type='table' AND name NOT LIKE 'sqlite_%';",
    sqlite_engine
)

for t in tables["name"]:
    df = pd.read_sql(f"SELECT * FROM {t}", sqlite_engine)
    df.to_sql(t, mssql_engine, if_exists="replace", index=False)
    print("Migrado:", t)

print("Migração concluída.")