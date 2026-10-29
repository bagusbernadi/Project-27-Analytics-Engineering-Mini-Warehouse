"""Dashboard Streamlit (4 halaman): Ringkasan, Yield per Stasiun, Pareto Defect, Status Data.
Jalankan dari folder project/:  streamlit run code/3-presentation/streamlit/app.py
Membaca CSV yang di-commit di results/ (tanpa database). Semua data adalah simulasi buatan sendiri."""
from pathlib import Path

import pandas as pd
import plotly.graph_objects as go
import streamlit as st

ROOT = Path(__file__).resolve().parents[3]
RES = ROOT / "results"
BLUE, ORANGE, GREY = "#1A73E8", "#E8710A", "#9AA0A6"
st.set_page_config(page_title="Project 27: Mini-Warehouse LED", layout="wide")


@st.cache_data
def load():
    r = lambda d, f: pd.read_csv(RES / d / f)
    return dict(k=r("3-presentation", "dash_kpi_daily.csv"), p=r("3-presentation", "dash_pareto.csv"), w=r("3-presentation", "dash_line_weekly.csv"),
                s=r("3-presentation", "dash_data_status.csv"), drop=r("2-analysis", "drop_weeks.csv"), run=r("4-automation", "run_log.csv"))


D = load()
page = st.sidebar.radio("Halaman", ["1. Ringkasan", "2. Yield per Stasiun", "3. Pareto Defect", "4. Status Data"])
models = st.sidebar.multiselect("Model lampu", ["5W", "9W", "12W"], default=["5W", "9W", "12W"])
st.sidebar.caption("Data simulasi buatan sendiri.")
if not models:
    st.warning("Pilih minimal satu model."); st.stop()
k = D["k"][D["k"].model.isin(models)]
w = D["w"][D["w"].model.isin(models)]
st.title("Project 27: Mini-Warehouse Produksi Lampu LED")
st.caption("150 file Excel harian dibersihkan dan diuji dengan dbt, lalu dihitung menjadi KPI mingguan. Data simulasi 2 Mar–25 Sep 2026.")

if page.startswith("1"):
    i, ng, ok = k.input_qty.sum(), k.ng_qty.sum(), k.ok_first_pass.sum()
    c = st.columns(4)
    c[0].metric("FPY (lulus pertama kali)", f"{ok / i:.2%}".replace(".", ","))
    c[1].metric("NG rate", f"{ng / i:.2%}".replace(".", ","))
    c[2].metric("Scrap rate", f"{k.scrap_qty.sum() / i:.2%}".replace(".", ","))
    c[3].metric("Input total (unit)", f"{int(i):,}".replace(",", "."))
    g = w.groupby("week")[["rty", "final_yield"]].mean().reset_index()
    f = go.Figure([go.Scatter(x=g.week, y=g.rty, name="RTY", line=dict(color=BLUE)), go.Scatter(x=g.week, y=g.final_yield, name="Final yield", line=dict(color=GREY))])
    dw = D["drop"][D["drop"].is_drop]
    for r in dw.itertuples():
        f.add_annotation(x=r.week, y=g.set_index("week").rty.get(r.week, None), text=f"turun, stasiun {r.worst_station}", showarrow=True, arrowhead=2)
    f.update_layout(title="RTY dan final yield per minggu (rata-rata antar model)", yaxis_tickformat=".0%", height=400, margin=dict(t=50))
    st.plotly_chart(f, width="stretch")
elif page.startswith("2"):
    s = k.groupby(["sequence", "station_name"])[["input_qty", "ok_first_pass", "ng_qty"]].sum().reset_index()
    s["fpy"] = s.ok_first_pass / s.input_qty; s["ng_rate"] = s.ng_qty / s.input_qty
    f = go.Figure(go.Bar(x=s.station_name, y=s.ng_rate, marker_color=[ORANGE if v == s.ng_rate.max() else BLUE for v in s.ng_rate],
                         text=(s.ng_rate * 100).round(2).astype(str) + "%", textposition="outside"))
    f.update_layout(title="NG rate per stasiun (urut proses)", yaxis_tickformat=".1%", height=400, margin=dict(t=50))
    st.plotly_chart(f, width="stretch")
    st.dataframe(s.rename(columns={"station_name": "stasiun", "input_qty": "input", "ok_first_pass": "ok pertama", "ng_qty": "NG"}).drop(columns="sequence").round(4), hide_index=True)
if page.startswith("3"):
    p = D["p"]
    stn = st.selectbox("Stasiun", sorted(p.station_code.unique()))
    d = p[p.station_code == stn].groupby(["defect_name"]).qty.sum().sort_values(ascending=False).reset_index()
    d["cum"] = d.qty.cumsum() / d.qty.sum()
    f = go.Figure([go.Bar(x=d.defect_name, y=d.qty, marker_color=BLUE, name="jumlah"), go.Scatter(x=d.defect_name, y=d.cum, yaxis="y2", name="kumulatif", line=dict(color=ORANGE))])
    f.update_layout(title=f"Pareto defect, stasiun {stn}", yaxis2=dict(overlaying="y", side="right", tickformat=".0%", range=[0, 1.05]), height=420, margin=dict(t=50))
    st.plotly_chart(f, width="stretch")
    st.caption("Nama defect adalah rekaan. Pada data simulasi ini defect dalam satu stasiun terbagi hampir merata, jadi tidak ada satu defect dominan.")
if page.startswith("4"):
    st.subheader("Hasil uji dbt per lapisan")
    st.dataframe(D["s"].rename(columns={"layer": "lapisan", "status": "status"}), hide_index=True)
    st.subheader("Log run harian (simulasi 10 hari)")
    st.dataframe(D["run"], hide_index=True)
    st.caption("Uji lapisan raw berstatus warn: data kotor dicatat, tidak menghentikan pipeline. Uji mart berstatus error: gagal berarti hasil tidak dipublikasikan.")
