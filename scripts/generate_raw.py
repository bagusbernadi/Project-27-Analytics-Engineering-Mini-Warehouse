"""Project 27: file produksi, defect, dan rework harian (simulasi) pabrik lampu LED. Seed tetap.

150 hari kerja -> 150 file Excel (data/sim/daily/produksi_YYYYMMDD.xlsx, masing-masing 3 sheet: production, defect, rework).
+-9.000 baris produksi (10 stasiun x 3 model x 2 shift x 150 hari), +-15.000 baris defect. Hasil lain (data/sim/):
file_manifest.csv (tanggal bisnis vs tanggal diterima), truth_*.csv (data bersih), ground_truth.json.
Opsi benchmark: python scripts/generate_raw.py --big 1000000  -> data/sim/benchmark_production.csv (tidak termasuk jalan default).
Jalankan: python scripts/generate_raw.py   (versi data: v1; butuh openpyxl)
"""
import io
import json
import re
import sys
import zipfile
from pathlib import Path

import numpy as np
import pandas as pd
from openpyxl import Workbook

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "data" / "sim"
SEED = 27260302
DATA_VERSION = "v1"
N_DAYS, START = 150, "2026-03-02"
STATIONS = ["Chip Mounting", "LED Soldering", "Driver Assembly", "Housing Assembly", "Potting", "Wiring Check",
            "Burn-in Test", "Photometric Test", "Final QC", "Packing"]
MODELS, SHIFTS = ["5W", "9W", "12W"], ["Shift 1", "Shift 2"]
BASE_NG = [0.008, 0.012, 0.010, 0.008, 0.009, 0.007, 0.045, 0.015, 0.006, 0.003]   # Burn-in Test paling sering NG
NG_SCALE = 0.80
MODEL_F = {"5W": 0.9, "9W": 1.0, "12W": 1.15}
QTY = {"5W": 520, "9W": 480, "12W": 400}
DEFECTS = {0: ["CHP-01", "CHP-02"], 1: ["SLD-01", "SLD-02", "SLD-03"], 2: ["DRV-01", "DRV-02"], 3: ["HSG-01", "HSG-02"],
           4: ["POT-01", "POT-02"], 5: ["WIR-01", "WIR-02"], 6: ["BRN-01", "BRN-02", "BRN-03"], 7: ["PHM-01", "PHM-02", "PHM-03"],
           8: ["FQC-01", "FQC-02"], 9: ["PKG-01"]}
SPIKE = dict(station=7, start_day=70, length=5, factor=4.0)               # lonjakan NG Photometric Test +-1 minggu
COLUMN_CHANGE_DAY = 90                                                   # mulai bulan ke-4: kolom mentah berganti nama
LATE = dict(day=57, delay_days=2)                                         # satu file terlambat 2 hari
DIRTY_RATE = 0.025

rng = np.random.default_rng(SEED)
days = pd.bdate_range(START, periods=N_DAYS)
OPERATOR = {(s, sh): f"OP{(s * 2 + j) % 20 + 1:02d}" for s in range(10) for j, sh in enumerate(SHIFTS)}


def normalize_zip(path):
    buf = io.BytesIO()
    with zipfile.ZipFile(path) as zin, zipfile.ZipFile(buf, "w", zipfile.ZIP_DEFLATED) as zout:
        for name in sorted(zin.namelist()):
            zi = zipfile.ZipInfo(name, date_time=(2026, 1, 1, 0, 0, 0)); zi.compress_type = zipfile.ZIP_DEFLATED
            data = zin.read(name)
            if name == "docProps/core.xml":
                data = re.sub(rb"(<dcterms:(?:created|modified)[^>]*>)[^<]*", rb"\g<1>2026-01-01T00:00:00Z", data)
            zout.writestr(zi, data)
    Path(path).write_bytes(buf.getvalue())


def simulate_day(t, day):
    prod, dfc, rwk = [], [], []
    for s, st in enumerate(STATIONS):
        for m in MODELS:
            for sh in SHIFTS:
                qin = int(round(QTY[m] * rng.normal(1, 0.06)))
                p = NG_SCALE * BASE_NG[s] * MODEL_F[m] * float(np.exp(rng.normal(0, 0.15)))
                if s == SPIKE["station"] and SPIKE["start_day"] <= t < SPIKE["start_day"] + SPIKE["length"]:
                    p *= SPIKE["factor"]
                ng = int(rng.binomial(qin, min(p, 0.5)))
                prod.append([day.date(), sh, st, m, OPERATOR[(s, sh)], qin, qin - ng, ng])
                if ng:
                    split = rng.multinomial(ng, np.ones(len(DEFECTS[s])) / len(DEFECTS[s]))
                    for code, q in zip(DEFECTS[s], split):
                        if q:
                            dfc.append([day.date(), sh, st, m, code, int(q)])
                            if rng.random() < 0.6:
                                rw = int(rng.integers(1, q + 1))
                                rwk.append([day.date(), sh, st, m, code, rw, int(rng.binomial(rw, 0.88))])
    return prod, dfc, rwk


PCOL = ["date", "shift", "station", "model", "operator_id", "qty_input", "qty_ok", "qty_ng"]
DCOL = ["date", "shift", "station", "model", "defect_code", "qty"]
RCOL = ["date", "shift", "station", "model", "defect_code", "qty_rework", "qty_recovered"]
NEW_P = {"qty_input": "input_qty", "qty_ok": "ok_qty", "qty_ng": "ng_qty"}      # nama kolom baru mulai bulan ke-4
NEW_D = {"defect_code": "defect_cd"}


