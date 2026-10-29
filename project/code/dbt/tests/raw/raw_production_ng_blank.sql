{{ config(severity='warn', tags=['raw']) }}
-- Baris produksi mentah dengan NG kosong (rata-rata satu dari lima jenis data kotor).
select _source_file, _excel_row from {{ source('raw', 'production') }} where coalesce(ng_qty, qty_ng) is null
