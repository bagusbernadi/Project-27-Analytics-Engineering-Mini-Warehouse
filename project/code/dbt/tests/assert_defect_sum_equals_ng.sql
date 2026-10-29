-- Jumlah defect per stasiun, model, shift, hari harus sama dengan NG pada stg_production.
with d as (select date, shift, station_code, model, sum(qty) as defect_qty from {{ ref('stg_defect') }} group by 1, 2, 3, 4)
select p.prod_key, p.ng_qty, coalesce(d.defect_qty, 0) as defect_qty from {{ ref('stg_production') }} p left join d using (date, shift, station_code, model)
where p.ng_qty <> coalesce(d.defect_qty, 0)
