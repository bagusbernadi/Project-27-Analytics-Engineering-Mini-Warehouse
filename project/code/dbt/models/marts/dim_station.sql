-- Daftar 10 stasiun berurutan. station_code dibuat dari urutan (data mentah hanya memuat nama).
select * from (values
    ('S01', 'Chip Mounting', 1), ('S02', 'LED Soldering', 2), ('S03', 'Driver Assembly', 3), ('S04', 'Housing Assembly', 4), ('S05', 'Potting', 5),
    ('S06', 'Wiring Check', 6), ('S07', 'Burn-in Test', 7), ('S08', 'Photometric Test', 8), ('S09', 'Final QC', 9), ('S10', 'Packing', 10)
) as t(station_code, station_name, sequence)
