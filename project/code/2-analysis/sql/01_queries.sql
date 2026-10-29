-- Query analisis. Format: "-- name: <nama>" memulai satu query; hasilnya ditulis ke results/2-analysis/<nama>.csv oleh 04_run_queries.py.
-- Semua query membaca model dbt (lapisan mart), bukan file mentah.

-- name: kpi_station
SELECT s.sequence, k.station_code, s.station_name, sum(k.input_qty) AS input_qty, sum(k.ok_first_pass) AS ok_first_pass, sum(k.ng_qty) AS ng_qty,
       sum(k.rework_qty) AS rework_qty, sum(k.recovered_qty) AS recovered_qty, sum(k.scrap_qty) AS scrap_qty,
       sum(k.ok_first_pass) * 1.0 / sum(k.input_qty) AS fpy, sum(k.ng_qty) * 1.0 / sum(k.input_qty) AS ng_rate,
       sum(k.rework_qty) * 1.0 / sum(k.input_qty) AS rework_rate, sum(k.scrap_qty) * 1.0 / sum(k.input_qty) AS scrap_rate
FROM fct_kpi_daily k JOIN dim_station s USING (station_code) GROUP BY ALL ORDER BY ng_rate DESC;

-- name: kpi_station_shift_model
SELECT station_code, shift, model, sum(input_qty) AS input_qty, sum(ng_qty) AS ng_qty, sum(ok_first_pass) * 1.0 / sum(input_qty) AS fpy,
       sum(ng_qty) * 1.0 / sum(input_qty) AS ng_rate, sum(rework_qty) * 1.0 / sum(input_qty) AS rework_rate, sum(scrap_qty) * 1.0 / sum(input_qty) AS scrap_rate
FROM fct_kpi_daily GROUP BY ALL ORDER BY station_code, shift, model;

-- name: kpi_line_total
WITH s AS (SELECT station_code, sum(ok_first_pass) * 1.0 / sum(input_qty) AS fpy, (sum(ok_first_pass) + sum(recovered_qty)) * 1.0 / sum(input_qty) AS final_yield FROM fct_kpi_daily GROUP BY 1)
SELECT list_product(list(fpy ORDER BY station_code)) AS rty, list_product(list(final_yield ORDER BY station_code)) AS final_yield, (SELECT sum(rework_qty) * 1.0 / sum(input_qty) FROM fct_kpi_daily) AS rework_rate,
       (SELECT count(DISTINCT date) FROM fct_kpi_daily) AS n_days, (SELECT count(*) FROM fct_kpi_daily) AS n_rows, (SELECT sum(input_qty) FROM fct_kpi_daily) AS input_qty FROM s;

-- name: defect_pareto_station
WITH d AS (SELECT station_code, defect_code, sum(qty) AS qty FROM stg_defect GROUP BY 1, 2),
     r AS (SELECT *, qty * 1.0 / sum(qty) OVER (PARTITION BY station_code) AS share,
                  sum(qty) OVER (PARTITION BY station_code ORDER BY qty DESC, defect_code) * 1.0 / sum(qty) OVER (PARTITION BY station_code) AS cum_share,
                  row_number() OVER (PARTITION BY station_code ORDER BY qty DESC, defect_code) AS rank FROM d)
SELECT r.station_code, s.station_name, r.rank, r.defect_code, df.defect_name, r.qty, r.share, r.cum_share FROM r JOIN dim_station s USING (station_code) JOIN dim_defect df USING (defect_code)
ORDER BY s.sequence, r.rank;

-- name: ng_shift_model
SELECT shift, model, sum(input_qty) AS input_qty, sum(ng_qty) AS ng_qty, sum(ng_qty) * 1.0 / sum(input_qty) AS ng_rate FROM fct_kpi_daily GROUP BY ALL ORDER BY ng_rate DESC;

-- name: ng_by_shift
SELECT shift, sum(input_qty) AS input_qty, sum(ng_qty) AS ng_qty, sum(ng_qty) * 1.0 / sum(input_qty) AS ng_rate FROM fct_kpi_daily GROUP BY 1 ORDER BY 1;

-- name: ng_by_model
SELECT model, sum(input_qty) AS input_qty, sum(ng_qty) AS ng_qty, sum(ng_qty) * 1.0 / sum(input_qty) AS ng_rate FROM fct_kpi_daily GROUP BY 1 ORDER BY 1;

-- name: trend_weekly
SELECT week, list_avg(list(rty ORDER BY model)) AS rty, list_avg(list(final_yield ORDER BY model)) AS final_yield, list_avg(list(rework_rate ORDER BY model)) AS rework_rate FROM fct_line_weekly GROUP BY 1 ORDER BY 1;

-- name: trend_line_weekly_model
SELECT week, model, rty, final_yield, rework_rate FROM fct_line_weekly ORDER BY week, model;

-- name: trend_daily_ma7
WITH s AS (SELECT date, station_code, sum(ok_first_pass) * 1.0 / sum(input_qty) AS fpy FROM fct_kpi_daily GROUP BY 1, 2),
     d AS (SELECT date, list_product(list(fpy ORDER BY station_code)) AS rty FROM s GROUP BY 1)
SELECT date, rty, avg(rty) OVER (ORDER BY date ROWS BETWEEN 6 PRECEDING AND CURRENT ROW) AS rty_ma7, count(*) OVER (ORDER BY date ROWS BETWEEN 6 PRECEDING AND CURRENT ROW) AS n_in_window FROM d ORDER BY date;

-- name: station_week_fpy
SELECT date_trunc('week', date)::date AS week, station_code, sum(ng_qty) AS ng_qty, sum(input_qty) AS input_qty, sum(ok_first_pass) * 1.0 / sum(input_qty) AS fpy, sum(ng_qty) * 1.0 / sum(input_qty) AS ng_rate
FROM fct_kpi_daily GROUP BY 1, 2 ORDER BY 1, 2;

-- name: station_daily_ng_photometric
SELECT date, sum(ng_qty) AS ng_qty, sum(input_qty) AS input_qty, sum(ng_qty) * 1.0 / sum(input_qty) AS ng_rate FROM fct_kpi_daily WHERE station_code = 'S08' GROUP BY 1 ORDER BY 1;
