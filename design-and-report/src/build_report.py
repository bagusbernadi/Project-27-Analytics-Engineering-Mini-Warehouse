"""Membuat design-and-report/index.html (Report Project versi 2) dari page_v1.html dan CSV hasil.

- Pane Design diambil apa adanya dari page_v1.html (dicek identik).
- Semua angka di Report berasal dari project/results/*.csv lewat helper I/D/P/cs (report_lib.py) dan diaudit di akhir.
Jalankan dari folder mana saja:  python design-and-report/src/build_report.py
"""
import re
import sys
from pathlib import Path

import pandas as pd

HERE = Path(__file__).resolve().parent
REPO = HERE.parents[1]
sys.path.insert(0, str(REPO / "project" / "code"))
sys.path.insert(0, str(HERE))
from common import RES_ANALYSIS, RES_AUTO, RES_PREP, RES_PRESENT, result  # noqa: E402
from report_lib import (BLUE, D, cs, GREY, HI, I, NO, OK, P, PART, SOFT, audit, bars, esc, gbars, hbars,  # noqa: E402
                        legend, lines, qa, table)

R = lambda n: pd.read_csv(result(n))
PRIO = {1: "Utama", 2: "Utama", 3: "Utama", 4: "Pendukung", 5: "Utama", 6: "Utama", 7: "Pendukung", 8: "Utama", 9: "Pendukung", 10: "Pendukung", 11: "Utama", 12: "Tambahan", 13: "Utama", 14: "Utama"}
QT = {1: "Berapa yield, NG rate, dan rework rate per stasiun, shift, dan hari jika semuanya dihitung dengan satu definisi?",
      2: "Apakah KPI dari mart sama dengan rekap Excel manual, dan jika berbeda, apa penyebabnya?",
      3: "Jenis defect apa yang menyumbang sekitar 80% NG di tiap stasiun?",
      4: "Shift dan model mana yang NG rate-nya paling tinggi?",
      5: "Bagaimana tren yield mingguan, dan kapan terjadi penurunan?",
      6: "Berapa persen baris yang gagal data tests, dan test mana yang paling sering gagal?",
      7: "Apakah file yang terlambat masuk dan perubahan kolom di file mentah terdeteksi?",
      8: "Apakah pipeline berjalan otomatis setiap hari tanpa campur tangan, dan berapa lama satu kali jalan?",
      9: "Seberapa cepat Polars dan DuckDB dibanding pandas untuk data berukuran besar?",
      10: "Dari file dan model mana setiap angka di dashboard berasal?",
      11: "Berapa jam penyusunan laporan manual yang dihemat per tahun?",
      12: "Berapa poin yield yang \"salah terlapor\" jika data kotor tidak dicegat test?",
      13: "Apakah semua kejadian yang sengaja ditanam terdeteksi oleh test atau oleh analisis?",
      14: "Apakah hasilnya sama persis jika seluruh pipeline dibangun ulang dari nol?"}
WARN = set()


def Q(n, ans, warn=False):
    if warn:
        WARN.add(n)
    return qa(f"Q{n}", QT[n], PRIO[n], ans, "Terjawab dengan catatan" if warn else "Terjawab", warn)


mk = lambda *a: "".join(a)
pv = lambda p: "&lt; 0,001" if p < 0.001 else D(p, 2)
card = lambda title, body: f'<div class="card"><h4>{title}</h4>{body}</div>'

# ---------------------------------------------------------------- data
ks, kl = R("kpi_station.csv").sort_values("sequence"), R("kpi_line_total.csv").iloc[0]
ksm = R("kpi_station_shift_model.csv")
dd, ev, drift = R("dirty_detection.csv"), R("event_detection.csv"), R("schema_drift_check.csv")
tests, mods = R("dbt_test_results.csv"), R("dbt_model_results.csv")
cxl, cmd, cmc = R("crosscheck_excel.csv"), R("crosscheck_manual_diff.csv"), R("crosscheck_manual_causes.csv")
par, p80 = R("defect_pareto_station.csv"), R("pareto_80.csv")
ngt, ngm, ngs, ngsm = R("ng_tests.csv").set_index("factor"), R("ng_by_model.csv").set_index("model"), R("ng_by_shift.csv").set_index("shift"), R("ng_shift_model.csv")
tw, dw, sp, swf, tl = R("trend_weekly.csv"), R("drop_weeks.csv"), R("spike_detection.csv"), R("station_week_fpy.csv"), R("trend_line_weekly_model.csv")
hrs, nvc, nvs = R("impact_hours.csv"), R("impact_naive_vs_clean.csv").set_index("metrik"), R("impact_naive_by_station.csv")
bm, bme = R("benchmark.csv"), R("benchmark_env.csv").iloc[0]
rl, rt, gt, rb = R("run_log.csv"), R("run_timing_daily.csv"), R("gate_test.csv").iloc[0], R("rebuild_check.csv")
lin, apt, ds = R("lineage.csv"), R("app_test.csv"), R("dash_data_status.csv")
dashk = R("dash_kpi_daily.csv")

nraw = int(nvc.loc["baris dipakai", "bersih"] + dd.loc[dd.dirty_type == "duplicate_row", "planted"].iloc[0])
n_tests, n_warn, n_pass = len(tests), int((tests.status == "warn").sum()), int((tests.status == "pass").sum())
n_err = int(tests.status.isin(["fail", "error"]).sum())
dw1 = dw[dw.is_drop].iloc[0]
spk = sp[sp.is_spike]
top = ks.sort_values("ng_rate", ascending=False).iloc[0]
sec = ks.sort_values("ng_rate", ascending=False).iloc[1]
agg = bm[bm.task == "baca + agregasi KPI"].set_index("engine")
rdo = bm[bm.task == "baca CSV saja"].set_index("engine")
n_late = int(ev.loc[ev.fact_no == 4, "temuan"].iloc[0].split()[0])
late_file = re.search(r"produksi_\d+\.xlsx", ev.loc[ev.fact_no == 4, "temuan"].iloc[0]).group(0)
n_drift_files = drift.file_name.nunique()
inc = rl[rl.jenis == "inkremental"]
assert (ev.hasil == "Sesuai").all() and (dd.detected == dd.planted).all() and dd.exact_per_file.all() and n_err == 0
assert (cxl.status == "PASS").all() and rb.sama.all() and (rl.gerbang == "publish").all() and (apt.exception == 0).all()
assert top.station_code == "S07" and dw1.worst_station == "S08" and gt.hasil == "tahan (tidak dipublikasikan)"

# ---------------------------------------------------------------- 1. data
kp = lambda c, v, l, d: f'<div class="card kpi" style="--h:var(--{c}H)"><span class="v">{v}</span><span class="l">{l}</span><span class="d">{d}</span></div>'
rp1 = mk('<div class="kpis">',
         kp("navy", I(150), "file Excel harian", "Tiga sheet per file (production, defect, rework), satu file per hari kerja, 2 Mar sampai 25 Sep 2026."),
         kp("amber", I(nraw), "baris produksi mentah", f"{I(nvc.loc['baris dipakai', 'bersih'])} baris bersih ditambah {I(dd.planted.iloc[4])} baris ganda yang dibuang."),
         kp("teal", I(kl.input_qty), "unit input (data bersih)", "10 stasiun, 3 model lampu, 2 shift."),
         kp("plum", I(len(mods)), "model dbt", f"{I((mods.model.str.startswith('stg_')).sum())} staging, {I(mods.model.str.startswith('dim_').sum())} dimensi, {I(mods.model.str.startswith('fct_').sum())} fakta."),
         kp("rose", f"{I(dd.detected.sum())} / {I(dd.planted.sum())}", "baris kotor tertangkap", "Lima jenis data kotor, dicocokkan per file dengan yang ditanam."),
         kp("sky", I(n_tests), "data test dbt", f"{I(n_pass)} lulus, {I(n_warn)} peringatan (data kotor di raw), {I(n_err)} gagal."),
         '</div><h3>1.1 Data simulasi (mentah dan bersih)</h3>')
