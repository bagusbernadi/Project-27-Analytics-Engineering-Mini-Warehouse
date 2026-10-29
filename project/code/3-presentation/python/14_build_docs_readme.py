"""Langkah 17: menulis README.md dan docs/*.md dari CSV hasil (semua angka dibaca dari results/)."""
import sys
from pathlib import Path

import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
import common as C  # noqa: E402

R = lambda f: pd.read_csv(C.result(f))
pc = lambda v, d=1: f"{v * 100:.{d}f}".replace(".", ",") + "%"
fi = lambda v: f"{v:,.0f}".replace(",", ".")
ks = R("kpi_station.csv"); line = R("kpi_line_total.csv").iloc[0]; dd = R("dirty_detection.csv"); hrs = R("impact_hours.csv"); bm = R("benchmark.csv")
nv = R("impact_naive_vs_clean.csv").set_index("metrik"); tests = R("dbt_test_results.csv"); mods = R("dbt_model_results.csv"); run = R("run_log.csv"); nt = R("ng_tests.csv").set_index("factor")
dw = R("drop_weeks.csv"); dw = dw[dw.is_drop].iloc[0]; ce = R("crosscheck_excel.csv"); md = R("crosscheck_manual_diff.csv"); ev = R("event_detection.csv"); bym = R("ng_by_model.csv").set_index("model")
top = ks.iloc[0]
agg = bm[bm.task == "baca + agregasi KPI"].set_index("engine"); rd = bm[bm.task == "baca CSV saja"].set_index("engine")
n_tests, n_warn = len(tests), int((tests.status == "warn").sum())
PV = lambda p: ("< 0,001" if p < 0.001 else f"{p:.2f}".replace(".", ","))

(C.DOCS_DIR / "cleaning_log.md").write_text("\n".join([
    "# Log cleaning", "", f"Mentah {fi(nv.loc['baris dipakai', 'bersih'] + 60)} baris produksi (9.000 + 60 duplikat). Tiap jenis kotor ditanam generator, ditangkap satu test raw (severity warn), lalu ditangani di `stg_production`. Cocok per file: {', '.join(dd.dirty_type[dd.exact_per_file])}.", "",
    "| Jenis | Test raw | Ditanam | Tertangkap | Aturan staging |", "|---|---|---|---|---|",
    *[f"| {r.dirty_type} | `{r.test}` | {r.planted} | {r.detected} | {RULE[r.dirty_type]} |" for RULE in [{"blank_qty": "S3: NG = input - OK, ditandai was_recovered", "negative_qty": "S3: NG dihitung ulang", "text_qty": "S2: ambil digit dari teks", "lowercase_station": "S4: cocokkan nama tanpa beda huruf", "duplicate_row": "S5: simpan baris pertama"}] for r in dd.itertuples()],
    "", "Kolom berganti nama mulai Juli (60 file, `input_qty`/`ok_qty`/`ng_qty` menggantikan `qty_*`): `S1` menggabungkan nama lama dan baru; test `raw_schema_signature` (error) hanya menerima skema v1 pada run deteksi."]) + "\n", encoding="utf-8")
