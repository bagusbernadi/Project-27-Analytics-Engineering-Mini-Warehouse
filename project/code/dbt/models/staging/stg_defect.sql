-- Jumlah defect per jenis; kolom defect_code (lama) dan defect_cd (baru) digabung.
select _source_file as source_file, _excel_row as excel_row,
       coalesce(try_strptime(left(date, 19), '%Y-%m-%d %H:%M:%S'), try_strptime(left(date, 10), '%Y-%m-%d'))::date as date,
       trim(shift) as shift, d.station_code, trim(model) as model, coalesce(defect_code, defect_cd) as defect_code,
       try_cast(try_cast(qty as double) as integer) as qty
from {{ source('raw', 'defect') }} s join {{ ref('dim_station') }} d on lower(trim(s.station)) = lower(d.station_name)
