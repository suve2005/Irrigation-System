CREATE TABLE plot (
    plot_id INT AUTO_INCREMENT PRIMARY KEY,
    latitude DECIMAL(9,6),
    longitude DECIMAL(9,6),
    elevation DECIMAL(8,2),
    zone_macro VARCHAR(100)
);