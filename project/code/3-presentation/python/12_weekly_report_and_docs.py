"""Langkah 15: laporan mingguan otomatis (HTML+PDF, minggu terakhir) dan dokumentasi dbt (docs statis + lineage.csv).
Laporan memakai template Python (bukan Quarto). Keluaran: results/3-presentation/weekly_report.html|pdf, dbt_docs.html, lineage.csv."""
import json
import os
import subprocess
import sys
from pathlib import Path

import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
import common as C  # noqa: E402

k = pd.read_csv(C.RES_PRESENT / "dash_kpi_daily.csv"); w = pd.read_csv(C.RES_PRESENT / "dash_line_weekly.csv"); p = pd.read_csv(C.RES_PRESENT / "dash_pareto.csv")
k["week"] = (pd.to_datetime(k.date) - pd.to_timedelta(pd.to_datetime(k.date).dt.weekday, unit="D")).dt.strftime("%Y-%m-%d")
wk = sorted(k.week.unique())[-1]                       # minggu terakhir pada data (21-25 Sep, 5 hari kerja lengkap)
cur, prev = k[k.week == wk], k[k.week == sorted(k.week.unique())[-2]]
pc = lambda v, d=2: f"{v * 100:.{d}f}".replace(".", ",") + "%"
st = cur.groupby("station_name")[["input_qty", "ng_qty", "ok_first_pass"]].sum(); st["fpy"] = st.ok_first_pass / st.input_qty
pv = prev.groupby("station_name")[["input_qty", "ok_first_pass"]].sum(); st["fpy_prev"] = pv.ok_first_pass / pv.input_qty
st = st.sort_values("fpy")
rows = "".join(f"<tr><td>{n}</td><td>{int(r.input_qty)}</td><td>{int(r.ng_qty)}</td><td>{pc(r.fpy)}</td><td>{f'{(r.fpy - r.fpy_prev) * 100:+.2f}'.replace('.', ',')} poin</td></tr>" for n, r in st.iterrows())
wl = w[w.week == wk]
tp = p[p.week == wk].groupby(["station_code", "defect_name"]).qty.sum().sort_values(ascending=False).head(3)
html = f"""<!doctype html><html lang="id"><head><meta charset="utf-8"><title>Laporan mingguan</title><style>body{{font:15px/1.5 Calibri,Arial,sans-serif;margin:32px;color:#202124}}
h1{{color:#174EA6;font-size:24px}}table{{border-collapse:collapse;width:100%}}td,th{{border-bottom:1px solid #DADCE0;padding:6px 10px;text-align:left}}th{{background:#E8F0FE}}.n{{color:#5F6368;font-size:13px}}</style></head><body>
<h1>Laporan mingguan produksi, minggu {wk}</h1><p class="n">Dibuat otomatis dari mart dbt (data simulasi). RTY lini rata-rata antar model: {pc(wl.rty.mean(), 1)}; final yield {pc(wl.final_yield.mean(), 1)}.</p>
<h3>FPY per stasiun (terendah dulu), dibanding minggu sebelumnya</h3><table><tr><th>Stasiun</th><th>Input</th><th>NG</th><th>FPY</th><th>Selisih</th></tr>{rows}</table>
<h3>Tiga defect terbanyak minggu ini</h3><ul>{''.join(f'<li>{s} {d}: {int(q)} unit</li>' for (s, d), q in tp.items())}</ul>
<p class="n">Selisih = perubahan FPY dalam poin persentase terhadap minggu sebelumnya.</p></body></html>"""
(C.RES_PRESENT / "weekly_report.html").write_text(html, encoding="utf-8")
from playwright.sync_api import sync_playwright  # noqa: E402

with sync_playwright() as pw:
    b = pw.chromium.launch(); pg = b.new_page(); pg.goto((C.RES_PRESENT / "weekly_report.html").as_uri())
    pg.pdf(path=str(C.RES_PRESENT / "weekly_report.pdf"), format="A4", print_background=True); b.close()

env = {**os.environ, "WAREHOUSE_PATH": str(C.DB_PATH)}
r = subprocess.run(["dbt", "--no-use-colors", "docs", "generate", "--static", "--profiles-dir", "."], cwd=C.DBT_DIR, capture_output=True, text=True, env=env)
assert r.returncode == 0, r.stdout[-1500:] + r.stderr[-800:]
(C.RES_PRESENT / "dbt_docs.html").write_bytes((C.DBT_DIR / "target" / "static_index.html").read_bytes())
man = json.loads((C.DBT_DIR / "target" / "manifest.json").read_text())
edges = [(d.split(".")[-1], n["name"], n["resource_type"]) for n in man["nodes"].values() if n["resource_type"] == "model" for d in n["depends_on"]["nodes"]]
pd.DataFrame(sorted(edges), columns=["dari", "ke", "jenis_ke"]).to_csv(C.RES_PRESENT / "lineage.csv", index=False)
print("minggu", wk, "| edges", len(edges), "| docs KB", (C.RES_PRESENT / "dbt_docs.html").stat().st_size // 1024)
