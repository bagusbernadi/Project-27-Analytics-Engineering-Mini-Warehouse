"""Langkah 14: one-sheet infografik (PDF dan PNG) dari CSV hasil. Dibuat sebagai HTML lalu dicetak dengan Chromium (Playwright)."""
import sys
from pathlib import Path

import pandas as pd

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
sys.path.insert(0, str(ROOT / "code"))
sys.path.insert(0, str(ROOT.parent / "design-and-report" / "src"))
import common as C  # noqa: E402
from report_lib import BLUE, GREY, HI, bars, hbars  # noqa: E402

R = lambda f: pd.read_csv(C.result(f))
ks = R("kpi_station.csv"); line = R("kpi_line_total.csv").iloc[0]; dd = R("dirty_detection.csv"); hrs = R("impact_hours.csv").set_index("menit_per_laporan")
bm = R("benchmark.csv"); dw = R("drop_weeks.csv"); dw = dw[dw.is_drop].iloc[0]; run = R("run_log.csv")
pc = lambda v, d=1: f"{v * 100:.{d}f}".replace(".", ",") + "%"
fi = lambda v: f"{v:,.0f}".replace(",", ".")
top = ks.iloc[0]
chart1 = bars([(r.station_name.replace(" Test", "").replace(" Assembly", ""), r.ng_rate, HI if i == 0 else BLUE, f"{r.station_name}: NG rate {pc(r.ng_rate, 2)}") for i, r in enumerate(ks.itertuples())],
              lambda v: pc(v, 1), "NG rate per stasiun", h=240, rot=30, small=True)
agg = bm[bm.task == "baca + agregasi KPI"].sort_values("median_s")
chart2 = hbars([(r.engine, r.median_s, HI if i == 0 else BLUE, f"{r.engine}: {r.median_s:.2f} detik (median 3 kali, 1 juta baris)") for i, r in enumerate(agg.itertuples())],
               lambda v: f"{v:.2f} dtk", "Baca CSV + hitung KPI, 1 juta baris", float(agg.median_s.max()) * 1.2)
html = f"""<!doctype html><html lang="id"><head><meta charset="utf-8"><title>Infografik Project 27</title><style>
@page{{size:1100px 1500px;margin:0}}*{{box-sizing:border-box}}body{{margin:0;font:16px/1.5 "Source Sans 3",Calibri,Arial,sans-serif;color:#202124;background:#F8F9FA;width:1156px;padding:28px}}
h1{{margin:0;font-size:30px;color:#174EA6}}.sub{{color:#5F6368;margin:2px 0 18px}}.row{{display:grid;gap:14px;margin-bottom:14px}}.r3{{grid-template-columns:repeat(3,1fr)}}.r2{{grid-template-columns:1fr 1fr}}
.c{{background:#fff;border:1px solid #DADCE0;border-radius:16px;padding:16px 20px}}.k b{{display:block;font-size:38px;line-height:1.1;color:#1A73E8}}.k span{{color:#5F6368;font-size:14px}}
h3{{margin:0 0 6px;font-size:18px;color:#174EA6}}svg{{width:100%;height:auto}}svg text{{fill:#5F6368;font-size:12px}}.v{{background:#E6F4EA;border:1px solid #A8DAB5;color:#0D652D}}
.w{{background:#FEF7E0;border:1px solid #FDD663;font-size:14px}}.f{{color:#5F6368;font-size:13px;margin-top:10px}}</style></head><body>
<h1>{top.station_name} paling sering NG ({pc(top.ng_rate, 2)}); 300 dari 300 baris kotor tertangkap oleh uji dbt</h1>
<div class="sub">Project 27: Analytics Engineering Mini-Warehouse (lampu LED). 150 file Excel harian, data simulasi Mar–Sep 2026.</div>
<div class="row r3"><div class="c k"><b>{pc(line.rty, 1)}</b><span>RTY lini (hasil kali FPY 10 stasiun); final yield setelah rework {pc(line.final_yield, 1)}</span></div>
<div class="c k"><b>{int(dd.detected.sum())} / {int(dd.planted.sum())}</b><span>baris kotor ditanam dan tertangkap uji raw (5 jenis, dicocokkan per file)</span></div>
<div class="c k"><b>{int(hrs.jam_per_tahun.min())}–{int(hrs.jam_per_tahun.max())} jam</b><span>per tahun waktu rekap mingguan yang bisa dihemat (asumsi 60–120 menit per laporan, estimated)</span></div></div>
<div class="row"><div class="c v"><b>Kesimpulan:</b> pipeline mengubah file Excel yang berantakan menjadi KPI yang bisa diaudit. Minggu {dw.week} turun ke RTY {pc(dw.rty, 1)} karena Photometric Test (NG rate {pc(dw.worst_station_ng_rate, 1)}). Shift tidak berpengaruh pada NG; model lampu berpengaruh. {len(run) - 1} run harian simulasi semuanya lolos gerbang publish.</div></div>
<div class="row r2"><div class="c"><h3>NG rate per stasiun</h3>{chart1}</div><div class="c"><h3>Kecepatan mesin pengolah (1 juta baris)</h3>{chart2}</div></div>
<div class="row"><div class="c w"><h3>Perhatikan</h3>Data simulasi buatan sendiri; hasil membuktikan metode, bukan kondisi pabrik. Jam hemat adalah asumsi. GitHub Actions harian sudah ditulis tetapi belum terbukti berjalan 7 hari berturut-turut.</div></div>
<div class="f">Sumber: project/results (kpi_station.csv, kpi_line_total.csv, dirty_detection.csv, impact_hours.csv, benchmark.csv, drop_weeks.csv, run_log.csv).</div></body></html>"""
out = C.RES_PRESENT
tmp = out / "infographic.html"
tmp.write_text(html, encoding="utf-8")
from playwright.sync_api import sync_playwright  # noqa: E402

with sync_playwright() as p:
    b = p.chromium.launch(); pg = b.new_page(viewport={"width": 1156, "height": 1000})
    pg.goto(tmp.as_uri()); pg.wait_for_timeout(500)
    h = pg.evaluate("document.body.scrollHeight")
    pg.set_viewport_size({"width": 1156, "height": h}); pg.screenshot(path=str(out / "infographic.png"))
    pg.pdf(path=str(out / "infographic.pdf"), width="1156px", height=f"{h + 4}px", print_background=True)
    b.close()
tmp.unlink()
print("infografik", h)
