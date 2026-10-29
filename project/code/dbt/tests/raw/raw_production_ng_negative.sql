{{ config(severity='warn', tags=['raw']) }}
-- Baris produksi mentah dengan NG negatif.
select _source_file, _excel_row from {{ source('raw', 'production') }} where try_cast(try_cast(coalesce(ng_qty, qty_ng) as double) as integer) < 0
