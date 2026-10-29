-- RTY dan yield akhir lini harus di antara 0 dan 1, dan yield akhir tidak boleh lebih kecil dari RTY.
select * from {{ ref('fct_line_weekly') }} where rty not between 0 and 1 or final_yield not between 0 and 1 or final_yield < rty - 1e-12
