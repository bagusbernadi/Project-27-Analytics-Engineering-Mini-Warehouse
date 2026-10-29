"""Langkah 11-12 (Q11, Q12): dampak penghematan jam dan selisih KPI 'naif' (tanpa uji) vs 'bersih' (dbt + uji).
Naif = rekap langsung dari raw: hanya kolom nama lama, TRY_CAST, nama stasiun apa adanya, tanpa dedupe, tanpa pemulihan NG.
Bersih = mart dbt. Jam hemat = skenario menit per laporan x 52 laporan per tahun (asumsi, bukan hasil ukur).
Keluaran: results/2-analysis/impact_hours.csv, impact_naive_vs_clean.csv, impact_naive_by_station.csv."""
import sys
from pathlib import Path

import duckdb
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
import common as C  # noqa: E402

pd.DataFrame([dict(menit_per_laporan=m, laporan_per_tahun=C.REPORTS_PER_YEAR, jam_per_tahun=round(m * C.REPORTS_PER_YEAR / 60, 1),
                   dasar="asumsi (estimated)") for m in C.MANUAL_MIN_SCENARIOS]).to_csv(C.RES_ANALYSIS / "impact_hours.csv", index=False)

con = duckdb.connect(str(C.DB_PATH), read_only=True)
con.execute("""CREATE TEMP VIEW naive AS SELECT station AS station_name, try_cast(qty_input AS DOUBLE) AS i, try_cast(qty_ok AS DOUBLE) AS ok, try_cast(qty_ng AS DOUBLE) AS ng
               FROM raw.production WHERE qty_input IS NOT NULL""")
n = con.execute("SELECT count(*) rows_used, sum(i) input_qty, sum(ng) ng, sum(ok) ok FROM naive WHERE i IS NOT NULL").df().iloc[0]
cl = con.execute("SELECT sum(input_qty) input_qty, sum(ng_qty) ng, sum(ok_first_pass) ok, count(*) rows_used FROM fct_kpi_daily").df().iloc[0]
raw_rows = con.execute("SELECT count(*) FROM raw.production").fetchone()[0]
rows = [dict(metrik="baris dipakai", naif=n.rows_used, bersih=cl.rows_used, keterangan=f"raw {raw_rows} baris; mart per hari x stasiun x model x shift"),
        dict(metrik="input_qty total", naif=n.input_qty, bersih=cl.input_qty, keterangan=""),
        dict(metrik="NG total", naif=n.ng, bersih=cl.ng, keterangan=""),
        dict(metrik="NG rate", naif=n.ng / n.input_qty, bersih=cl.ng / cl.input_qty, keterangan=""),
        dict(metrik="FPY", naif=n.ok / n.input_qty, bersih=cl.ok / cl.input_qty, keterangan="FPY = ok_first_pass / input")]
pd.DataFrame(rows).to_csv(C.RES_ANALYSIS / "impact_naive_vs_clean.csv", index=False)

bs = con.execute("""WITH nv AS (SELECT station_name, sum(i) i, sum(ok) ok FROM naive WHERE i IS NOT NULL GROUP BY 1),
                   cl AS (SELECT s.station_name, sum(f.ok_first_pass)*1.0/sum(f.input_qty) fpy_bersih FROM fct_kpi_daily f JOIN dim_station s USING (station_code) GROUP BY 1)
                   SELECT coalesce(cl.station_name, nv.station_name) station, nv.ok/nv.i fpy_naif, cl.fpy_bersih, nv.ok/nv.i - cl.fpy_bersih selisih
                   FROM nv FULL JOIN cl ON nv.station_name = cl.station_name ORDER BY 1""").df()
bs.to_csv(C.RES_ANALYSIS / "impact_naive_by_station.csv", index=False)
print(pd.DataFrame(rows).to_string(index=False)); print(bs.round(4).to_string(index=False))