rp1 += card("Tabel 1.1a. Jumlah baris per lapisan (database <code>warehouse.duckdb</code>)", table(
    ["Lapisan", "Tabel atau model", "Baris", "Isi"],
    [["raw", "<code>raw.production</code>", I(nraw), "Semua kolom teks apa adanya, ditambah file asal dan nomor baris Excel"],
     ["staging", "<code>stg_production</code>", I(mods.set_index("model").loc["stg_production", "rows"]), "Satu baris per hari, shift, stasiun, model; sudah dibersihkan"],
     ["staging", "<code>stg_defect</code>", I(mods.set_index("model").loc["stg_defect", "rows"]), "Jumlah satu jenis defect per hari, shift, stasiun, model"],
     ["staging", "<code>stg_rework</code>", I(mods.set_index("model").loc["stg_rework", "rows"]), "Rework per hari, stasiun, model (tanpa lot atau serial)"],
     ["mart", "<code>fct_kpi_daily</code>", I(mods.set_index("model").loc["fct_kpi_daily", "rows"]), "FPY, NG rate, rework rate, scrap rate per hari, stasiun, model, shift"],
     ["mart", "<code>fct_defect_pareto</code>", I(mods.set_index("model").loc["fct_defect_pareto", "rows"]), "Defect per minggu dan stasiun dengan kontribusi kumulatif"],
     ["mart", "<code>fct_line_weekly</code>", I(mods.set_index("model").loc["fct_line_weekly", "rows"]), "RTY, final yield, rework rate lini per minggu dan model"],
     ["mart", "<code>dim_station</code>, <code>dim_defect</code>", f"{I(mods.set_index('model').loc['dim_station', 'rows'])} dan {I(mods.set_index('model').loc['dim_defect', 'rows'])}", "Tabel referensi stasiun dan kode defect"]]) +
    "<p>Data dibuat oleh generator dengan seed tetap, dan isinya sama setiap dijalankan (dicek lewat sidik jari SHA-256 di registri DataCenter).</p>")
LAB = {"blank_qty": "NG kosong", "negative_qty": "NG negatif", "text_qty": "Jumlah input berupa teks", "lowercase_station": "Nama stasiun huruf kecil", "duplicate_row": "Baris ganda"}
rp1 += card("Tabel 1.1b. Data kotor yang ditanam dan yang tertangkap (Q6, Q13)", table(
    ["Jenis data kotor", "Test raw yang menangkap", "Ditanam", "Tertangkap", "File cocok"],
    [[LAB[r.dirty_type], f"<code>{r.test}</code>", I(r.planted), I(r.detected), f"{I(r.files_detected)} dari {I(r.files_planted)}"] for r in dd.itertuples()]) +
    f"<p>Total {I(dd.planted.sum())} baris kotor dari {I(nraw)} baris mentah ({D(dd.planted.sum() / nraw * 100, 1)}%). Semua ditangani di lapisan staging dengan aturan yang tercatat (<code>docs/cleaning_log.md</code>).</p>")
FILES = {"dbt_model_results": ("Status dan jumlah baris tiap model dbt", "Q6"), "dbt_test_results": ("Status tiap data test dbt", "Q6"), "dirty_detection": ("Data kotor ditanam vs tertangkap", "Q6, Q13"),
         "event_detection": ("Lima fakta yang ditanam vs temuan", "Q13"), "run_timing": ("Durasi dbt build (bergantung mesin)", "Q8"), "schema_drift_check": ("Kolom tiap sheet tiap file yang berubah", "Q7"),
         "benchmark": ("Waktu pandas, Polars, DuckDB pada 1 juta baris", "Q9"), "benchmark_env": ("Mesin dan versi library benchmark", "Q9"), "crosscheck_excel": ("Mart vs rekap Excel SUMIFS", "Q2"),
         "crosscheck_manual_causes": ("Penyebab selisih rekap manual", "Q2"), "crosscheck_manual_diff": ("Selisih rekap manual dari raw vs mart", "Q2"), "defect_pareto_station": ("Pareto defect per stasiun", "Q3"),
         "drop_weeks": ("RTY mingguan dan penanda minggu turun", "Q5"), "impact_hours": ("Jam hemat per tahun menurut skenario", "Q11"), "impact_naive_by_station": ("FPY naif vs bersih per nama stasiun", "Q12"),
         "impact_naive_vs_clean": ("KPI lini naif vs bersih", "Q12"), "kpi_line_total": ("RTY dan final yield seluruh lini", "Q1"), "kpi_station": ("KPI per stasiun", "Q1"),
         "kpi_station_shift_model": ("KPI per stasiun, shift, model", "Q1, Q4"), "ng_by_model": ("NG rate per model", "Q4"), "ng_by_shift": ("NG rate per shift", "Q4"), "ng_shift_model": ("NG rate shift x model", "Q4"),
         "ng_tests": ("Uji chi-square shift dan model", "Q4"), "pareto_80": ("Jumlah defect untuk mencapai 80% NG per stasiun", "Q3"), "spike_detection": ("NG rate harian Photometric Test dan penanda lonjakan", "Q5, Q13"),
         "station_daily_ng_photometric": ("NG harian stasiun Photometric", "Q5"), "station_week_fpy": ("FPY stasiun per minggu", "Q5"), "trend_daily_ma7": ("RTY harian dan rata-rata bergerak 7 hari", "Q5"),
         "trend_line_weekly_model": ("RTY mingguan per model", "Q5"), "trend_weekly": ("RTY mingguan seluruh lini", "Q5"), "app_test": ("Hasil uji dashboard (AppTest)", "Q8"),
         "dash_data_status": ("Ringkasan hasil test untuk dashboard", "Q6"), "dash_kpi_daily": ("KPI harian untuk dashboard", "Q1"), "dash_line_weekly": ("KPI mingguan untuk dashboard", "Q5"),
         "dash_pareto": ("Pareto defect untuk dashboard", "Q3"), "lineage": ("Hubungan antar model dbt", "Q10"), "gate_test": ("Uji gerbang publish saat skema berubah", "Q8"),
         "rebuild_check": ("Hash isi tabel pada dua build dari nol", "Q14"), "run_log": ("Log 10 run harian simulasi", "Q8"), "run_timing_daily": ("Durasi tiap run harian (bergantung mesin)", "Q8")}
resfiles = sorted(p for d in (RES_PREP, RES_ANALYSIS, RES_PRESENT, RES_AUTO) for p in d.glob("*.csv"))
miss = [p.stem for p in resfiles if p.stem not in FILES]
assert not miss, f"CSV hasil belum didokumentasikan di FILES: {miss}"
rp1 += card("Tabel 1.1c. Data hasil analisis (<code>project/results/</code>)", table(
    ["File", "Isi", "Baris", "Menjawab"], [[f"<code>{p.stem}.csv</code>", FILES[p.stem][0], I(len(pd.read_csv(p))), FILES[p.stem][1]] for p in resfiles]) +
    f"<p>{I(len(resfiles))} file CSV. Waktu pada <code>run_timing</code>, <code>run_timing_daily</code>, dan <code>benchmark</code> bergantung pada mesin dan tidak ikut uji hasil identik.</p>")
rp1 += '<h3>1.2 Angka kunci (KPI)</h3>' + card("Tabel 1.2. Lima KPI, satu definisi (<code>docs/kpi_definitions.md</code>)", table(
    ["KPI", "Rumus", "Hasil seluruh lini", "Jumlah data"],
    [["FPY", "OK lulus pertama ÷ input", P(ks.ok_first_pass.sum() / ks.input_qty.sum(), 2), f"{I(kl.input_qty)} unit"],
     ["NG rate", "NG ÷ input", P(ks.ng_qty.sum() / ks.input_qty.sum(), 2), f"{I(ks.ng_qty.sum())} NG"],
     ["Rework rate", "rework ÷ input", P(kl.rework_rate, 2), f"{I(ks.rework_qty.sum())} rework"],
     ["RTY", "hasil kali FPY 10 stasiun", P(kl.rty, 1), f"{I(kl.n_days)} hari"],
     ["Final yield", "hasil kali (OK + pulih) ÷ input", P(kl.final_yield, 1), "setelah rework"]]))

