# Data simulasi

- Versi data: v1
- Tanggal dibuat: 28 Okt 2026
- Seed: 27260302
- Data tidak disimpan di repo. Dibuat ulang (hasil identik) dengan:

```
pip install numpy pandas openpyxl Faker reportlab Pillow   # sesuai impor skrip
python code/1-data-preparation/python/01_generate_raw.py      # dari folder project/
```

- Hasil di `data/raw/`: 150 file Excel harian (3 sheet), `file_manifest.csv`, `truth_*.csv`, `ground_truth_dirty.csv` (9.000 baris produksi, 15.999 baris defect).
- Uji determinisme: dijalankan 2x, SHA-256 semua berkas identik. Daftar hash ada di repo DataCenter, `simulasi/fingerprints/project-27.sha256`.

- `data/sample/`: 3 file harian contoh (2 Mar skema lama, 6 Jul skema baru, 20 Mei file terlambat), `file_manifest.csv`, `ground_truth_dirty.csv`, `ground_truth.json`.
- Opsi `--big 1000000` membuat `benchmark_production.csv` untuk benchmark (tidak di-commit, tidak ikut perbandingan hash).
