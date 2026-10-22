CREATE TABLE sensor_reading (
    reading_id INT AUTO_INCREMENT PRIMARY KEY,
    node_id INT,
    recorded_at TIMESTAMP,
    soil_moisture_vwc DECIMAL(6,3),
    soil_temp DECIMAL(5,2),
    canopy_air_temp DECIMAL(5,2),
    canopy_rh DECIMAL(5,2),
    battery_voltage DECIMAL(4,2),
    FOREIGN KEY (node_id) REFERENCES node(node_id)
);