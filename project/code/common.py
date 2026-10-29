"""Pengaturan bersama untuk semua skrip Project 27. Semua jalur relatif terhadap folder project/."""
import os
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent          # folder project/
CODE = ROOT / "code"
DATA = ROOT / "data"
RAW_DIR = DATA / "raw"                                 # file mentah simulasi (tidak di-commit)
DAILY_DIR = RAW_DIR / "daily"                          # 150 file Excel harian
SAMPLE_DIR = DATA / "sample"                           # contoh kecil yang di-commit (3 file harian dan catatan)
DB_PATH = Path(os.environ.get("WAREHOUSE_PATH", ROOT / "warehouse.duckdb"))   # database hasil dbt (tidak di-commit); bisa ditimpa lewat env
DBT_DIR = CODE / "dbt"                                 # project dbt (satu folder karena dbt butuh satu project)
RES_PREP = ROOT / "results" / "1-data-preparation"
RES_ANALYSIS = ROOT / "results" / "2-analysis"
RES_PRESENT = ROOT / "results" / "3-presentation"
RES_AUTO = ROOT / "results" / "4-automation"
DOCS_DIR = ROOT / "docs"
for _d in (RAW_DIR, SAMPLE_DIR, RES_PREP, RES_ANALYSIS, RES_PRESENT, RES_AUTO, DOCS_DIR):
    _d.mkdir(parents=True, exist_ok=True)

SEED, DATA_VERSION, DATA_DATE = 27260302, "v1", "28 Okt 2026"
# Definisi dan asumsi (lihat docs/kpi_definitions.md)
REPORTS_PER_YEAR = 52                                  # laporan mingguan per tahun (asumsi)
MANUAL_MIN_PER_REPORT = 90                             # menit penyusunan manual per laporan (asumsi, estimated)
MANUAL_MIN_SCENARIOS = [60, 90, 120]
BENCH_ROWS = 1_000_000
BENCH_REPEATS = 3
FRESHNESS_WARN_DAYS = 1                                # file terlambat lebih dari 1 hari kerja memberi peringatan


def result(name):
    """Cari CSV hasil di folder hasil per tahap."""
    for d in (RES_PREP, RES_ANALYSIS, RES_PRESENT, RES_AUTO):
        p = d / name
        if p.exists():
            return p
    raise FileNotFoundError(name)