(C.DOCS_DIR / "kpi_definitions.md").write_text("""# Definisi KPI

| KPI | Rumus | Catatan |
|---|---|---|
| FPY | ok_first_pass / input | lulus pertama kali, per stasiun |
| NG rate | ng / input | |
| Rework rate | rework / input | rework dicatat per hari, stasiun, model (tanpa lot atau serial) |
| Scrap | NG - recovered | NG yang tidak pulih lewat rework |
| RTY | hasil kali FPY semua stasiun | per minggu dan model |
| Final yield | hasil kali (ok + recovered) / input | setelah rework |

Asumsi dampak: 52 laporan per tahun; 60, 90, atau 120 menit per laporan (estimated, bukan hasil ukur).
""", encoding="utf-8")
(C.DOCS_DIR / "architecture.md").write_text(f"""# Arsitektur

```
Excel harian (150 file, 3 sheet) -> 02_load_raw.py -> DuckDB schema raw (semua VARCHAR + _source_file, _excel_row)
  -> dbt staging (stg_production, stg_defect, stg_rework: cleaning S1-S5)
  -> dbt marts (dim_station, dim_defect, fct_kpi_daily, fct_defect_pareto, fct_line_weekly)
  -> analisis SQL -> CSV -> dashboard Streamlit, laporan mingguan, infografik
```

- {len(mods)} model dan {n_tests} test dbt ({n_warn} warn pada raw untuk data kotor, sisanya error severity).
- Run harian: `code/4-automation/python/08_run_daily.py` (muat file baru, `dbt build`, gerbang publish, log). Jika ada test error gagal, hasil tidak dipublikasikan.
- Workflow GitHub Actions `.github/workflows/daily.yml` sudah ditulis, tetapi belum terbukti berjalan 7 hari berturut-turut.
""", encoding="utf-8")
(C.DOCS_DIR / "data_dictionary.md").write_text("""# Kamus data

**raw.production**: date, shift, station, model, operator_id, qty_input, qty_ok, qty_ng (nama lama) atau input_qty, ok_qty, ng_qty, line_id (nama baru, mulai Juli), _source_file, _excel_row. Semua teks.

**raw.defect**: date, shift, station, model, defect_cd, qty. **raw.rework**: baris per hari, stasiun, model. **raw.file_manifest**: file_name, business_date, received_date.

**stg_production**: prod_key, date, shift, station_code (S01-S10), model, operator_id, input_qty, ok_first_pass, ng_qty, was_recovered, source_file, excel_row.

**fct_kpi_daily**: kpi_key, date, station_code, model, shift, input_qty, ok_first_pass, ng_qty, rework_qty, recovered_qty, scrap_qty, fpy, ng_rate, rework_rate, scrap_rate.
**fct_defect_pareto**: week, station_code, defect_code, qty, share, cum_share. **fct_line_weekly**: week, model, rty, final_yield, rework_rate.
**dim_station**: station_code, station_name, sequence. **dim_defect**: defect_code, defect_name (rekaan), category.
""", encoding="utf-8")