# ---------------------------------------------------------------- 2. questions
s2 = []
# Q1
ch1 = bars([(r.station_name, r.ng_rate, HI if r.station_code == top.station_code else BLUE, f"{r.station_name}: NG rate {P(r.ng_rate, 2)}, FPY {P(r.fpy, 2)}") for r in ks.sort_values("ng_rate", ascending=False).itertuples()],
           lambda v: P(v, 1), "NG rate per stasiun", h=290)
t1 = table(["Stasiun", "Input", "NG", "FPY", "NG rate", "Rework rate", "Scrap rate"],
           [[f"{int(r.sequence)}. {r.station_name}", I(r.input_qty), I(r.ng_qty), P(r.fpy, 2), P(r.ng_rate, 2), P(r.rework_rate, 2), P(r.scrap_rate, 2)] for r in ks.itertuples()])
s2.append(f'<h3 id="sec21">2.1 KPI per stasiun (Q1, Q2)</h3>' + card("Grafik 2.1. NG rate per stasiun", legend([(HI, "tertinggi"), (BLUE, "lainnya")]) + ch1) + card("Tabel 2.1. KPI per stasiun (urut proses)", t1) +
          Q(1, f"{top.station_name} paling sering NG ({P(top.ng_rate, 2)}), jauh di atas stasiun berikutnya, {sec.station_name} ({P(sec.ng_rate, 2)}). Di seluruh lini FPY {P(ks.ok_first_pass.sum() / ks.input_qty.sum(), 2)} per stasiun, tetapi RTY (hasil kali 10 stasiun) hanya {P(kl.rty, 1)}; setelah rework final yield {P(kl.final_yield, 1)}. "
             f"Mart <code>fct_kpi_daily</code> menyimpan KPI yang sama per hari, shift, dan model (satu definisi untuk semua laporan; {I(len(ksm))} baris per stasiun, shift, model pada <code>kpi_station_shift_model</code>)."))
# Q2
mx = cmd.fpy_diff_pts.abs().max()
n_off = int((cmd.fpy_diff_pts.abs() > 0.05).sum())
s2.append(Q(2, f"Ya. Mart sama dengan rekap Excel (rumus SUMIFS dihitung ulang LibreOffice) pada {I((cxl.status == 'PASS').sum())} dari {I(len(cxl))} pemeriksaan (22 hari sampel × stasiun × model × ukuran). "
            f"Rekap manual yang dibuat langsung dari file mentah berbeda: FPY meleset sampai {D(mx, 1)} poin persentase, dan {I(n_off)} dari {I(len(cmd))} kombinasi stasiun × model meleset lebih dari 0,05 poin. Penyebabnya adalah data kotor yang tidak disaring (Tabel 2.2)."))
s2.append(card("Tabel 2.2. Penyebab selisih rekap manual (sampel 22 hari)", table(["Jenis data kotor", "Baris pada sampel", "Efek pada rekap manual"],
                                                                                  [[LAB[r.dirty_type], I(r.rows_in_sample), cs(r.effect_on_manual_recap)] for r in cmc.itertuples()])))
# Q3
nt80 = p80.set_index("station_code")
s2.append('<h3 id="sec22">2.2 Defect (Q3)</h3>' + card("Tabel 2.3. Defect terbesar per stasiun", table(["Stasiun", "Jenis defect", "Defect terbesar", "Porsi terbesar", "Porsi terkecil", "Jenis untuk 80%"],
                                                                                              [[r.station_name, I(r.n_defect_types), f"<code>{r.top_defect}</code>", P(r.top_share, 1), P(r.min_share, 1), I(r.n_types_to_80pct)] for r in p80.itertuples()])))
s2.append(Q(3, f"Tidak ada defect yang dominan. Di tiap stasiun defect terbagi hampir merata: porsi defect terbesar hanya {P(p80.top_share[p80.n_defect_types > 1].min(), 1)} sampai {P(p80.top_share[p80.n_defect_types > 1].max(), 1)}, sehingga semua jenis defect dibutuhkan untuk mencapai 80% NG. "
            f"Burn-in dan Photometric punya tiga jenis defect (masing-masing sekitar sepertiga). Rancangan menyebut Burn-in didominasi kegagalan driver; generator tidak menanamnya, jadi temuan ini tidak bisa menunjuk satu penyebab dan mart tetap menyimpan Pareto mingguan.", warn=True))
# Q4
mdl = ngsm
chm = bars([(m, ngm.loc[m, "ng_rate"], HI if m == ngm.ng_rate.idxmax() else BLUE, f"{m}: NG rate {P(ngm.loc[m, 'ng_rate'], 2)}") for m in ("5W", "9W", "12W")], lambda v: P(v, 2), "NG rate per model", h=230, rot=0, small=True)
s2.append('<h3 id="sec23">2.3 Shift dan model (Q4)</h3>' + card("Grafik 2.3. NG rate per model", chm) +
          Q(4, f"Shift tidak berpengaruh: NG rate Shift 1 {P(ngs.loc['Shift 1', 'ng_rate'], 2)} dan Shift 2 {P(ngs.loc['Shift 2', 'ng_rate'], 2)} (chi-square p = {pv(ngt.loc['shift', 'p_value'])}). "
             f"Model berpengaruh (p {pv(ngt.loc['model', 'p_value'])}): 12W tertinggi ({P(ngm.loc['12W', 'ng_rate'], 2)}), 5W terendah ({P(ngm.loc['5W', 'ng_rate'], 2)}). Ukuran efeknya kecil (Cramér V {D(ngt.loc['model', 'cramers_v'], 3)}), jadi bedanya nyata secara statistik tetapi tidak besar. Pola belum tentu penyebab (dikerjakan di Project 29)."))
# Q5
w = tw.copy()
wl = list(w.week.str[5:])
drops = [i for i, r in enumerate(w.itertuples()) if r.week in set(dw[dw.is_drop].week)]
ch5 = lines(wl, [("Final yield", GREY, 2, list(w.final_yield)), ("RTY", BLUE, 2.5, list(w.rty))], lambda v: P(v, 0), "RTY dan final yield mingguan", bands=drops, band_label="minggu turun")
ph = sp.copy()
ch5b = lines(list(ph.date.str[5:]), [("NG rate Photometric", HI, 1.8, list(ph.ng_rate))], lambda v: P(v, 1), "NG rate harian lini (hari lonjakan berlatar kuning)", zero=True, bands=[i for i, r in enumerate(ph.itertuples()) if r.is_spike], band_label="lonjakan")
s2.append('<h3 id="sec24">2.4 Tren (Q5)</h3>' + card("Grafik 2.4a. RTY dan final yield per minggu", legend([(BLUE, "RTY"), (GREY, "final yield"), ("#FBBC04", "minggu turun")]) + ch5) +
          card("Grafik 2.4b. NG rate harian seluruh lini", ch5b) +
          Q(5, f"RTY mingguan berkisar {P(w.rty.min(), 1)} sampai {P(w.rty.max(), 1)}. Penurunan jelas hanya sekali: minggu {dw1.week}, RTY {P(dw1.rty, 1)} (skor robust {D(dw1.z_robust, 1)}). Stasiun terburuk minggu itu {dw1.worst_station} (Photometric Test), NG rate {P(dw1.worst_station_ng_rate, 2)} atau {D(dw1.ng_rate_ratio, 1)} kali rata-ratanya. "
             f"Lonjakan NG harian terdeteksi pada {I(len(spk))} hari berturut-turut, {spk.date.min()} sampai {spk.date.max()}, sesuai fakta yang ditanam."))
