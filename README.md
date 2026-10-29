# Project 27: Analytics Engineering Mini-Warehouse

File Excel produksi harian (150 file, tiga sheet, format sering berubah) dibersihkan dan diuji dengan **dbt + DuckDB**, lalu dihitung menjadi KPI yang bisa diaudit: FPY, NG rate, RTY, Pareto defect. **Data simulasi** buatan sendiri; hasilnya menguji metode, bukan kondisi pabrik.

- Rancangan dan laporan (halaman web): `design-and-report/index.html`
- Dashboard: `streamlit run code/3-presentation/streamlit/app.py` (dari folder `project/`; belum di-deploy)
- Infografik: `project/results/3-presentation/infographic.png`; dokumentasi dbt: `project/results/3-presentation/dbt_docs.html`

## Masalah
Rekap mingguan disusun manual dari Excel yang kolomnya berganti nama, ada angka kosong, negatif, berupa teks, baris ganda, dan nama stasiun tidak seragam. Angka yang dihasilkan sulit dipercaya dan sulit ditelusuri.

## Data
9.060 baris produksi mentah, 4.199.497 unit input pada data bersih, 10 stasiun, 3 model lampu, 2 shift, 2 Mar sampai 25 Sep 2026. Seed tetap; `project/data/README.md`.

## Temuan
- **Stasiun terburuk:** Burn-in Test dengan NG rate 3,70% (stasiun berikutnya 1,35%).
- **Lini:** RTY 90,2%, final yield setelah rework 93,7%.
- **Minggu turun:** 2026-06-08 (RTY 86,9%), stasiun terburuk S08 (NG rate 4,7%).
- **Shift vs model:** shift tidak berpengaruh pada NG (chi-square p = 0,76); model berpengaruh (p < 0,001), 12W tertinggi (1,17%), 5W terendah (0,91%).
- **Defect:** dalam satu stasiun defect terbagi hampir merata, tidak ada defect dominan.
- **Kualitas data:** 300 dari 300 baris kotor tertangkap uji raw (5 jenis, cocok per file). 60 test dbt, 6 warn (data kotor di raw), 0 error.
- **Validasi:** mart sama dengan rekap Excel SUMIFS (300 dari 300 PASS pada 22 hari sampel). Rekap manual dari raw meleset sampai 2.5 poin FPY karena data kotor.
- **Naif vs bersih:** rekap langsung dari raw hanya memakai 5.400 dari 9.000 baris (kolom nama baru terlewat) dan membaca 20 stasiun, bukan 10.
- **Benchmark 1 juta baris:** baca + hitung KPI: DuckDB 0.22 dtk, Polars 0.26 dtk, pandas 0.67 dtk (median 3 kali; bergantung mesin).
- **Otomasi:** simulasi 10 run harian lokal, semua lolos gerbang publish; gerbang terbukti menahan hasil saat skema berubah.

## Rekomendasi
1. Fokuskan perbaikan pada Burn-in Test.
2. Jadikan test dbt gerbang wajib sebelum KPI dipublikasikan; perubahan nama kolom harus memicu peringatan, bukan hilang diam-diam.
3. Standarkan template Excel (kolom terkunci, validasi input) agar data kotor tidak masuk.
4. Hemat waktu rekap sekitar 52 sampai 104 jam per tahun (asumsi 60 sampai 120 menit per laporan, 52 laporan; estimated).

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
