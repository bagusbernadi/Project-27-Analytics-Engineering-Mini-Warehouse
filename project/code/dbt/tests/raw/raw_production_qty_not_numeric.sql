{{ config(severity='warn', tags=['raw']) }}
-- Baris produksi mentah dengan jumlah input bukan angka murni (mis. "480 pcs").
select _source_file, _excel_row from {{ source('raw', 'production') }} where coalesce(input_qty, qty_input) is not null and try_cast(try_cast(coalesce(input_qty, qty_input) as double) as integer) is null