# Q6, Q7
tt = tests.groupby("layer").status.value_counts().unstack(fill_value=0)
t6 = table(["Lapisan", "Lulus", "Peringatan (warn)", "Gagal"], [[l, I(tt.loc[l].get("pass", 0)), I(tt.loc[l].get("warn", 0)), I(tt.loc[l].get("fail", 0) + tt.loc[l].get("error", 0))] for l in ("raw", "staging", "mart")])
s2.append('<h3 id="sec25">2.5 Kualitas data dan test (Q6, Q7)</h3>' + card("Tabel 2.5a. Hasil data test dbt per lapisan", t6) +
          Q(6, f"{I(dd.detected.sum())} dari {I(nraw)} baris mentah ({D(dd.detected.sum() / nraw * 100, 1)}%) gagal data test di lapisan raw, dan semuanya tertangkap. Kelima test raw menangkap masing-masing {I(dd.detected.iloc[0])} baris, jadi tidak ada satu test yang paling sering gagal. "
             f"Dari {I(n_tests)} test, {I(n_pass)} lulus, {I(n_warn)} peringatan (test raw berseverity warn: data kotor dicatat tanpa menghentikan pipeline), dan {I(n_err)} gagal; setelah staging semua test staging dan mart lulus. Test <code>raw_schema_signature</code> berseverity error karena perubahan skema harus menghentikan pipeline."))
s2.append(Q(7, f"Ya, keduanya. File terlambat <code>{late_file}</code> ({I(n_late)} file) tertangkap test <code>raw_file_freshness</code> (peringatan). Perubahan nama kolom pada {I(n_drift_files)} file mulai Juli tertangkap test <code>raw_schema_signature</code> pada run deteksi yang hanya menerima skema lama: semua {I(n_drift_files)} file gagal. "
            "Pada pipeline normal kedua nama kolom diterima lewat aturan staging S1, sehingga data baru tidak hilang."))

# Q8, Q9, Q10
ch8 = table(["Tanggal run", "Jenis", "File baru", "Test lulus", "Peringatan", "Gagal", "Gerbang"],
            [[r.run_date, r.jenis, I(r.file_baru), I(r.tes_pass), I(r.tes_warn), I(r.tes_error), OK("Publish") if r.gerbang == "publish" else NO("Tahan")] for r in rl.itertuples()])
med = float(rt[rt.run_date.isin(inc.run_date)].detik.median())
s2.append('<h3 id="sec26">2.6 Otomasi, kecepatan, dan lineage (Q8, Q9, Q10)</h3>' + card("Tabel 2.6a. Log run harian simulasi (database terpisah)", ch8 +
          f"<p>Uji gerbang: skema file terakhir diubah menjadi tidak dikenal, test <code>{gt.uji_yang_gagal}</code> gagal ({I(gt.tes_error)} error), pipeline keluar dengan kode {I(gt.kode_keluar_gerbang)}, dan hasil tidak dipublikasikan.</p>"))
s2.append(Q(8, f"Sebagian. Skrip run harian dan workflow GitHub Actions (<code>.github/workflows/daily.yml</code>, jadwal hari kerja) sudah ditulis. Run harian disimulasikan lokal: 1 full load dan {I(len(inc))} run inkremental, semuanya lolos gerbang publish; satu run inkremental memakan median {D(med, 0)} detik (bergantung mesin). "
            "Yang belum terbukti adalah eksekusi otomatis oleh GitHub Actions 7 hari berturut-turut: repositori ini belum digabung ke <code>main</code> dan belum punya riwayat run.", warn=True))
ench = [(e, agg.loc[e, "median_s"], HI if e == "DuckDB" else (GREY if e == "pandas" else BLUE), f"{e}: {D(agg.loc[e, 'median_s'], 2)} detik") for e in ("pandas", "Polars", "DuckDB")]
s2.append(card("Grafik 2.6. Waktu baca CSV dan hitung KPI, 1 juta baris (median 3 kali)", hbars(ench, lambda v: f"{D(v, 2)} dtk", "Waktu benchmark", float(agg.median_s.max()) * 1.2)) +
          Q(9, f"Pada 1 juta baris, baca CSV dan hitung KPI: DuckDB {D(agg.loc['DuckDB', 'median_s'], 2)} detik ({D(agg.loc['DuckDB', 'speedup_vs_pandas'], 1)} kali pandas), Polars {D(agg.loc['Polars', 'median_s'], 2)} detik ({D(agg.loc['Polars', 'speedup_vs_pandas'], 1)} kali), pandas {D(agg.loc['pandas', 'median_s'], 2)} detik. "
             f"Hanya membaca CSV, Polars {D(rdo.loc['Polars', 'speedup_vs_pandas'], 1)} kali lebih cepat. Hasil ketiganya dicocokkan lebih dulu. Mesin: Python <code>{bme.python}</code>, {I(bme.cpu_count)} CPU; hasil bergantung mesin dan ukuran data."))
ed = lin[lin.jenis_ke == "model"]
s2.append(Q(10, f"Peta asal tersedia di dokumentasi dbt (<code>project/results/3-presentation/dbt_docs.html</code>, diekspor statis) dan <code>lineage.csv</code> ({I(len(ed))} hubungan antar model). Contoh: angka FPY di dashboard dari <code>fct_kpi_daily</code>, yang bersumber dari <code>stg_production</code> dan <code>stg_rework</code>, yang bersumber dari <code>raw.production</code> dan <code>raw.rework</code>; "
             "kolom <code>source_file</code> dan <code>excel_row</code> membawa angka sampai ke baris Excel asalnya."))

# Q11, Q12
hr = hrs.set_index("menit_per_laporan")
s2.append('<h3 id="sec27">2.7 Dampak (Q11, Q12)</h3>' + card("Tabel 2.7a. Jam hemat per tahun (estimated)", table(["Menit per laporan", "Laporan per tahun", "Jam per tahun", "Dasar"],
                                                                                                           [[I(r.menit_per_laporan), I(r.laporan_per_tahun), D(r.jam_per_tahun, 0), r.dasar] for r in hrs.itertuples()])) +
          Q(11, f"Sekitar {D(hr.loc[90, 'jam_per_tahun'], 0)} jam per tahun pada asumsi {I(90)} menit per laporan dan {I(52)} laporan; rentangnya {D(hr.loc[60, 'jam_per_tahun'], 0)} sampai {D(hr.loc[120, 'jam_per_tahun'], 0)} jam untuk {I(60)} sampai {I(120)} menit. Menit per laporan adalah asumsi, bukan hasil ukur (estimated, simulated)."))
mt = nvs[nvs.fpy_bersih.notna()]
nph = int(nvs.fpy_bersih.isna().sum())
t12 = table(["Metrik", "Rekap naif dari raw", "Mart bersih"],
            [["Baris dipakai", I(nvc.loc["baris dipakai", "naif"]), I(nvc.loc["baris dipakai", "bersih"])], ["Input total", I(nvc.loc["input_qty total", "naif"]), I(nvc.loc["input_qty total", "bersih"])],
             ["NG rate", P(nvc.loc["NG rate", "naif"], 2), P(nvc.loc["NG rate", "bersih"], 2)], ["FPY lini", P(nvc.loc["FPY", "naif"], 2), P(nvc.loc["FPY", "bersih"], 2)],
             ["Jumlah nama stasiun", I(len(nvs)), I(len(mt))]])
s2.append(card("Tabel 2.7b. Rekap naif vs bersih (Q12)", t12) +
          Q(12, f"Pada total lini selisihnya kecil: FPY naif {P(nvc.loc['FPY', 'naif'], 2)} vs bersih {P(nvc.loc['FPY', 'bersih'], 2)} (selisih {D(abs(nvc.loc['FPY', 'naif'] - nvc.loc['FPY', 'bersih']) * 100, 2)} poin), karena data kotor saling meniadakan. "
             f"Bahayanya ada di rincian: rekap naif hanya memakai {I(nvc.loc['baris dipakai', 'naif'])} dari {I(nvc.loc['baris dipakai', 'bersih'])} baris (kolom bernama baru terlewat), membaca {I(nph)} nama stasiun huruf kecil sebagai stasiun tambahan, dan per stasiun dan model FPY meleset sampai {D(mx, 1)} poin (Q2). "
             "Jadi test tidak mengubah angka lini secara besar tetapi mencegah angka per stasiun yang salah.", warn=True))