def run_default():
    (OUT / "daily").mkdir(parents=True, exist_ok=True)
    tp, td, tr, manifest, dirty_log = [], [], [], [], []
    for t, day in enumerate(days):
        prod, dfc, rwk = simulate_day(t, day)
        P, D, R = (pd.DataFrame(x, columns=c) for x, c in ((prod, PCOL), (dfc, DCOL), (rwk, RCOL)))
        tp.append(P.copy()); td.append(D.copy()); tr.append(R.copy())
        P = P.astype({"qty_input": object, "qty_ok": object, "qty_ng": object, "station": object})
        # data kotor (+-2,5% baris produksi): qty kosong, negatif, teks, nama stasiun huruf kecil, baris ganda
        kinds = ["blank_qty", "negative_qty", "text_qty", "lowercase_station", "duplicate_row"]
        pick = rng.permutation(len(P))[: max(1, int(round(len(P) * DIRTY_RATE)))]
        dup = []
        for k, i in enumerate(pick):
            kind = kinds[(t + k) % 5]
            if kind == "blank_qty": P.at[i, "qty_ng"] = None
            elif kind == "negative_qty": P.at[i, "qty_ng"] = -abs(int(P.at[i, "qty_ng"]) or 1)
            elif kind == "text_qty": P.at[i, "qty_input"] = f"{P.at[i, 'qty_input']} pcs"
            elif kind == "lowercase_station": P.at[i, "station"] = str(P.at[i, "station"]).lower()
            else: dup.append(i)
            dirty_log.append([f"produksi_{day.strftime('%Y%m%d')}.xlsx", int(i) + 2, kind])
        if dup:
            P = pd.concat([P, P.loc[dup]]).sort_index(kind="stable").reset_index(drop=True)
        if t >= COLUMN_CHANGE_DAY:
            P = P.rename(columns=NEW_P); P["line_id"] = "LINE-1"
            D = D.rename(columns=NEW_D)
        name = f"produksi_{day.strftime('%Y%m%d')}.xlsx"
        wb = Workbook(); wb.properties.creator = "simulasi"
        for title, frame in (("production", P), ("defect", D), ("rework", R)):
            ws = wb.active if title == "production" else wb.create_sheet(title)
            ws.title = title
            ws.append(list(frame.columns))
            for row in frame.itertuples(index=False):
                ws.append([None if (isinstance(v, float) and np.isnan(v)) else (v.item() if hasattr(v, "item") else v) for v in row])
        wb.save(OUT / "daily" / name); normalize_zip(OUT / "daily" / name)
        recv = day + pd.offsets.BDay(1 + (LATE["delay_days"] if t == LATE["day"] else 0))
        manifest.append([name, day.date(), recv.date()])
    for nm, frames in (("production", tp), ("defect", td), ("rework", tr)):
        pd.concat(frames).to_csv(OUT / f"truth_{nm}.csv", index=False)
    pd.DataFrame(manifest, columns=["file_name", "business_date", "received_date"]).to_csv(OUT / "file_manifest.csv", index=False)
    pd.DataFrame(dirty_log, columns=["file_name", "excel_row", "dirty_type"]).to_csv(OUT / "ground_truth_dirty.csv", index=False)
    P_all, D_all = pd.concat(tp), pd.concat(td)
    gt = {"seed": SEED, "version": DATA_VERSION, "n_files": N_DAYS, "production_rows": len(P_all), "defect_rows": len(D_all),
          "facts": [{"id": 1, "fact": "Burn-in Test paling sering NG", "station": STATIONS[6]},
                    {"id": 2, "fact": "Lonjakan NG Photometric Test", "start": str(days[SPIKE["start_day"]].date()),
                     "end": str(days[SPIKE["start_day"] + SPIKE["length"] - 1].date()), "factor": SPIKE["factor"]},
                    {"id": 3, "fact": "Kolom file mentah berganti nama mulai bulan ke-4", "from": str(days[COLUMN_CHANGE_DAY].date()),
                     "production": NEW_P, "defect": NEW_D, "new_column": "line_id"},
                    {"id": 4, "fact": "Satu file terlambat 2 hari", "file": manifest[LATE["day"]][0]},
                    {"id": 5, "fact": "Data kotor", "rate": DIRTY_RATE, "n_rows": len(dirty_log)}]}
    (OUT / "ground_truth.json").write_text(json.dumps(gt, indent=2, ensure_ascii=False), encoding="utf-8")
    print(f"{N_DAYS} file, produksi {len(P_all)} baris, defect {len(D_all)} baris, kotor {len(dirty_log)}")


def run_big(n_rows):
    """Perbesar data produksi untuk benchmark (n_rows baris), seed tetap."""
    OUT.mkdir(parents=True, exist_ok=True)
    idx = rng.integers(0, len(STATIONS), n_rows)
    mdl = rng.integers(0, 3, n_rows)
    qin = np.round(np.array([QTY[MODELS[i]] for i in range(3)])[mdl] * rng.normal(1, 0.06, n_rows)).astype(int)
    ng = rng.binomial(qin, np.minimum(np.array(BASE_NG)[idx] * np.array([MODEL_F[m] for m in MODELS])[mdl], 0.5))
    date = days.date[rng.integers(0, N_DAYS, n_rows)]
    pd.DataFrame({"date": date, "station": np.array(STATIONS)[idx], "model": np.array(MODELS)[mdl],
                  "qty_input": qin, "qty_ok": qin - ng, "qty_ng": ng}).to_csv(OUT / "benchmark_production.csv", index=False)
    print(f"benchmark_production.csv {n_rows} baris")


if __name__ == "__main__":
    if "--big" in sys.argv:
        run_big(int(sys.argv[sys.argv.index("--big") + 1]))
    else:
        run_default()
