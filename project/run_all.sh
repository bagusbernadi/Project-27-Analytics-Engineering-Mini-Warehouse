#!/usr/bin/env bash
# Menjalankan seluruh pipeline P27 dari nol (dari folder project/). Butuh LibreOffice untuk langkah 05.
set -euo pipefail
P=code
python $P/1-data-preparation/python/01_generate_raw.py
python $P/1-data-preparation/python/02_load_raw.py
python $P/1-data-preparation/python/03_build_warehouse.py
python $P/2-analysis/python/04_run_queries.py
python $P/2-analysis/python/05_excel_crosscheck.py
[ -f data/raw/benchmark_production.csv ] || python $P/1-data-preparation/python/01_generate_raw.py --big 1000000
python $P/2-analysis/python/06_benchmark.py
python $P/2-analysis/python/07_impact.py
python $P/4-automation/python/08_run_daily.py --simulate 10
python $P/4-automation/python/09_rebuild_check.py
python $P/3-presentation/python/09_build_dashboard_data.py
python $P/3-presentation/python/10_test_app.py
python $P/3-presentation/python/11_build_infographic.py
python $P/3-presentation/python/12_weekly_report_and_docs.py
python $P/3-presentation/python/13_build_notebooks.py
python $P/3-presentation/python/14_build_docs_readme.py
python ../design-and-report/src/build_report.py