# Q13, Q14
t13 = table(["No", "Fakta yang ditanam", "Penangkap", "Temuan", "Hasil"], [[I(r.fact_no), r.fakta, cs(r.penangkap), cs(r.temuan), OK("Sesuai")] for r in ev.itertuples()])
s2.append('<h3 id="sec28">2.8 Validitas (Q13, Q14)</h3>' + card("Tabel 2.8a. Lima fakta yang ditanam dan hasil deteksi", t13) +
          Q(13, f"Ya, kelima fakta terdeteksi ({I((ev.hasil == 'Sesuai').sum())} dari {I(len(ev))} sesuai). Dua fakta ditangkap analisis (Burn-in paling sering NG, lonjakan Photometric) dan tiga ditangkap test (perubahan kolom, file terlambat, data kotor)."))
t14 = table(["Tabel", "Baris", "Hash run 1", "Hash run 2", "Sama"], [[f"<code>{r.tabel}</code>", I(r.baris), f"<code>{r.sha256_run1}</code>", f"<code>{r.sha256_run2}</code>", OK("Ya") if r.sama else NO("Tidak")] for r in rb.itertuples()])
s2.append(card("Tabel 2.8b. Bangun ulang dari database kosong, dua kali", t14) +
          Q(14, f"Ya. Seluruh pipeline (muat 150 file, dbt build) dijalankan dua kali dari database kosong dan isi {I(len(rb))} tabel staging dan mart identik menurut SHA-256. Pengujian ini menemukan satu sumber beda: RTY dihitung dengan <code>exp(sum(ln))</code> yang bergantung urutan penjumlahan; sekarang memakai <code>list_product</code> dengan urutan stasiun tetap."))
rp2_body = "".join(s2)
SEC = {1: "21", 2: "21", 3: "22", 4: "23", 5: "24", 6: "25", 7: "25", 8: "26", 9: "26", 10: "26", 11: "27", 12: "27", 13: "28", 14: "28"}
qn_uniq = sorted(set(int(x) for x in re.findall(r'<span class="qn">Q(\d+)</span>', rp1 + rp2_body)))
assert qn_uniq == list(range(1, 15)), qn_uniq
npr = {k: sum(1 for v in PRIO.values() if v == k) for k in ("Utama", "Pendukung", "Tambahan")}
nw, wtxt = len(WARN), ", ".join(f"Q{n}" for n in sorted(WARN))
chips = '<div class="qchips">' + "".join(f'<a class="qc{" w" if n in WARN else ""}" href="#sec{SEC[n]}" title="{esc(QT[n])}">Q{n}</a>' for n in range(1, 15)) + "</div>"
rp2 = mk(f'<div class="card"><p><b>Jawaban singkat:</b> semua {len(QT)} pertanyaan terjawab ({npr["Utama"]} Utama, {npr["Pendukung"]} Pendukung, {npr["Tambahan"]} Tambahan). {nw} jawaban dengan catatan (kuning): {wtxt}. Klik nomor pertanyaan untuk melompat ke pembahasannya. Pertanyaan utama project dijawab di bagian 7.</p>',
         chips, '<p class="report-note">Q hijau = terjawab, Q kuning = terjawab dengan catatan.</p></div>', rp2_body)

# ---------------------------------------------------------------- 3-5
npy = len(list((REPO / "project/code").rglob("*.py")))
loc = sum(len(p.read_text(encoding="utf-8").splitlines()) for p in (REPO / "project/code").rglob("*.py"))
nsql = len(list((REPO / "project/code").rglob("*.sql")))
rp3 = mk('<div class="card"><p><b>Jawaban singkat:</b> dataset sesuai rancangan pada hal pokok (150 file harian, 10 stasiun, 3 model, 2 shift, lima fakta ditanam, seed tetap) dan dibuat ulang identik. '
         'Perbedaan ada pada nama stasiun, jenis data kotor, dominasi defect, dan bentuk data rework. Tidak ada masalah lisensi karena data buatan sendiri.</p></div>',
         table(["Aspek", "Rancangan", "Realisasi", "Verdict"], [
             ["Sumber", "Simulasi buatan sendiri, skrip <code>scripts/generate_raw.py</code>", "<code>01_generate_raw.py</code> (dipindah ke struktur repo standar), seed 27260302; sidik jari SHA-256 156 file cocok dengan registri DataCenter", OK("Sesuai")],
             ["Ukuran", "±150 file, ±9.000 baris produksi, ±15.000 baris defect", f"150 file, {I(nvc.loc['baris dipakai', 'bersih'])} baris produksi bersih ({I(nraw)} mentah), {I(mods.set_index('model').loc['stg_defect', 'rows'])} baris defect", OK("Sesuai")],
             ["Nama stasiun", "Solder Paste Printing, SMT Placement, Reflow, AOI, ..., Packaging", "Chip Mounting, LED Soldering, Driver Assembly, ..., Photometric Test, Packing (10 stasiun, kode S01-S10)", PART("Berubah")],
             ["Fakta 1", "Burn-in paling sering NG, didominasi kegagalan driver", f"{cs(ev.temuan.iloc[0])}; defect tidak didominasi satu jenis", PART("Sesuai + penyesuaian")],
             ["Fakta 2", "Lonjakan NG Photometric ±1 minggu", cs(ev.temuan.iloc[1]), OK("Sesuai")],
             ["Fakta 3", "Bulan ke-4: satu kolom bertambah, satu kolom berganti nama", f"{I(n_drift_files)} file mulai Juli memakai nama kolom baru dan kolom <code>line_id</code>; test skema gagal", OK("Sesuai")],
             ["Fakta 4", "Satu file terlambat 2 hari", f"{cs(ev.temuan.iloc[3])}", OK("Sesuai")],
             ["Fakta 5", "2-3% data kotor: ganda, NG kosong, stasiun salah ketik, format tanggal berbeda", f"{D(dd.planted.sum() / nraw * 100, 1)}% ({I(dd.planted.sum())} baris): NG kosong, NG negatif, input berupa teks, stasiun huruf kecil, baris ganda; format tanggal berbeda tidak ditanam", PART("Sesuai + penyesuaian")],
             ["Rework", "Satu baris per unit NG (rework_id, date_in, date_out)", "Satu baris per hari, stasiun, model; tidak ada nomor lot atau serial", PART("Berubah")],
             ["Nama defect", "Kode defect", "Kode dan nama defect rekaan pada <code>dim_defect</code>", OK("Sesuai")],
             ["Lisensi", "Tidak memakai dataset pihak ketiga", "Tidak ada dataset pihak ketiga, tidak perlu dicek", OK("Tidak berlaku")]]))
