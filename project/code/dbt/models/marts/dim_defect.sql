-- Kode defect, nama, dan kategori. Nama dan kategori dibuat untuk simulasi ini (data mentah hanya memuat kode).
select * from (values
    ('CHP-01', 'Chip bergeser', 'Assembly'), ('CHP-02', 'Chip retak', 'Material'),
    ('SLD-01', 'Solder dingin', 'Assembly'), ('SLD-02', 'Solder jembatan', 'Assembly'), ('SLD-03', 'Solder kurang', 'Assembly'),
    ('DRV-01', 'Driver tidak menyala', 'Electrical'), ('DRV-02', 'Konektor longgar', 'Assembly'),
    ('HSG-01', 'Housing retak', 'Material'), ('HSG-02', 'Housing tidak rapat', 'Assembly'),
    ('POT-01', 'Potting bergelembung', 'Assembly'), ('POT-02', 'Potting kurang', 'Assembly'),
    ('WIR-01', 'Kabel putus', 'Electrical'), ('WIR-02', 'Polaritas terbalik', 'Electrical'),
    ('BRN-01', 'Gagal menyala saat burn-in', 'Electrical'), ('BRN-02', 'LED redup', 'Optical'), ('BRN-03', 'Flicker', 'Electrical'),
    ('PHM-01', 'Flux di bawah spec', 'Optical'), ('PHM-02', 'CCT di luar spec', 'Optical'), ('PHM-03', 'CRI di bawah spec', 'Optical'),
    ('FQC-01', 'Cacat visual', 'Cosmetic'), ('FQC-02', 'Label salah', 'Cosmetic'),
    ('PKG-01', 'Kemasan rusak', 'Packaging')
) as t(defect_code, defect_name, category)
