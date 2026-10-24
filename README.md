[← Back to portfolio](https://bagusbernadi.github.io/)

# Project 27: Analytics Engineering Mini-Warehouse

**Status: Design (rancangan).** Halaman rancangan ada di [`index.html`](index.html). Model dbt, workflow, dashboard, dan angka hasil belum dikerjakan, sehingga bagian Analysis, Recommendation, dan Impact di bawah masih kosong.

**Tujuan:** membangun mini data warehouse yang mengubah file produksi harian menjadi KPI yield, NG rate, dan rework rate yang konsisten, teruji, dan ter-update otomatis setiap hari, sehingga laporan tidak lagi disusun dengan copy-paste dan setiap angka bisa dilacak asalnya.

| | |
|---|---|
| Kategori | Manufaktur (pabrik lampu LED) |
| Tingkat | Lanjut |
| Data | Simulasi: file produksi, NG, dan rework harian (generator disertakan) |
| Tools | dbt-duckdb, DuckDB + SQL, GitHub Actions, Python (Polars, pandas), Streamlit + Plotly, Quarto (opsional) |

## 1. Problem

**Pertanyaan utama:** Bagaimana membuat KPI produksi (yield, NG rate, rework rate per stasiun dan shift) yang konsisten, teruji, dan ter-update otomatis tanpa copy-paste Excel setiap minggu?

Rancangan memecahnya menjadi 14 pertanyaan (9 Utama, 4 Pendukung, 1 Tambahan) dalam 6 tema: KPI, defect dan tren, kualitas data, otomasi, dampak, dan validitas.

## 2. Data

- Sumber: data simulasi buatan sendiri, dibuat oleh `scripts/generate_raw.py` (Versi: v1, rancangan; Tanggal dibuat: saat Tahap B dikerjakan). Tidak memakai dataset publik atau data perusahaan.
- Konteks: 10 stasiun produksi lampu LED, 3 model (5W, 9W, 12W), 2 shift, ±20 operator.
- Ukuran (perkiraan): ±150 file harian (6 bulan); ±9.000 baris produksi, ±15.000 baris defect. Untuk benchmark, data diperbesar menjadi ±1 juta baris.
- Rencana model dbt: 3 staging (`stg_production`, `stg_defect`, `stg_rework`), 2 dimensi (`dim_station`, `dim_defect`), 3 fakta (`fct_kpi_daily`, `fct_defect_pareto`, `fct_line_weekly`).
- Fakta yang sengaja ditanam: Burn-in Test paling sering NG, lonjakan NG Photometric Test ±1 minggu, perubahan kolom file mentah di bulan ke-4, satu file terlambat 2 hari, dan 2–3% data kotor.

## 3. Analysis

Belum dikerjakan. Setiap run harian: muat raw → staging → mart → data tests. Dashboard dan laporan hanya diperbarui jika semua test lulus. KPI mart dicek silang dengan Excel.

## 4. Recommendation

Belum dikerjakan. Output yang direncanakan: stasiun dan defect prioritas dari mart KPI, serta rekomendasi aturan data tests untuk file produksi.

## 5. Impact

Belum dikerjakan. Rumus yang akan dipakai (semua hasil diberi label `estimated` dan `simulated`):

```
Jam dihemat per tahun = jumlah laporan per tahun × menit penyusunan manual per laporan ÷ 60
```

## Batasan yang sudah diketahui

- Data tests hanya menangkap aturan yang ditulis.
- Jadwal GitHub Actions bisa terlambat, dan workflow terjadwal berhenti jika repositori lama tidak aktif.
- Hasil benchmark bergantung pada mesin yang dipakai.
- Pola belum tentu penyebab; pengujian penyebab dikerjakan di Project 29.

## Struktur repository

```
index.html   Halaman rancangan project (bisa dibuka di browser atau lewat GitHub Pages)
README.md    Dokumen ini
```

Folder `docs/`, `dbt/`, `.github/workflows/`, `data/`, `scripts/`, `notebooks/`, `dashboard/`, `reports/`, dan `outputs/` ditambahkan saat pengerjaan dimulai.
