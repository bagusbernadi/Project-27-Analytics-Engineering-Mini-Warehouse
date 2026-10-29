"""Langkah 13: data ringkas untuk dashboard, diambil dari mart dbt. Di-commit supaya dashboard jalan tanpa database.
Keluaran (results/3-presentation): dash_kpi_daily.csv (hari x stasiun x model), dash_pareto.csv (minggu x stasiun x defect),
dash_line_weekly.csv, dash_data_status.csv (hasil uji dbt per lapisan dan status kesegaran file)."""
import sys
from pathlib import Path

import duckdb
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
import common as C  # noqa: E402

con = duckdb.connect(str(C.DB_PATH), read_only=True)
k = con.execute("""SELECT f.date::VARCHAR AS date, f.station_code, s.station_name, s.sequence, f.model, sum(input_qty) AS input_qty, sum(ok_first_pass) AS ok_first_pass,
                          sum(ng_qty) AS ng_qty, sum(rework_qty) AS rework_qty, sum(recovered_qty) AS recovered_qty, sum(scrap_qty) AS scrap_qty
                   FROM fct_kpi_daily f JOIN dim_station s USING (station_code) GROUP BY ALL ORDER BY ALL""").df()
p = con.execute("""SELECT p.week::VARCHAR AS week, p.station_code, d.defect_code, d.defect_name, d.category, p.qty
                   FROM fct_defect_pareto p JOIN dim_defect d USING (defect_code) ORDER BY ALL""").df()
w = con.execute("SELECT week::VARCHAR AS week, model, rty, final_yield, rework_rate FROM fct_line_weekly ORDER BY ALL").df()
t = pd.read_csv(C.RES_PREP / "dbt_test_results.csv")
st = t.groupby(["layer", "status"]).size().rename("jumlah").reset_index()
k.to_csv(C.RES_PRESENT / "dash_kpi_daily.csv", index=False); p.to_csv(C.RES_PRESENT / "dash_pareto.csv", index=False)
w.to_csv(C.RES_PRESENT / "dash_line_weekly.csv", index=False); st.to_csv(C.RES_PRESENT / "dash_data_status.csv", index=False)
assert k.input_qty.sum() == 4199497 and k.ng_qty.sum() == 42832
print(len(k), len(p), len(w), len(st))