rp4 = mk('<div class="card"><p><b>Jawaban singkat:</b> semua tool inti rancangan dipakai (dbt-duckdb, DuckDB, Python, Streamlit + Plotly, Excel, GitHub Actions). Quarto diganti template Python, dashboard dan workflow belum berjalan di layanan publik, dan Playwright, SciPy, serta Polars ditambahkan.</p></div>',
         table(["Tool", "Rancangan", "Realisasi", "Verdict"], [
             ["dbt-duckdb", "Model berlapis, data test, lineage", f"{I(len(mods))} model dan {I(n_tests)} test ({I(n_warn)} berseverity warn untuk data kotor di raw); dokumentasi statis diekspor", OK("Sesuai")],
             ["DuckDB + SQL", "Penyimpanan dan perhitungan KPI", f"<code>warehouse.duckdb</code>; {I(nsql)} file SQL pada analisis", OK("Sesuai")],
             ["Python (Polars, pandas)", "Generator, pemuat, benchmark", f"{I(npy)} skrip dan modul ({I(loc)} baris); Polars dan DuckDB dibandingkan dengan pandas pada 1 juta baris", OK("Sesuai")],
             ["GitHub Actions", "Jadwal harian, alert jika gagal", "<code>daily.yml</code> ditulis (jadwal hari kerja, artefak <code>run_results.json</code>); belum ada riwayat run di repositori", PART("Sebagian")],
             ["Streamlit + Plotly", "Dashboard 4 halaman, link publik", f"<code>streamlit/app.py</code> 4 halaman, diuji AppTest ({I(len(apt) - 1)} halaman tanpa error); belum di-deploy", PART("Sebagian")],
             ["Quarto (opsional)", "Laporan mingguan HTML/PDF", "Diganti template Python dan Playwright (<code>weekly_report.html</code> dan <code>.pdf</code>)", PART("Berubah")],
             ["Excel", "Cek silang KPI", f"<code>crosscheck.xlsx</code> ({I(len(cxl))} pemeriksaan, rumus dihitung LibreOffice, bukan Microsoft Excel); tidak di-commit", PART("Sesuai + penyesuaian")],
             ["GitHub + Markdown", "Kode, workflow, README", "README, docs, struktur repo standar; di branch <code>project-27-build</code>, belum digabung ke <code>main</code>", PART("Sebagian")],
             ["SciPy, Playwright", "Tidak ada di rancangan", "Chi-square shift dan model; mencetak infografik dan laporan mingguan menjadi PDF", PART("Tambahan")]]))
steps = [("1", "Menyepakati definisi KPI", "<code>docs/kpi_definitions.md</code>", OK("Sesuai"), ""),
         ("2", "Merancang lapisan model dan test", "<code>docs/architecture.md</code>", OK("Sesuai"), ""),
         ("3", "Membuat data simulasi", "<code>01_generate_raw.py</code>", OK("Sesuai"), "Ditambah opsi <code>--big</code> untuk benchmark."),
         ("4", "Memuat file mentah", "<code>02_load_raw.py</code>, <code>sources.yml</code>", OK("Sesuai"), "Kesegaran data dibuat sebagai test, bukan source freshness bawaan dbt (tanggal terima ada di manifest)."),
         ("5", "Membuat model staging", "<code>stg_*.sql</code> (aturan S1-S5)", OK("Sesuai"), "Aturan pembersihan tercatat di <code>cleaning_log.md</code>."),
         ("6", "Membuat model mart KPI", "<code>dim_*.sql</code>, <code>fct_*.sql</code>, <code>04_run_queries.py</code>", OK("Sesuai"), "Q1, Q3, Q4, Q5 dijawab dari mart."),
         ("7", "Menulis data test", "<code>schema.yml</code>, <code>tests/</code>", OK("Sesuai"), f"{I(n_tests)} test; test raw berseverity warn."),
         ("8", "Cek silang Excel", "<code>05_excel_crosscheck.py</code>", OK("Sesuai"), "LibreOffice menghitung rumus."),
         ("9", "Jadwal otomatis dan build ulang", "<code>08_run_daily.py</code>, <code>daily.yml</code>, <code>09_rebuild_check.py</code>", PART("Sebagian"), "Simulasi lokal 10 hari; Actions belum terbukti 7 hari."),
         ("10", "Benchmark dan dampak", "<code>06_benchmark.py</code>, <code>07_impact.py</code>", OK("Sesuai"), ""),
         ("11", "Dashboard dan laporan", "<code>streamlit/app.py</code>, <code>12_weekly_report_and_docs.py</code>", PART("Sebagian"), "Dashboard belum di-deploy; laporan mingguan dari template Python."),
         ("12", "Docs dan README", "<code>dbt_docs.html</code>, <code>README.md</code>", PART("Sebagian"), "Siap; digabung ke main setelah ditinjau.")]
rp5 = mk('<div class="card"><p><b>Jawaban singkat:</b> 12 langkah dijalankan sesuai urutan dependensi data; langkah 9, 11, dan 12 sebagian.</p></div>',
         table(["Langkah", "Rancangan", "Realisasi", "Verdict", "Catatan"], [[a, b, c, d, e] for a, b, c, d, e in steps]),
         '<div class="card"><h4>Penyesuaian yang tidak ada di rancangan</h4><ul class="tight">',
         '<li>Gerbang publish dan uji bahwa gerbang menahan hasil saat skema berubah.</li>',
         '<li>Bangun ulang dari nol dua kali dengan hash isi tabel; menemukan dan memperbaiki satu sumber ketidakidentikan (urutan penjumlahan pada RTY).</li>',
         '<li>Pengamatan naif vs bersih (Q12) dan rekap manual dari raw sebagai pembanding cek silang.</li>',
         '<li>Notebook, infografik, dan laporan mingguan dibuat otomatis dari hasil; angka halaman ini diaudit terhadap CSV.</li></ul></div>')

# ---------------------------------------------------------------- 6
chk_f = lambda rel: (REPO / rel).exists()
outs = [("Dashboard auto-refresh", "Utama", PART("Sebagian"), "<code>streamlit/app.py</code> 4 halaman, diuji AppTest; link publik belum ada. Auto-refresh bergantung pada workflow yang belum berjalan"),
        ("Laporan KPI otomatis", "Utama", OK("Tercapai"), "<code>weekly_report.html</code> dan <code>weekly_report.pdf</code> (minggu terakhir) dari <code>12_weekly_report_and_docs.py</code>"),
        ("Project dbt dan database", "Utama", OK("Tercapai"), f"{I(len(mods))} model dengan {I(n_tests)} test; satu rangkaian perintah membangun ulang dari nol (hash identik)"),
        ("Workflow GitHub Actions", "Utama", PART("Sebagian"), "<code>daily.yml</code> ditulis; belum ada riwayat run"),
        ("Dokumentasi lineage", "Utama", OK("Tercapai"), "<code>dbt_docs.html</code> (statis) dan <code>lineage.csv</code>"),
        ("Generator data simulasi", "Utama", OK("Tercapai"), "<code>01_generate_raw.py</code>, seed tetap, hasil identik"),
        ("Laporan temuan dan rekomendasi", "Utama", OK("Tercapai"), "<code>README.md</code> dan halaman ini, dengan infografik"),
        ("Repositori GitHub", "Utama", PART("Sebagian"), "Struktur dan cara menjalankan ulang siap; di branch <code>project-27-build</code>, belum digabung ke <code>main</code>"),
        ("Slide presentasi", "Opsional", NO("Tidak dibuat"), "Opsional, tidak dibuat")]
nU = [o for o in outs if o[1] == "Utama"]
cnt_o = lambda s: sum(1 for o in nU if s in o[2])
docs = [("docs/kpi_definitions.md", "Definisi KPI", "project/docs/kpi_definitions.md"), ("docs/architecture.md", "Lapisan model dan test", "project/docs/architecture.md"),
        ("scripts/generate_raw.py", "Generator data", "project/code/1-data-preparation/python/01_generate_raw.py"), ("data/raw/*", "File mentah (tidak di-commit)", "project/data/raw"),
        ("data/planted_facts.json", "Fakta ditanam", "project/data/sample/ground_truth.json"), ("scripts/load_raw.py", "Pemuat ke DuckDB", "project/code/1-data-preparation/python/02_load_raw.py"),
        ("dbt/models/staging/", "3 model staging", "project/code/dbt/models/staging"), ("dbt/models/marts/", "Dimensi dan fakta", "project/code/dbt/models/marts"),
        ("dbt/models/**/schema.yml", "Test dan deskripsi kolom", "project/code/dbt/models/marts/schema.yml"), ("warehouse.duckdb", "Database (tidak di-commit)", "project/warehouse.duckdb"),
        ("outputs/crosscheck.xlsx", "Cek silang Excel (tidak di-commit)", "project/results/2-analysis/crosscheck.xlsx"), (".github/workflows/daily.yml", "Workflow harian", ".github/workflows/daily.yml"),
        ("notebooks/benchmark.ipynb", "Benchmark", "project/results/3-presentation/benchmark.ipynb"), ("dashboard/app.py", "Dashboard", "project/code/3-presentation/streamlit/app.py"),
        ("reports/weekly.qmd", "Template laporan (diganti skrip Python)", "project/code/3-presentation/python/12_weekly_report_and_docs.py"), ("requirements.txt", "Paket Python", "project/requirements.txt"),
        ("README.md", "Laporan temuan", "README.md"), ("index.html", "Pengalihan ke design-and-report/", "index.html"), ("slides/presentation.pdf", "Slide", "slides/presentation.pdf")]
