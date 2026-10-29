-- Porsi kumulatif Pareto tiap stasiun dan minggu harus berakhir di 100%.
select week, station_code, max(cum_share) as max_cum from {{ ref('fct_defect_pareto') }} group by 1, 2 having abs(max(cum_share) - 1) > 1e-9
