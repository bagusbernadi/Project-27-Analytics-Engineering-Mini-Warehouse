# Arsitektur

```
Excel harian (150 file, 3 sheet) -> 02_load_raw.py -> DuckDB schema raw (semua VARCHAR + _source_file, _excel_row)
  -> dbt staging (stg_production, stg_defect, stg_rework: cleaning S1-S5)
  -> dbt marts (dim_station, dim_defect, fct_kpi_daily, fct_defect_pareto, fct_line_weekly)
  -> analisis SQL -> CSV -> dashboard Streamlit, laporan mingguan, infografik
```

- 8 model dan 60 test dbt (6 warn pada raw untuk data kotor, sisanya error severity).
- Run harian: `code/4-automation/python/08_run_daily.py` (muat file baru, `dbt build`, gerbang publish, log). Jika ada test error gagal, hasil tidak dipublikasikan.
- Workflow GitHub Actions `.github/workflows/daily.yml` sudah ditulis, tetapi belum terbukti berjalan 7 hari berturut-turut.