stat_doc = lambda rel: PART("Tidak di-commit") if ("duckdb" in rel or rel.endswith("/raw") or "crosscheck.xlsx" in rel) else (OK("Ada") if chk_f(rel) else NO("Belum ada"))
rp6 = mk(f'<div class="card"><p><b>Jawaban singkat:</b> {I(cnt_o("Tercapai"))} dari {I(len(nU))} output Utama tercapai penuh dan {I(cnt_o("Sebagian"))} sebagian (dashboard belum di-deploy, workflow belum terbukti berjalan, repositori belum digabung ke main). Slide Opsional tidak dibuat.</p></div>',
         table(["Output", "Label", "Status", "Bukti"], [[f"<b>{a}</b>", b, c, d] for a, b, c, d in outs]),
         '<div class="card"><h4>Daftar dokumen pada rancangan vs repositori</h4>',
         table(["Dokumen (rancangan)", "Isi", "Lokasi sekarang", "Status"], [[f"<code>{a}</code>", b, f"<code>{c}</code>", stat_doc(c)] for a, b, c in docs]),
         '<p>Data mentah, database, dan <code>crosscheck.xlsx</code> tidak di-commit karena bisa dibuat ulang oleh skrip.</p></div>')

# ---------------------------------------------------------------- 7
crit = [("1. Kesembilan pertanyaan Utama terjawab dengan angka", OK("Tercapai"), "Q1, Q2, Q3, Q5, Q6, Q8, Q11, Q13, Q14 terjawab (bagian 2); Q3 dan Q8 dengan catatan"),
        ("2. KPI mart sama dengan hitungan manual Excel pada sampel", OK("Tercapai"), f"{I(len(cxl))} dari {I(len(cxl))} pemeriksaan PASS"),
        ("3. Semua test lulus pada data bersih, dan test yang tepat gagal pada fakta yang ditanam", OK("Tercapai"), f"{I(n_err)} test gagal pada pipeline normal; {I(dd.detected.sum())} dari {I(dd.planted.sum())} baris kotor, perubahan kolom, dan file terlambat tertangkap"),
        ("4. Pipeline berjalan otomatis minimal 7 hari berturut-turut, dan build ulang dari nol menghasilkan angka sama", PART("Sebagian"), f"Build ulang identik (Tabel 2.8b); simulasi lokal {I(len(inc))} run; GitHub Actions belum punya riwayat 7 hari"),
        ("5. Orang awam menyebut stasiun yield terendah dalam &lt; 1 menit", PART("Belum diuji"), "Ringkasan dashboard dan infografik memuat jawabannya di bagian atas; belum diuji ke pembaca sebenarnya"),
        ("6. Checklist standar (pertanyaan, cleaning, SQL, dashboard ter-deploy, README)", PART("Sebagian"), "Semua ada kecuali dashboard ter-deploy")]
ncr = sum(1 for c in crit if ">Tercapai<" in c[1])
rp7 = mk('<div class="card"><h4>7.1 Hasil analisis</h4><p><b>Pertanyaan utama:</b> KPI produksi bisa dibuat konsisten, teruji, dan dibangun ulang otomatis: satu definisi di model dbt, '
         f'{I(n_tests)} data test, dan gerbang publish yang menahan hasil jika skema berubah. Cek silang dengan Excel sama pada semua {I(len(cxl))} pemeriksaan, sedangkan rekap manual dari raw meleset sampai {D(mx, 1)} poin FPY. '
         'Bagian yang belum terbukti adalah eksekusi terjadwal oleh GitHub Actions selama 7 hari.</p><ul class="tight">',
         f'<li>{top.station_name} stasiun terburuk (NG rate {P(top.ng_rate, 2)}); RTY lini {P(kl.rty, 1)}, final yield {P(kl.final_yield, 1)}.</li>',
         f'<li>Minggu {dw1.week} turun (RTY {P(dw1.rty, 1)}) karena Photometric Test; {I(len(spk))} hari lonjakan berturut-turut.</li>',
         f'<li>Shift tidak berpengaruh (p = {pv(ngt.loc["shift", "p_value"])}); model berpengaruh kecil (12W {P(ngm.loc["12W", "ng_rate"], 2)}, 5W {P(ngm.loc["5W", "ng_rate"], 2)}).</li>',
         '<li>Defect dalam satu stasiun terbagi merata; tidak ada defect dominan.</li>',
         f'<li>{I(dd.detected.sum())} dari {I(dd.planted.sum())} baris kotor tertangkap; kelima fakta yang ditanam terdeteksi.</li></ul></div>',
         f'<div class="card"><h4>7.2 Impact (estimated, simulated)</h4><p>Penyusunan laporan manual sekitar {D(hr.loc[90, "jam_per_tahun"], 0)} jam per tahun pada asumsi {I(90)} menit × {I(52)} laporan; rentang {D(hr.loc[60, "jam_per_tahun"], 0)} sampai {D(hr.loc[120, "jam_per_tahun"], 0)} jam. Angka ini asumsi.</p></div>',
         '<div class="card"><h4>7.3 Success criteria</h4>' + table(["Kriteria (Design Project, bagian 8)", "Status", "Bukti"], [[a, b, c] for a, b, c in crit]) +
         f'<p>{I(ncr)} dari {I(len(crit))} kriteria tercapai penuh; sisanya sebagian atau belum diuji.</p></div>')
rp7 += mk('<div class="card"><h4>7.4 Rekomendasi</h4><ul class="tight">',
          f'<li>Fokuskan perbaikan proses pada {top.station_name}, stasiun dengan NG rate tertinggi.</li>',
          '<li>Jadikan <code>dbt build</code> gerbang wajib sebelum KPI dipublikasikan; perubahan nama kolom harus menghentikan pipeline atau memicu peringatan, bukan hilang diam-diam.</li>',
          '<li>Standarkan template Excel produksi (kolom terkunci, validasi angka, daftar pilihan stasiun) agar data kotor tidak masuk.</li>',
          '<li>Catat rework per unit (nomor lot atau serial) agar analisis penyebab bisa dilanjutkan di Project 29.</li></ul></div>')
rp7 += mk('<div class="card"><h4>7.5 Saran perbaikan</h4><ul class="tight">',
          '<li>Gabungkan ke <code>main</code> setelah ditinjau, lalu biarkan GitHub Actions berjalan 7 hari untuk memenuhi kriteria 4.</li>',
          '<li>Deploy dashboard ke Streamlit Community Cloud dan uji ke satu pembaca awam untuk kriteria 5 dan 6.</li>',
          '<li>Tambahkan data kotor berformat tanggal berbeda dan defect dominan pada generator versi berikutnya agar Q3 bisa menunjuk penyebab.</li></ul></div>')