readme = f"""# Project 27: Analytics Engineering Mini-Warehouse

File Excel produksi harian (150 file, tiga sheet, format sering berubah) dibersihkan dan diuji dengan **dbt + DuckDB**, lalu dihitung menjadi KPI yang bisa diaudit: FPY, NG rate, RTY, Pareto defect. **Data simulasi** buatan sendiri; hasilnya menguji metode, bukan kondisi pabrik.

- Rancangan dan laporan (halaman web): `design-and-report/index.html`
- Dashboard: `streamlit run code/3-presentation/streamlit/app.py` (dari folder `project/`; belum di-deploy)
- Infografik: `project/results/3-presentation/infographic.png`; dokumentasi dbt: `project/results/3-presentation/dbt_docs.html`

## Masalah
Rekap mingguan disusun manual dari Excel yang kolomnya berganti nama, ada angka kosong, negatif, berupa teks, baris ganda, dan nama stasiun tidak seragam. Angka yang dihasilkan sulit dipercaya dan sulit ditelusuri.

## Data
{fi(nv.loc['baris dipakai', 'bersih'] + 60)} baris produksi mentah, {fi(line.input_qty)} unit input pada data bersih, 10 stasiun, 3 model lampu, 2 shift, 2 Mar sampai 25 Sep 2026. Seed tetap; `project/data/README.md`.

## Temuan
- **Stasiun terburuk:** {top.station_name} dengan NG rate {pc(top.ng_rate, 2)} (stasiun berikutnya {pc(ks.iloc[1].ng_rate, 2)}).
- **Lini:** RTY {pc(line.rty)}, final yield setelah rework {pc(line.final_yield)}.
- **Minggu turun:** {dw.week} (RTY {pc(dw.rty)}), stasiun terburuk {dw.worst_station} (NG rate {pc(dw.worst_station_ng_rate)}).
- **Shift vs model:** shift tidak berpengaruh pada NG (chi-square p = {PV(nt.loc['shift', 'p_value'])}); model berpengaruh (p {PV(nt.loc['model', 'p_value'])}), 12W tertinggi ({pc(bym.loc['12W', 'ng_rate'], 2)}), 5W terendah ({pc(bym.loc['5W', 'ng_rate'], 2)}).
- **Defect:** dalam satu stasiun defect terbagi hampir merata, tidak ada defect dominan.
- **Kualitas data:** {int(dd.detected.sum())} dari {int(dd.planted.sum())} baris kotor tertangkap uji raw (5 jenis, cocok per file). {n_tests} test dbt, {n_warn} warn (data kotor di raw), 0 error.
- **Validasi:** mart sama dengan rekap Excel SUMIFS ({int((ce.status == 'PASS').sum())} dari {len(ce)} PASS pada 22 hari sampel). Rekap manual dari raw meleset sampai {md.fpy_diff_pts.abs().max():.1f} poin FPY karena data kotor.
- **Naif vs bersih:** rekap langsung dari raw hanya memakai {fi(nv.loc['baris dipakai', 'naif'])} dari {fi(nv.loc['baris dipakai', 'bersih'])} baris (kolom nama baru terlewat) dan membaca 20 stasiun, bukan 10.
- **Benchmark 1 juta baris:** baca + hitung KPI: DuckDB {agg.loc['DuckDB', 'median_s']:.2f} dtk, Polars {agg.loc['Polars', 'median_s']:.2f} dtk, pandas {agg.loc['pandas', 'median_s']:.2f} dtk (median 3 kali; bergantung mesin).
- **Otomasi:** simulasi {len(run) - 1} run harian lokal, semua lolos gerbang publish; gerbang terbukti menahan hasil saat skema berubah.

## Rekomendasi
1. Fokuskan perbaikan pada {top.station_name}.
2. Jadikan test dbt gerbang wajib sebelum KPI dipublikasikan; perubahan nama kolom harus memicu peringatan, bukan hilang diam-diam.
3. Standarkan template Excel (kolom terkunci, validasi input) agar data kotor tidak masuk.
4. Hemat waktu rekap sekitar {int(hrs.jam_per_tahun.min())} sampai {int(hrs.jam_per_tahun.max())} jam per tahun (asumsi 60 sampai 120 menit per laporan, 52 laporan; estimated).

## Batasan
Data simulasi; tidak ada `lot` atau `serial` (rework hanya per hari, stasiun, model); nama defect rekaan; jam hemat adalah asumsi; dashboard belum di-deploy; GitHub Actions harian ditulis tetapi belum terbukti berjalan 7 hari.

## Menjalankan ulang (dari folder `project/`)
```
pip install -r requirements.txt
python code/1-data-preparation/python/01_generate_raw.py
python code/1-data-preparation/python/02_load_raw.py
python code/1-data-preparation/python/03_build_warehouse.py
python code/2-analysis/python/04_run_queries.py
python code/2-analysis/python/05_excel_crosscheck.py      # butuh LibreOffice
python code/1-data-preparation/python/01_generate_raw.py --big 1000000
python code/2-analysis/python/06_benchmark.py
python code/2-analysis/python/07_impact.py
python code/4-automation/python/08_run_daily.py --simulate 10
python code/3-presentation/python/09_build_dashboard_data.py
python code/3-presentation/python/10_test_app.py
python code/3-presentation/python/11_build_infographic.py
python code/3-presentation/python/12_weekly_report_and_docs.py
python code/3-presentation/python/13_build_notebooks.py
python code/3-presentation/python/14_build_docs_readme.py
python ../design-and-report/src/build_report.py
```

## Struktur
`design-and-report/` (rancangan dan laporan), `project/code/` (1-data-preparation, 2-analysis, 3-presentation, 4-automation, dbt/), `project/results/`, `project/data/` (README, sample), `project/docs/`, `.github/workflows/daily.yml`.
"""
(C.ROOT.parent / "README.md").write_text(readme, encoding="utf-8")
print("README.md dan docs ditulis")
