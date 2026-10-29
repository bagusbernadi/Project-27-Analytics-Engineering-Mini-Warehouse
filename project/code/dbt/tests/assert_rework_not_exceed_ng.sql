-- Rework tidak boleh melebihi NG, pulih tidak boleh melebihi rework, scrap tidak boleh negatif.
select * from {{ ref('fct_kpi_daily') }} where rework_qty > ng_qty or recovered_qty > rework_qty or scrap_qty < 0