rp7 += mk('<div class="card"><h4>7.6 Batasan</h4><ul class="tight">',
          '<li>Semua temuan berasal dari data simulasi; fakta yang ditemukan adalah fakta yang ditanam sendiri.</li>',
          '<li>Data test hanya menangkap aturan yang ditulis; kesalahan yang tidak terpikirkan tetap bisa lolos.</li>',
          '<li>Rework hanya per hari, stasiun, dan model; tidak ada lot atau serial. Nama defect dan nama stasiun berbeda dari rancangan.</li>',
          '<li>Waktu benchmark dan durasi run bergantung pada mesin. Jam hemat adalah asumsi menit per laporan.</li>',
          '<li>Dashboard belum di-deploy dan GitHub Actions belum terbukti 7 hari. Slide Opsional tidak dibuat. Cek silang Excel dihitung LibreOffice. Pola belum tentu penyebab (Project 29). Tidak ada masalah lisensi dataset.</li></ul></div>')

evq = [("1", "rp1", "Data yang didapat", OK("Didapat"), f"150 file Excel, {I(nraw)} baris produksi mentah, {I(dd.planted.sum())} baris kotor ditangani"),
       ("2", "rp2", "Business question terjawab?", OK(f"{len(QT)} dari {len(QT)}"), f"Semua terjawab ({npr['Utama']} Utama, {npr['Pendukung']} Pendukung, {npr['Tambahan']} Tambahan); {nw} dengan catatan ({wtxt})"),
       ("3", "rp3", "Dataset sesuai?", PART("Sesuai + penyesuaian"), "Pokok sesuai; nama stasiun, jenis data kotor, dominasi defect, dan rework berbeda"),
       ("4", "rp4", "Tools sesuai?", PART("Sesuai + penyesuaian"), "Quarto diganti template Python; dashboard dan Actions belum berjalan publik"),
       ("5", "rp5", "Alur sesuai?", PART("Sesuai + penyesuaian"), "12 langkah dijalankan; langkah 9, 11, 12 sebagian"),
       ("6", "rp6", "Output tercapai?", PART(f"{cnt_o('Tercapai')} penuh, {cnt_o('Sebagian')} sebagian"), f"{cnt_o('Tercapai')} dari {len(nU)} output Utama penuh"),
       ("7", "rp7", "Kesimpulan", OK("Tersedia"), f"Hasil analisis, Impact, {len(crit)} kriteria sukses, rekomendasi, saran perbaikan, batasan")]
evq_html = '<div class="scroll"><table class="evq"><tr><th>No</th><th>Pertanyaan evaluasi</th><th>Verdict</th><th>Ringkasan</th></tr>' + "".join(
    f'<tr><td><span class="en">{n}</span></td><td><a href="#{h}">{t}</a></td><td>{v}</td><td>{s}</td></tr>' for n, h, t, v, s in evq) + "</table></div>"
H = lambda i, t, sm, body: f'\n<h2 id="rp{i}">{i}. {t}<small>{sm}</small></h2>\n{body}\n'
report = mk(
    '<div class="pane" id="report" data-tab="report" hidden>\n',
    '<div class="callout g"><h4>Report Project versi 2: evaluasi hasil terhadap Design Project</h4><p>Halaman ini disusun sebagai 7 jawaban atas pertanyaan evaluasi. Tabel dan grafik dibuat otomatis dari hasil query SQL (DuckDB) dan model dbt pada data simulasi. '
    f'Angka pada teks diaudit terhadap file di <code>project/results/</code>: @@AUDIT@@ angka diperiksa tanpa selisih. Semua angka bersumber dari data simulasi buatan sendiri dan menguji metode, bukan kondisi pabrik. Rancangan lengkap ada di tab <a href="#design">Design Project</a>.</p></div>\n',
    evq_html,
    H(1, "Data yang berhasil didapatkan", "Isi data mentah, tabel di database, dan data hasil analisis", rp1),
    H(2, "Apakah business question terjawab?", f"{len(QT)} pertanyaan pada Design Project, dijawab dengan data", rp2),
    H(3, "Apakah dataset sesuai dengan Design Project?", "Perbandingan rancangan dengan realisasi", rp3),
    H(4, "Apakah tools yang digunakan sesuai?", "Perbandingan rancangan dengan eksekusi", rp4),
    H(5, "Apakah alur pengerjaan sesuai dengan Design Project?", f"{len(steps)} langkah rancangan vs yang dijalankan", rp5),
    H(6, "Apakah project output tercapai?", "Output pada Design Project, bagian 7", rp6),
    H(7, "Kesimpulan", "Hasil analisis, Impact, success criteria, rekomendasi, saran perbaikan, dan batasan", rp7),
    '</div>\n')

# ---------------------------------------------------------------- audit angka
STATIC = {str(i) for i in range(0, 21)} | {"30", "100", "80", "60", "0,05", "95", "150", "156", "27", "26", "29", "23", "25", "7", "10", "52", "90", "120", "2026", "27260302", "1.000", "9.000", "15.000", "S01", "0,001", "2", "5", "9", "12"}
STATIC |= {f"{a}.{b}" for a in range(1, 10) for b in range(1, 10)} | {f"{a}.{b}{c}" for a in range(1, 10) for b in range(1, 10) for c in "abc"}
n_tok, bad = audit(report, STATIC)
manual = [("seluruh CSV hasil terdokumentasi", not miss), ("lima fakta ditanam sesuai", bool((ev.hasil == "Sesuai").all())), ("cek silang Excel semua PASS", bool((cxl.status == "PASS").all())),
          ("data kotor ditemukan = ditanam", bool((dd.detected == dd.planted).all())), ("14 pertanyaan (9 Utama, 4 Pendukung, 1 Tambahan)", len(QT) == 14 and npr == {"Utama": 9, "Pendukung": 4, "Tambahan": 1}),
          ("catatan hanya Q3, Q8, Q12", WARN == {3, 8, 12}), ("langkah rancangan = 12", len(steps) == 12), ("pertanyaan unik = 14", qn_uniq == list(range(1, 15))),
          ("build ulang identik", bool(rb.sama.all())), ("semua run harian lolos gerbang", bool((rl.gerbang == "publish").all())), ("gerbang menahan saat skema berubah", gt.hasil.startswith("tahan")),
          ("test gagal pada pipeline normal = 0", n_err == 0), ("10 stasiun dan 150 file", len(ks) == 10 and kl.n_days == 150)]
assert all(v for _, v in manual), [k for k, v in manual if not v]
if bad:
    print("TOKEN TIDAK TERDAFTAR:", bad)
    sys.exit(1)
report = report.replace("@@AUDIT@@", I(n_tok) + f" (ditambah {I(len(manual))} klaim manual)")

# ---------------------------------------------------------------- rakit halaman
v1 = (HERE / "page_v1.html").read_text(encoding="utf-8")
a = v1.index('<div class="pane" id="report"')
b = v1.index("</main>")
design_pane = v1[v1.index('<div class="pane" id="design"'):a]
nav_old = re.search(r'<nav aria-label="Project navigation">.*?</nav>', v1, re.S).group(0)
btn = lambda t: re.search(rf'<button type="button" class="tab[^"]*" data-t="{t}".*?</button>', nav_old, re.S).group(0)
design_links = re.search(r'<div class="links" data-tab="design">.*?</div>', nav_old, re.S).group(0)
report_links = ('<div class="links" data-tab="report" hidden>' + "".join(f'<a href="#rp{i}">{t}</a>' for i, t in
               enumerate(["Data", "Business Questions", "Dataset", "Tools", "Alur Kerja", "Project Output", "Kesimpulan"], 1)) + "</div>")
nav_new = f'<nav aria-label="Project navigation">{btn("design")}{btn("report")}{design_links}{report_links}</nav>'
css = (HERE / "report.css").read_text(encoding="utf-8")
html = v1[:a] + report + v1[b:]
html = html.replace(nav_old, nav_new)
i = html.rindex("</style>")
html = html[:i] + css + html[i:]
out = REPO / "design-and-report" / "index.html"
out.write_text(html, encoding="utf-8")
assert design_pane == html[html.index('<div class="pane" id="design"'):html.index('<div class="pane" id="report"')], "pane Design berubah"
print(f"index.html {len(html) / 1024:.0f} KB; {n_tok} angka diaudit; {len(manual)} klaim manual; pane Design identik")
