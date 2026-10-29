-- Semua rate KPI harian harus berada di antara 0 dan 1.
select * from {{ ref('fct_kpi_daily') }} where fpy not between 0 and 1 or ng_rate not between 0 and 1 or rework_rate not between 0 and 1 or scrap_rate not between 0 and 1
