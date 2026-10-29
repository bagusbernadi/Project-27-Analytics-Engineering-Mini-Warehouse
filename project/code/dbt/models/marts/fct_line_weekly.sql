-- KPI seluruh lini per minggu dan model. RTY = hasil kali FPY semua stasiun; final_yield = hasil kali yield akhir (OK pertama + pulih lewat rework).
with s as (
    select date_trunc('week', date)::date as week, model, station_code,
           sum(ok_first_pass) * 1.0 / sum(input_qty) as fpy, (sum(ok_first_pass) + sum(recovered_qty)) * 1.0 / sum(input_qty) as final_yield,
           sum(rework_qty) as rework_qty, sum(input_qty) as input_qty
    from {{ ref('fct_kpi_daily') }} group by 1, 2, 3
)
-- list_product dengan urutan stasiun tetap supaya hasil identik di setiap build (exp(sum(ln)) bergantung urutan penjumlahan)
select week, model, list_product(list(fpy order by station_code)) as rty, list_product(list(final_yield order by station_code)) as final_yield, sum(rework_qty) * 1.0 / sum(input_qty) as rework_rate
from s group by 1, 2
