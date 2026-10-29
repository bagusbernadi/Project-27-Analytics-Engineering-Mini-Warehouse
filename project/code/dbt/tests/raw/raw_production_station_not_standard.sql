{{ config(severity='warn', tags=['raw']) }}
-- Nama stasiun yang tidak persis sama dengan daftar baku (huruf kecil, salah ketik).
select _source_file, _excel_row from {{ source('raw', 'production') }} where station not in (select station_name from {{ ref('dim_station') }})
