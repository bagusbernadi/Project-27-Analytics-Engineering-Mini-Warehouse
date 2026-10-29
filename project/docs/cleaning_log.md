# Log cleaning

Mentah 9.060 baris produksi (9.000 + 60 duplikat). Tiap jenis kotor ditanam generator, ditangkap satu test raw (severity warn), lalu ditangani di `stg_production`. Cocok per file: blank_qty, negative_qty, text_qty, lowercase_station, duplicate_row.

| Jenis | Test raw | Ditanam | Tertangkap | Aturan staging |
|---|---|---|---|---|
| blank_qty | `raw_production_ng_blank` | 60 | 60 | S3: NG = input - OK, ditandai was_recovered |
| negative_qty | `raw_production_ng_negative` | 60 | 60 | S3: NG dihitung ulang |
| text_qty | `raw_production_qty_not_numeric` | 60 | 60 | S2: ambil digit dari teks |
| lowercase_station | `raw_production_station_not_standard` | 60 | 60 | S4: cocokkan nama tanpa beda huruf |
| duplicate_row | `raw_production_duplicate` | 60 | 60 | S5: simpan baris pertama |

Kolom berganti nama mulai Juli (60 file, `input_qty`/`ok_qty`/`ng_qty` menggantikan `qty_*`): `S1` menggabungkan nama lama dan baru; test `raw_schema_signature` (error) hanya menerima skema v1 pada run deteksi.
