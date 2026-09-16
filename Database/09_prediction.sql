CREATE TABLE prediction (
    prediction_id INT AUTO_INCREMENT PRIMARY KEY,
    plot_id INT,
    analytics_id INT,
    probability DECIMAL(5,4),
    decision BOOLEAN,
    model_version VARCHAR(50),
    predicted_at TIMESTAMP,
    FOREIGN KEY (plot_id) REFERENCES plot(plot_id),
    FOREIGN KEY (analytics_id) REFERENCES daily_analytics(analytics_id)
);