{{ config(severity='warn', tags=['raw']) }}
-- OK + NG melebihi input pada baris yang angkanya bisa dibaca.
select _source_file, _excel_row from {{ source('raw', 'production') }}
where try_cast(try_cast(coalesce(ok_qty, qty_ok) as double) as integer) + try_cast(try_cast(coalesce(ng_qty, qty_ng) as double) as integer)
      > try_cast(try_cast(coalesce(input_qty, qty_input) as double) as integer)
