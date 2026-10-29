"""Langkah 8: menjalankan query analisis pada mart dbt dan menyimpan hasilnya (Q1, Q3, Q4, Q5), ditambah analisis statistik singkat.

Masukan : warehouse.duckdb (setelah dbt build), 2-analysis/sql/01_queries.sql.
Keluaran: results/2-analysis/<nama_query>.csv, pareto_80.csv, drop_weeks.csv, spike_detection.csv, ng_tests.csv.
"""
import re
import sys
from pathlib import Path

import duckdb
import numpy as np
import pandas as pd
from scipy import stats

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
import common as C  # noqa: E402

con = duckdb.connect(str(C.DB_PATH), read_only=True)
parts = re.split(r"^-- name: (\S+)\s*$", (C.CODE / "2-analysis" / "sql" / "01_queries.sql").read_text(), flags=re.M)
for name, sql in zip(parts[1::2], parts[2::2]):
    con.execute(sql.strip().rstrip(";")).df().to_csv(C.RES_ANALYSIS / f"{name}.csv", index=False)

# Q3: berapa jenis defect untuk mencapai 80% NG tiap stasiun
par = pd.read_csv(C.RES_ANALYSIS / "defect_pareto_station.csv")
rows = []
for (code, name), g in par.groupby(["station_code", "station_name"], sort=False):
    n80 = int((g.cum_share.shift(fill_value=0) < 0.8).sum())
    rows.append(dict(station_code=code, station_name=name, n_defect_types=len(g), n_types_to_80pct=n80, top_defect=g.defect_code.iloc[0], top_share=g.share.iloc[0],
                     min_share=g.share.min(), max_share=g.share.max()))
pd.DataFrame(rows).to_csv(C.RES_ANALYSIS / "pareto_80.csv", index=False)

# Q4: uji perbedaan NG rate antar shift dan antar model (chi-square; operator tidak diuji karena setiap operator hanya bekerja di satu stasiun dan shift)
def chi(df, key):
    g = df.groupby(key)[["ng_qty", "input_qty"]].sum()
    ct = np.array([g.ng_qty, g.input_qty - g.ng_qty])
    c, p, dof, _ = stats.chi2_contingency(ct)
    return dict(factor=key, groups=len(g), chi2=c, dof=dof, p_value=p, cramers_v=float(np.sqrt(c / ct.sum())), min_rate=float((g.ng_qty / g.input_qty).min()), max_rate=float((g.ng_qty / g.input_qty).max()))

k = con.execute("SELECT k.shift, k.model, k.station_code, k.ng_qty, k.input_qty FROM fct_kpi_daily k").df()
# pengaruh shift dan model dikontrol per stasiun supaya perbedaan stasiun tidak menyamarkan efeknya
def chi_within(df, key):
    tot, dof, pmin = 0.0, 0, []
    for _, g in df.groupby("station_code"):
        gg = g.groupby(key)[["ng_qty", "input_qty"]].sum()
        ct = np.array([gg.ng_qty, gg.input_qty - gg.ng_qty]); c, p, d, _ = stats.chi2_contingency(ct); tot += c; dof += d
    return tot, dof, float(1 - stats.chi2.cdf(tot, dof))

res = [chi(k, "shift"), chi(k, "model")]
for r, key in zip(res, ("shift", "model")):
    c, d, p = chi_within(k, key); r.update(chi2_within_station=c, dof_within_station=d, p_within_station=p)
pd.DataFrame(res).to_csv(C.RES_ANALYSIS / "ng_tests.csv", index=False)

# Q5: minggu dengan penurunan RTY (di bawah rata-rata minus 2 simpangan baku robust) dan stasiun penyebabnya
tw = pd.read_csv(C.RES_ANALYSIS / "trend_weekly.csv")
med, mad = tw.rty.median(), (tw.rty - tw.rty.median()).abs().median() * 1.4826
tw["z_robust"] = (tw.rty - med) / mad
tw["is_drop"] = tw.z_robust < -2
sw = pd.read_csv(C.RES_ANALYSIS / "station_week_fpy.csv")
base = sw.groupby("station_code").ng_rate.median()
sw["ng_rate_ratio"] = sw.ng_rate / sw.station_code.map(base)
worst = sw.loc[sw.groupby("week").ng_rate_ratio.idxmax()][["week", "station_code", "ng_rate", "ng_rate_ratio"]].rename(columns={"station_code": "worst_station", "ng_rate": "worst_station_ng_rate"})
tw = tw.merge(worst, on="week")
tw.to_csv(C.RES_ANALYSIS / "drop_weeks.csv", index=False)

# fakta 2: lonjakan NG Photometric Test (stasiun S08) per hari, ambang median + 3 MAD
ph = pd.read_csv(C.RES_ANALYSIS / "station_daily_ng_photometric.csv")
m, mad = ph.ng_rate.median(), (ph.ng_rate - ph.ng_rate.median()).abs().median() * 1.4826
ph["z_robust"] = (ph.ng_rate - m) / mad
ph["is_spike"] = ph.z_robust > 3
ph.to_csv(C.RES_ANALYSIS / "spike_detection.csv", index=False)
print(tw[tw.is_drop][["week", "rty", "z_robust", "worst_station"]].to_string(index=False)); print("hari lonjakan S08:", ph[ph.is_spike].date.tolist())
print(pd.DataFrame(res)[["factor", "p_value", "min_rate", "max_rate"]].to_string(index=False))

# ---- lengkapi event_detection.csv fakta 1 dan 2 dari hasil analisis (fakta 3-5 diisi 03_build_warehouse.py)
_ev = pd.read_csv(C.RES_PREP / "event_detection.csv", dtype=str)
_ks = pd.read_csv(C.RES_ANALYSIS / "kpi_station.csv"); _sp = pd.read_csv(C.RES_ANALYSIS / "spike_detection.csv"); _dw = pd.read_csv(C.RES_ANALYSIS / "drop_weeks.csv")
_top = _ks.sort_values("ng_rate", ascending=False).iloc[0]
_ev.loc[_ev.fact_no == "1", ["temuan", "hasil"]] = [f"{_top.station_name} NG rate tertinggi: {_top.ng_rate:.2%} (urutan 1 dari 10)", "Sesuai" if _top.station_code == "S07" else "Tidak sesuai"]
_s = _sp[_sp.is_spike]
_dr = _dw[_dw.is_drop]
_ev.loc[_ev.fact_no == "2", ["temuan", "hasil"]] = [f"{len(_s)} hari lonjakan {_s.date.min()} s.d. {_s.date.max()}; minggu turun {', '.join(_dr.week)} dengan stasiun terburuk {', '.join(_dr.worst_station)}", "Sesuai" if set(_dr.worst_station) == {"S08"} else "Tidak sesuai"]
_ev.to_csv(C.RES_PREP / "event_detection.csv", index=False)
