{{ config(severity='warn', tags=['raw']) }}
-- Salinan baris ganda (tanggal, shift, stasiun, model sama); baris pertama tidak dihitung.
select _source_file, _excel_row from (
  select _source_file, _excel_row, row_number() over (partition by date, shift, lower(station), model order by _source_file, _excel_row) as rn from {{ source('raw', 'production') }}
) where rn > 1
