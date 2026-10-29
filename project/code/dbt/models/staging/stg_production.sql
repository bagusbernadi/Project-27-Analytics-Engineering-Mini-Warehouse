-- Merapikan file produksi mentah: satu nama kolom (lama atau baru), tipe data, tanggal, kode stasiun, dan baris kotor.
-- Aturan (dicatat di docs/cleaning_log.md):
--   S1 kolom lama dan baru digabung dengan coalesce;
--   S2 qty_input bertulis angka plus teks (mis. "480 pcs") diambil angkanya;
--   S3 ng kosong atau negatif dihitung ulang = input - ok (dicatat di was_recovered);
--   S4 nama stasiun dicocokkan tanpa memperhatikan huruf besar/kecil;
--   S5 baris ganda (tanggal, shift, stasiun, model sama) dibuang, baris pertama dipertahankan.
with src as (
    select _source_file as source_file, _excel_row as excel_row,
           coalesce(try_strptime(left(date, 19), '%Y-%m-%d %H:%M:%S'), try_strptime(left(date, 10), '%Y-%m-%d'), try_strptime(date, '%d/%m/%Y'))::date as date,
           trim(shift) as shift, lower(trim(station)) as station_key, trim(model) as model, operator_id,
           coalesce(input_qty, qty_input) as input_raw, coalesce(ok_qty, qty_ok) as ok_raw, coalesce(ng_qty, qty_ng) as ng_raw
    from {{ source('raw', 'production') }}
), typed as (
    select s.*, d.station_code,
           try_cast(regexp_extract(input_raw, '(\d+)', 1) as integer) as input_qty,
           try_cast(try_cast(ok_raw as double) as integer) as ok_first_pass,
           try_cast(try_cast(ng_raw as double) as integer) as ng_parsed
    from src s join {{ ref('dim_station') }} d on s.station_key = lower(d.station_name)
), fixed as (
    select *, (ng_parsed is null or ng_parsed < 0) as was_recovered,
           case when ng_parsed is null or ng_parsed < 0 then input_qty - ok_first_pass else ng_parsed end as ng_qty,
           row_number() over (partition by date, shift, station_code, model order by source_file, excel_row) as rn
    from typed
)
select date || '|' || shift || '|' || station_code || '|' || model as prod_key,
       date, shift, station_code, model, operator_id, input_qty, ok_first_pass, ng_qty, was_recovered, source_file, excel_row
from fixed where rn = 1
