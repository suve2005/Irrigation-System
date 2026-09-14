CREATE TABLE planting_record (
    cycle_id INT AUTO_INCREMENT PRIMARY KEY,
    plot_id INT,
    crop_id INT,
    planting_date DATE,
    FOREIGN KEY (plot_id) REFERENCES plot(plot_id),
    FOREIGN KEY (crop_id) REFERENCES crop(crop_id)
);