-- Unit rework per (hari, shift, stasiun, model, defect). Satu baris data adalah kelompok unit, bukan satu unit.
-- qty_scrap_after_rework = unit rework yang tidak pulih.
select row_number() over (order by _source_file, _excel_row) as rework_id, _source_file as source_file,
       coalesce(try_strptime(left(date, 19), '%Y-%m-%d %H:%M:%S'), try_strptime(left(date, 10), '%Y-%m-%d'))::date as date,
       trim(shift) as shift, d.station_code, trim(model) as model, defect_code,
       try_cast(try_cast(qty_rework as double) as integer) as qty_rework, try_cast(try_cast(qty_recovered as double) as integer) as qty_recovered,
       try_cast(try_cast(qty_rework as double) as integer) - try_cast(try_cast(qty_recovered as double) as integer) as qty_scrap_after_rework
from {{ source('raw', 'rework') }} s join {{ ref('dim_station') }} d on lower(trim(s.station)) = lower(d.station_name)
