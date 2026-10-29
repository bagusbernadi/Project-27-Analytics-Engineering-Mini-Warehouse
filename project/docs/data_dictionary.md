# Kamus data

**raw.production**: date, shift, station, model, operator_id, qty_input, qty_ok, qty_ng (nama lama) atau input_qty, ok_qty, ng_qty, line_id (nama baru, mulai Juli), _source_file, _excel_row. Semua teks.

**raw.defect**: date, shift, station, model, defect_cd, qty. **raw.rework**: baris per hari, stasiun, model. **raw.file_manifest**: file_name, business_date, received_date.

**stg_production**: prod_key, date, shift, station_code (S01-S10), model, operator_id, input_qty, ok_first_pass, ng_qty, was_recovered, source_file, excel_row.

**fct_kpi_daily**: kpi_key, date, station_code, model, shift, input_qty, ok_first_pass, ng_qty, rework_qty, recovered_qty, scrap_qty, fpy, ng_rate, rework_rate, scrap_rate.
**fct_defect_pareto**: week, station_code, defect_code, qty, share, cum_share. **fct_line_weekly**: week, model, rty, final_yield, rework_rate.
**dim_station**: station_code, station_name, sequence. **dim_defect**: defect_code, defect_name (rekaan), category.
