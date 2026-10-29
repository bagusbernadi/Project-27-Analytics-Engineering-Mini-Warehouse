"""Q14: bangun ulang seluruh warehouse dari database kosong dua kali dan bandingkan hash isi tiap tabel (staging dan mart).
Tiap run: hapus database, muat 150 file, dbt build, ekspor tiap tabel terurut ke CSV, hitung SHA-256 isi.
Keluaran: results/4-automation/rebuild_check.csv (deterministik)."""
import hashlib
import os
import subprocess
import sys
import tempfile
from pathlib import Path

import duckdb
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
import common as C  # noqa: E402

TABLES = ["stg_production", "stg_defect", "stg_rework", "dim_station", "dim_defect", "fct_kpi_daily", "fct_defect_pareto", "fct_line_weekly"]
LOAD = C.CODE / "1-data-preparation" / "python" / "02_load_raw.py"
res = {}
for run in (1, 2):
    with tempfile.TemporaryDirectory() as td:
        db = Path(td) / "w.duckdb"
        env = {**os.environ, "WAREHOUSE_PATH": str(db)}
        assert subprocess.run([sys.executable, str(LOAD)], env=env, capture_output=True, text=True).returncode == 0
        p = subprocess.run(["dbt", "--no-use-colors", "build", "--profiles-dir", "."], cwd=C.DBT_DIR, env=env, capture_output=True, text=True)
        assert p.returncode == 0, p.stdout[-1500:]
        con = duckdb.connect(str(db), read_only=True)
        for t in TABLES:
            f = Path(td) / f"{t}.csv"
            con.execute(f"COPY (SELECT * FROM {t} ORDER BY ALL) TO '{f}' (HEADER, DELIMITER ',')")
            res[(t, run)] = (con.execute(f"SELECT count(*) FROM {t}").fetchone()[0], hashlib.sha256(f.read_bytes()).hexdigest())
        con.close()
rows = [dict(tabel=t, baris=res[(t, 1)][0], sha256_run1=res[(t, 1)][1][:16], sha256_run2=res[(t, 2)][1][:16], sama=res[(t, 1)] == res[(t, 2)]) for t in TABLES]
df = pd.DataFrame(rows); df.to_csv(C.RES_AUTO / "rebuild_check.csv", index=False)
print(df.to_string(index=False)); assert df.sama.all()
