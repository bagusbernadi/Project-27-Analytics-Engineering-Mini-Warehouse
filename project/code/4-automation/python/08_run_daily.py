"""Langkah 8 (Q8): satu run harian = muat file baru -> dbt build -> publish gate -> catat log.
Gerbang publish: jika ada uji severity error yang gagal, hasil TIDAK dipublikasikan (snapshot terakhir yang sehat tetap dipakai).
Uji severity warn (data kotor di raw) tidak menahan publish; dicatat di log.

Pemakaian:
  python 08_run_daily.py --simulate 10   simulasi 10 run harian lokal pada database terpisah (hasil: results/4-automation/run_log.csv)
  python 08_run_daily.py --date YYYY-MM-DD   satu run (dipakai GitHub Actions): memuat file dengan received_date <= tanggal itu
Keluaran: results/4-automation/run_log.csv (deterministik; waktu dan jam jalan ada di run_timing_daily.csv, volatil)."""
import argparse
import json
import os
import shutil
import subprocess
import sys
import time
from pathlib import Path

import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
import common as C  # noqa: E402

RES = C.ROOT / "results" / "4-automation"
RES.mkdir(parents=True, exist_ok=True)
PY = sys.executable
LOAD = C.CODE / "1-data-preparation" / "python" / "02_load_raw.py"


def sh(cmd, env, cwd=None):
    return subprocess.run(cmd, capture_output=True, text=True, env=env, cwd=cwd)


def one_run(date, db, first, pub_dir):
    env = {**os.environ, "WAREHOUSE_PATH": str(db)}
    t0 = time.perf_counter()
    ld = sh([PY, str(LOAD), "--through", date] + ([] if first else ["--append"]), env)
    assert ld.returncode == 0, ld.stderr[-1500:]
    n_new = int(ld.stdout.split("dimuat ")[1].split(" file")[0])
    p = sh(["dbt", "--no-use-colors", "build", "--profiles-dir", "."], env, cwd=C.DBT_DIR)
    rr = json.loads((C.DBT_DIR / "target" / "run_results.json").read_text())
    st = pd.Series([r["status"] for r in rr["results"]]).value_counts().to_dict()
    err = st.get("fail", 0) + st.get("error", 0)
    gate = "publish" if p.returncode == 0 and err == 0 else "tahan"
    if gate == "publish":
        pub_dir.mkdir(parents=True, exist_ok=True)
        shutil.copy(db, pub_dir / "warehouse_published.duckdb")
    return dict(run_date=date, file_baru=n_new, tes_pass=st.get("pass", 0), tes_warn=st.get("warn", 0), tes_error=err, model_sukses=st.get("success", 0),
                gerbang=gate), time.perf_counter() - t0


ap = argparse.ArgumentParser()
ap.add_argument("--simulate", type=int, default=0)
ap.add_argument("--date", default=None)
a = ap.parse_args()
man = pd.read_csv(C.RAW_DIR / "file_manifest.csv")
if a.simulate:
    days = sorted(man.received_date.unique())[-a.simulate:]
    db = C.ROOT / "warehouse_daily_sim.duckdb"
    db.unlink(missing_ok=True)
    pub = C.ROOT / "published_sim"
    shutil.rmtree(pub, ignore_errors=True)
    log, tim = [], []
    # run pertama memuat seluruh riwayat sampai hari sebelum jendela simulasi (full load), sisanya inkremental
    prev = sorted(man.received_date.unique())[-a.simulate - 1]
    first, secs = one_run(prev, db, True, pub)
    first["jenis"] = "full load awal"; log.append(first); tim.append((prev, secs))
    for d in days:
        r, secs = one_run(d, db, False, pub)
        r["jenis"] = "inkremental"; log.append(r); tim.append((d, secs))
    pd.DataFrame(log)[["run_date", "jenis", "file_baru", "tes_pass", "tes_warn", "tes_error", "model_sukses", "gerbang"]].to_csv(RES / "run_log.csv", index=False)
    pd.DataFrame(tim, columns=["run_date", "detik"]).round(2).to_csv(RES / "run_timing_daily.csv", index=False)
    db.unlink(missing_ok=True); shutil.rmtree(pub, ignore_errors=True)
    print(pd.DataFrame(log).to_string(index=False))
else:
    d = a.date or man.received_date.max()
    r, _ = one_run(d, C.DB_PATH, not C.DB_PATH.exists(), C.ROOT / "published")
    print(r); sys.exit(0 if r["gerbang"] == "publish" else 1)
