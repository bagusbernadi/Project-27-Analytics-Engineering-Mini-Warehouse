{{ config(severity='error', tags=['raw', 'schema']) }}
-- Sheet yang kolomnya tidak termasuk tanda tangan skema yang diterima (var accepted_signatures di dbt_project.yml).
select file_name, sheet, "columns" from {{ source('raw', 'file_columns') }}
where (sheet || ':' || "columns") not in ({% for s in var('accepted_signatures') %}'{{ s }}'{% if not loop.last %}, {% endif %}{% endfor %})
