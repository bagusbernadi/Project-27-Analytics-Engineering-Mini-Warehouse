"""Langkah 16: membuat dan menjalankan dua notebook dari CSV hasil: analysis.ipynb (Q1-Q8, Q10-Q14) dan benchmark.ipynb (Q9)."""
import sys
from pathlib import Path

import nbformat as nbf
from nbclient import NotebookClient

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
import common as C  # noqa: E402

M, K = nbf.v4.new_markdown_cell, nbf.v4.new_code_cell
SETUP = K("""from pathlib import Path
import pandas as pd, numpy as np, matplotlib.pyplot as plt
ROOT = Path.cwd()
while not (ROOT / 'results').exists():
    ROOT = ROOT.parent
R = lambda f: pd.read_csv(next((ROOT / 'results' / d / f) for d in ('1-data-preparation', '2-analysis', '3-presentation', '4-automation') if (ROOT / 'results' / d / f).exists()))
pd.options.display.float_format = '{:.4f}'.format
plt.rcParams.update({'figure.figsize': (9, 3.6), 'axes.spines.top': False, 'axes.spines.right': False})
BLUE, GREY, ORANGE = '#1A73E8', '#9AA0A6', '#E8710A'""")
ana = [
    M("# Project 27: Analisis KPI produksi\n\nSemua tabel dibaca dari `results/` (hasil mart dbt). Data simulasi buatan sendiri, 150 file Excel harian."), SETUP,
    M("## KPI per stasiun (urut proses)"), K("k = R('kpi_station.csv').sort_values('sequence'); k[['station_name', 'input_qty', 'ng_qty', 'fpy', 'ng_rate', 'rework_rate', 'scrap_rate']]"),
    K("k2 = k.sort_values('ng_rate', ascending=False); plt.bar(k2.station_name, k2.ng_rate, color=[ORANGE] + [BLUE] * 9); plt.xticks(rotation=35, ha='right'); plt.ylabel('NG rate'); plt.show()"),
    M("## KPI lini: RTY dan final yield"), K("R('kpi_line_total.csv')"),
    K("t = R('trend_weekly.csv'); plt.plot(t.week, t.rty, color=BLUE, label='RTY'); plt.plot(t.week, t.final_yield, color=GREY, label='final yield'); plt.xticks(t.week[::4], rotation=30); plt.legend(); plt.show()"),
    M("## Minggu turun dan lonjakan harian"), K("d = R('drop_weeks.csv'); display(d[d.is_drop]); s = R('spike_detection.csv'); s[s.is_spike]"),
    M("## Pareto defect per stasiun\nDefect dalam satu stasiun terbagi hampir merata, jadi tidak ada defect dominan."), K("R('pareto_80.csv')"),
    M("## Shift dan model (chi-square)"), K("display(R('ng_tests.csv')); R('ng_by_model.csv')"),
    M("## Validasi: mart vs rekap Excel (SUMIFS) dan rekap manual dari raw"),
    K("b = R('crosscheck_excel.csv'); print(f'Excel vs mart: {(b.status == \"PASS\").sum()} dari {len(b)} PASS'); display(R('crosscheck_manual_causes.csv')); m = R('crosscheck_manual_diff.csv'); print('selisih FPY maks (poin):', round(m.fpy_diff_pts.abs().max(), 3))"),
    M("## Lima fakta yang ditanam dan hasil deteksi"), K("display(R('event_detection.csv')); R('dirty_detection.csv')"),
    M("## Hasil uji dbt"), K("t = R('dbt_test_results.csv'); t.groupby(['layer', 'status']).size()"),
    M("## Dampak: waktu hemat dan angka naif vs bersih"), K("display(R('impact_hours.csv')); display(R('impact_naive_vs_clean.csv')); R('impact_naive_by_station.csv')"),
    M("## Otomasi: log 10 run harian simulasi"), K("display(R('run_log.csv')); R('gate_test.csv')"),
]
bench = [M("# Project 27: Benchmark pandas vs Polars vs DuckDB\n\n1 juta baris produksi sintetis (`01_generate_raw.py --big 1000000`); tiap tugas diulang 3 kali, dilaporkan median. Waktu bergantung pada mesin."), SETUP,
         K("display(R('benchmark_env.csv')); b = R('benchmark.csv'); b"),
         K("p = b.pivot(index='task', columns='engine', values='median_s'); p.plot.bar(color=[BLUE, GREY, ORANGE], rot=0); plt.ylabel('detik (median)'); plt.show()")]
for name, cells in (("analysis", ana), ("benchmark", bench)):
    nb = nbf.v4.new_notebook(cells=cells, metadata={"kernelspec": {"name": "python3", "display_name": "Python 3", "language": "python"}})
    NotebookClient(nb, timeout=300, kernel_name="python3", resources={"metadata": {"path": str(C.ROOT)}}).execute()
    nbf.write(nb, C.RES_PRESENT / f"{name}.ipynb")
    errs = [o for c in nb.cells if c.cell_type == "code" for o in c.get("outputs", []) if o.output_type == "error"]
    print(name, len(nb.cells), "sel;", len(errs), "error")
    assert not errs
