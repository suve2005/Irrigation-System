CREATE TABLE weather_daily (
    plot_id INT,
    recorded_date DATE,
    temp_max DECIMAL(5,2),
    temp_min DECIMAL(5,2),
    relative_humidity DECIMAL(5,2),
    wind_speed DECIMAL(6,2),
    solar_rad DECIMAL(8,3),
    precipitation DECIMAL(7,2),
    PRIMARY KEY (plot_id, recorded_date),
    FOREIGN KEY (plot_id) REFERENCES plot(plot_id)
);