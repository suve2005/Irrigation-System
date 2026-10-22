CREATE TABLE node (
    node_id INT AUTO_INCREMENT PRIMARY KEY,
    plot_id INT,
    sensor_depth_cm DECIMAL(6,2),
    install_date DATE,
    FOREIGN KEY (plot_id) REFERENCES plot(plot_id)
);