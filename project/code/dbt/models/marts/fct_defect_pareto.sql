-- Kontribusi tiap defect pada NG satu stasiun per minggu, diurutkan dari terbesar, dengan porsi kumulatif.
with w as (
    select date_trunc('week', date)::date as week, station_code, defect_code, sum(qty) as qty
    from {{ ref('stg_defect') }} group by 1, 2, 3
)
select week, station_code, defect_code, qty, qty * 1.0 / sum(qty) over (partition by week, station_code) as share,
       sum(qty) over (partition by week, station_code order by qty desc, defect_code) * 1.0 / sum(qty) over (partition by week, station_code) as cum_share
from w
