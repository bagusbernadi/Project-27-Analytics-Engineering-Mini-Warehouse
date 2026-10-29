-- KPI satu stasiun, model, shift, hari. Definisi di project/docs/kpi_definitions.md.
-- Unit NG yang tidak pulih lewat rework dianggap scrap.
with rw as (
    select date, shift, station_code, model, sum(qty_rework) as rework_qty, sum(qty_recovered) as recovered_qty
    from {{ ref('stg_rework') }} group by 1, 2, 3, 4
)
select p.prod_key as kpi_key, p.date, p.station_code, p.model, p.shift, p.input_qty, p.ok_first_pass, p.ng_qty,
       coalesce(rw.rework_qty, 0) as rework_qty, coalesce(rw.recovered_qty, 0) as recovered_qty,
       p.ng_qty - coalesce(rw.recovered_qty, 0) as scrap_qty,
       p.ok_first_pass * 1.0 / p.input_qty as fpy, p.ng_qty * 1.0 / p.input_qty as ng_rate,
       coalesce(rw.rework_qty, 0) * 1.0 / p.input_qty as rework_rate, (p.ng_qty - coalesce(rw.recovered_qty, 0)) * 1.0 / p.input_qty as scrap_rate
from {{ ref('stg_production') }} p left join rw using (date, shift, station_code, model)
