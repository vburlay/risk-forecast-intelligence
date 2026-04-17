import duckdb
from pack.config import DB_PATH

con = duckdb.connect(DB_PATH, read_only=True)

print("DB_PATH:", DB_PATH)
print("TABLES:", con.execute("SHOW TABLES").fetchall())
print("team_prognose:", con.execute("SELECT COUNT(*) FROM team_prognose").fetchone())
print("anomalie:", con.execute("SELECT COUNT(*) FROM anomalie").fetchone())
print("raw_bestand:", con.execute("SELECT COUNT(*) FROM raw_bestand").fetchone())

con.close()