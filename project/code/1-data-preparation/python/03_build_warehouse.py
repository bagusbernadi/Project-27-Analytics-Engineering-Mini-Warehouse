"""Langkah 5-7: membangun gudang dengan dbt (staging, dimensi, fakta) dan menjalankan semua data tests, lalu mencatat hasilnya.

Masukan : warehouse.duckdb dengan schema raw (dari 02_load_raw.py), project dbt di code/dbt, data/raw/ground_truth*.csv/json.
Keluaran (results/1-data-preparation/):
  dbt_test_results.csv    satu baris per test pada run dbt build (status, jumlah baris gagal, durasi)
  dbt_model_results.csv   satu baris per model (baris, durasi)
  dirty_detection.csv     data kotor yang ditanam vs yang ditangkap test, per jenis
  event_detection.csv     lima fakta yang ditanam vs test/analisis yang menangkapnya
  schema_drift_check.csv  hasil test skema bila hanya skema v1 diterima (bukti test gagal pada perubahan kolom bulan ke-4)
  run_timing.csv          durasi dbt build
Jalankan dari mana saja; butuh dbt-core dan dbt-duckdb.
"""
import json
import subprocess
import sys
import time
from pathlib import Path

import duckdb
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
import common as C  # noqa: E402

DBT = ["dbt", "--no-use-colors"]
env = {**__import__("os").environ, "WAREHOUSE_PATH": str(C.DB_PATH)}


def run(args):
    t = time.perf_counter()
    p = subprocess.run(DBT + args + ["--profiles-dir", "."], cwd=C.DBT_DIR, capture_output=True, text=True, env=env)
    return p, time.perf_counter() - t


p, dur = run(["build"])
assert p.returncode == 0, p.stdout[-2000:] + p.stderr[-1000:]
rr = json.loads((C.DBT_DIR / "target" / "run_results.json").read_text())
rows, mrows = [], []
for r in rr["results"]:
    uid = r["unique_id"]
    if uid.startswith("test."):
        rows.append(dict(test=uid.split(".")[2], status=r["status"], failures=int(r.get("failures") or 0),
                         layer="raw" if uid.split(".")[2].startswith("raw_") else ("staging" if "stg_" in uid.split(".")[2] else "mart")))
    else:
        mrows.append(dict(model=uid.split(".")[2], status=r["status"]))
tests = pd.DataFrame(rows).sort_values("test").reset_index(drop=True)
models = pd.DataFrame(mrows).sort_values("model").reset_index(drop=True)
con = duckdb.connect(str(C.DB_PATH), read_only=True)
models["rows"] = [con.execute(f"SELECT count(*) FROM {m}").fetchone()[0] for m in models.model]
tests.to_csv(C.RES_PREP / "dbt_test_results.csv", index=False)
models.to_csv(C.RES_PREP / "dbt_model_results.csv", index=False)
pd.DataFrame([dict(step="dbt build", seconds=round(dur, 2), tests=len(tests), models=len(models), pass_=int((tests.status == "pass").sum()), warn=int((tests.status == "warn").sum()),
                   error=int((tests.status.isin(["fail", "error"])).sum()))]).to_csv(C.RES_PREP / "run_timing.csv", index=False)
assert not tests.status.isin(["fail", "error"]).any(), tests[tests.status.isin(["fail", "error"])]

# ---- data kotor ditanam vs ditangkap test (per file dan jenis)
gt = pd.read_csv(C.RAW_DIR / "ground_truth_dirty.csv")
planted = gt.groupby(["file_name", "dirty_type"]).size().rename("planted")
KIND = {"blank_qty": "raw_production_ng_blank", "negative_qty": "raw_production_ng_negative", "text_qty": "raw_production_qty_not_numeric",
        "lowercase_station": "raw_production_station_not_standard", "duplicate_row": "raw_production_duplicate"}
