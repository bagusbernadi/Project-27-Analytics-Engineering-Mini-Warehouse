"""Langkah 10 (Q9): benchmark pandas vs Polars vs DuckDB pada ±1 juta baris produksi.

Tugas: baca CSV lalu hitung KPI harian per stasiun dan model (jumlah input, OK, NG, FPY, NG rate); hasil dari tiga mesin dicocokkan lebih dulu.
Tiap tugas diulang BENCH_REPEATS kali; yang dilaporkan median. Waktu bergantung pada mesin dan sengaja tidak ikut uji determinisme.
Masukan : data/raw/benchmark_production.csv (01_generate_raw.py --big 1000000). Keluaran: results/2-analysis/benchmark.csv, benchmark_env.csv.
"""
import os
import platform
import statistics
import sys
import time
from pathlib import Path

import duckdb
import pandas as pd
import polars as pl

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
import common as C  # noqa: E402

CSV = C.RAW_DIR / "benchmark_production.csv"
assert CSV.exists(), "jalankan: python code/1-data-preparation/python/01_generate_raw.py --big 1000000"


def pandas_task(read_only=False):
    df = pd.read_csv(CSV)
    if read_only:
        return len(df)
    g = df.groupby(["date", "station", "model"], as_index=False).agg(input_qty=("qty_input", "sum"), ok=("qty_ok", "sum"), ng=("qty_ng", "sum"))
    g["fpy"] = g.ok / g.input_qty; g["ng_rate"] = g.ng / g.input_qty
    return g.sort_values(["date", "station", "model"]).reset_index(drop=True)


def polars_task(read_only=False):
    df = pl.read_csv(CSV)
    if read_only:
        return df.height
    g = df.group_by(["date", "station", "model"]).agg(pl.col("qty_input").sum().alias("input_qty"), pl.col("qty_ok").sum().alias("ok"), pl.col("qty_ng").sum().alias("ng"))
    g = g.with_columns((pl.col("ok") / pl.col("input_qty")).alias("fpy"), (pl.col("ng") / pl.col("input_qty")).alias("ng_rate")).sort(["date", "station", "model"])
    return g.to_pandas()


def duck_task(read_only=False):
    con = duckdb.connect()
    if read_only:
        return con.execute(f"SELECT count(*) FROM read_csv_auto('{CSV}')").fetchone()[0]
    return con.execute(f"""SELECT date::VARCHAR AS date, station, model, sum(qty_input) AS input_qty, sum(qty_ok) AS ok, sum(qty_ng) AS ng, sum(qty_ok) * 1.0 / sum(qty_input) AS fpy, sum(qty_ng) * 1.0 / sum(qty_input) AS ng_rate
                           FROM read_csv_auto('{CSV}', types = {{'date': 'VARCHAR'}}) GROUP BY 1, 2, 3 ORDER BY 1, 2, 3""").df()


tasks = {"pandas": pandas_task, "Polars": polars_task, "DuckDB": duck_task}
# hasil harus sama di tiga mesin
ref = {k: f().astype({"date": str}) for k, f in tasks.items()}
for k in ("Polars", "DuckDB"):
    a, b = ref["pandas"], ref[k]
    assert len(a) == len(b) and (a.input_qty.values == b.input_qty.values).all() and (a.ng.values == b.ng.values).all() and abs(a.fpy.values - b.fpy.values).max() < 1e-12, k
rows = []
for name, f in tasks.items():
    for task, ro in (("baca CSV saja", True), ("baca + agregasi KPI", False)):
        ts = []
        for _ in range(C.BENCH_REPEATS):
            t = time.perf_counter(); f(ro); ts.append(time.perf_counter() - t)
        rows.append(dict(engine=name, task=task, median_s=statistics.median(ts), min_s=min(ts), max_s=max(ts), repeats=C.BENCH_REPEATS))
b = pd.DataFrame(rows)
base = b[b.engine == "pandas"].set_index("task").median_s
b["speedup_vs_pandas"] = b.apply(lambda r: base[r.task] / r.median_s, axis=1)
b["rows"] = len(pd.read_csv(CSV, usecols=["date"]))
b.to_csv(C.RES_ANALYSIS / "benchmark.csv", index=False)
pd.DataFrame([dict(python=platform.python_version(), platform=platform.platform(), cpu_count=os.cpu_count(), pandas=pd.__version__, polars=pl.__version__, duckdb=duckdb.__version__)]).to_csv(C.RES_ANALYSIS / "benchmark_env.csv", index=False)
print(b.round(3).to_string(index=False))
