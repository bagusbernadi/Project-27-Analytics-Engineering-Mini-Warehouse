"""Uji dashboard dengan Streamlit AppTest: tiap halaman terbuka tanpa error dan angka ringkasan cocok dengan CSV. Keluaran: results/3-presentation/app_test.csv"""
import sys
from pathlib import Path

import pandas as pd
from streamlit.testing.v1 import AppTest

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
import common as C  # noqa: E402

rows = []
for pg in ["1. Ringkasan", "2. Yield per Stasiun", "3. Pareto Defect", "4. Status Data"]:
    at = AppTest.from_file(str(C.CODE / "3-presentation" / "streamlit" / "app.py"), default_timeout=60).run()
    at.sidebar.radio[0].set_value(pg).run()
    rows.append(dict(halaman=pg, exception=len(at.exception), n_metric=len(at.metric), n_dataframe=len(at.dataframe)))
at = AppTest.from_file(str(C.CODE / "3-presentation" / "streamlit" / "app.py"), default_timeout=60).run()
k = pd.read_csv(C.RES_PRESENT / "dash_kpi_daily.csv")
exp = f"{k.ok_first_pass.sum() / k.input_qty.sum():.2%}".replace(".", ",")
rows.append(dict(halaman="angka FPY cocok CSV", exception=0, n_metric=int(at.metric[0].value == exp), n_dataframe=0))
df = pd.DataFrame(rows); df.to_csv(C.RES_PRESENT / "app_test.csv", index=False)
assert df.exception.sum() == 0 and df.iloc[-1].n_metric == 1, df
print(df.to_string(index=False))