out = []
for kind, tname in KIND.items():
    sql = (C.DBT_DIR / "target" / "compiled" / "led_warehouse" / "tests" / "raw" / f"{tname}.sql").read_text()
    det = con.execute(f"SELECT _source_file AS file_name, count(*) AS n FROM ({sql}) GROUP BY 1").df().set_index("file_name").n
    pl = planted.xs(kind, level="dirty_type")
    both = pd.concat([pl, det], axis=1).fillna(0)
    out.append(dict(dirty_type=kind, test=tname, planted=int(pl.sum()), detected=int(det.sum()), files_planted=int((pl > 0).sum()), files_detected=int((det > 0).sum()),
                    exact_per_file=bool((both.planted == both.n).all())))
dd = pd.DataFrame(out)
dd.to_csv(C.RES_PREP / "dirty_detection.csv", index=False)
n_prod_raw = con.execute("SELECT count(*) FROM raw.production").fetchone()[0]
late_files = con.execute((C.DBT_DIR / "target" / "compiled" / "led_warehouse" / "tests" / "raw" / "raw_file_freshness.sql").read_text()).df().file_name.tolist()
con.close()

# ---- test skema: terima hanya skema v1 -> harus gagal pada file mulai bulan ke-4
v1 = ["production:date|shift|station|model|operator_id|qty_input|qty_ok|qty_ng", "defect:date|shift|station|model|defect_code|qty", "rework:date|shift|station|model|defect_code|qty_rework|qty_recovered"]
p2, _ = run(["test", "--select", "raw_schema_signature", "--vars", json.dumps({"accepted_signatures": v1})])
rr2 = json.loads((C.DBT_DIR / "target" / "run_results.json").read_text())["results"][0]
drift_status, drift_failures = rr2["status"], int(rr2.get("failures") or 0)
con = duckdb.connect(str(C.DB_PATH), read_only=True)
csql = (C.DBT_DIR / "target" / "compiled" / "led_warehouse" / "tests" / "raw" / "raw_schema_signature.sql").read_text()
sd = con.execute(csql).df()
con.close()
sd.to_csv(C.RES_PREP / "schema_drift_check.csv", index=False)
gtj = json.loads((C.RAW_DIR / "ground_truth.json").read_text())
man = pd.read_csv(C.RAW_DIR / "file_manifest.csv")
change_from = gtj["facts"][2]["from"].replace("-", "")
files_changed = {f for f in man.file_name if f.split("_")[1][:8] >= change_from}
drift_files = set(sd.file_name)
late_file = gtj["facts"][3]["file"]
fr = tests.set_index("test").loc["raw_file_freshness"]
ev = pd.DataFrame([
    (1, gtj["facts"][0]["fact"], "analisis (fct_kpi_daily, Tabel KPI per stasiun)", "dicek di 04_run_queries.py", ""),
    (2, gtj["facts"][1]["fact"], "analisis (anomali FPY stasiun per minggu)", "dicek di 04_run_queries.py", ""),
    (3, gtj["facts"][2]["fact"], "test raw_schema_signature (hanya skema v1 diterima)", f"status {drift_status}: {len(drift_files)} file gagal, {len(files_changed)} file berubah", "Sesuai" if (drift_files == files_changed and drift_status == "fail") else "Tidak sesuai"),
    (4, gtj["facts"][3]["fact"], "test raw_file_freshness (warn)", f"{int(fr.failures)} file terlambat: {late_files[0] if len(late_files) else '-'}", "Sesuai" if (list(late_files) == [late_file] and fr.status == "warn") else "Tidak sesuai"),
    (5, gtj["facts"][4]["fact"], "lima test raw_production_*", f"{int(dd.detected.sum())} dari {int(dd.planted.sum())} baris kotor tertangkap ({n_prod_raw} baris mentah)", "Sesuai" if (dd.planted == dd.detected).all() else "Tidak sesuai"),
], columns=["fact_no", "fakta", "penangkap", "temuan", "hasil"])
ev.to_csv(C.RES_PREP / "event_detection.csv", index=False)
print(f"dbt build {dur:.1f} s; {len(tests)} test ({(tests.status == 'pass').sum()} pass, {(tests.status == 'warn').sum()} warn); schema drift file: {len(drift_files)} dari {len(files_changed)}")
print(dd.to_string(index=False))
