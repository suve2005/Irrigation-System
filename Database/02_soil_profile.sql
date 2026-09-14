CREATE TABLE soil_profile (
    plot_id INT PRIMARY KEY,
    soil_texture VARCHAR(50),
    sand_pct DECIMAL(5,2),
    clay_pct DECIMAL(5,2),
    bulk_density DECIMAL(6,3),
    field_capacity DECIMAL(6,3),
    wilting_point DECIMAL(6,3),
    taw DECIMAL(8,3),
    FOREIGN KEY (plot_id) REFERENCES plot(plot_id)
);