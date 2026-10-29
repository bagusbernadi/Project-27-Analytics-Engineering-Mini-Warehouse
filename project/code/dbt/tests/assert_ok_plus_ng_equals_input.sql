-- Setelah staging: OK + NG harus sama dengan input dan tidak boleh negatif.
select * from {{ ref('stg_production') }} where ok_first_pass + ng_qty <> input_qty or ok_first_pass < 0 or ng_qty < 0 or input_qty <= 0
