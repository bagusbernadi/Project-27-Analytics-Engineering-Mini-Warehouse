{{ config(severity='warn', tags=['raw', 'freshness']) }}
-- File diterima lebih dari {{ var('freshness_max_lag_days') }} hari kalender setelah hari kerja berikutnya dari tanggal bisnis.
select file_name, business_date, received_date,
       received_date - (business_date + case dayofweek(business_date) when 5 then 3 when 6 then 2 else 1 end) as lag_days
from {{ source('raw', 'file_manifest') }}
where received_date - (business_date + case dayofweek(business_date) when 5 then 3 when 6 then 2 else 1 end) > {{ var('freshness_max_lag_days') }}
