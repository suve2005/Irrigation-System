CREATE TABLE crop (
    crop_id INT AUTO_INCREMENT PRIMARY KEY,
    crop_name VARCHAR(50),
    variety VARCHAR(100),
    kc_ini DECIMAL(4,2),
    kc_mid DECIMAL(4,2),
    kc_end DECIMAL(4,2),
    root_depth_zr DECIMAL(5,2),
    depletion_p DECIMAL(4,2)
);