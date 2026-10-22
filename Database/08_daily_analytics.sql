CREATE TABLE daily_analytics (
    analytics_id INT AUTO_INCREMENT PRIMARY KEY,
    plot_id INT,
    cycle_id INT,
    recorded_date DATE,
    eto DECIMAL(6,3),
    rain_3d_sum DECIMAL(7,2),
    rain_7d_sum DECIMAL(7,2),
    eto_3d_mean DECIMAL(6,3),
    dap INT,
    kc DECIMAL(4,2),
    moisture_trend_3d DECIMAL(6,3),
    depletion_ratio_measured DECIMAL(6,3),
    depletion_ratio_simulated DECIMAL(6,3),
    sim_vs_measured_deviation DECIMAL(6,3),
    -- Required for the upsert to keep one summary per plot, crop cycle, and date.
    UNIQUE KEY uq_plot_id_cycle_id_recorded_date (plot_id, cycle_id, recorded_date),
    FOREIGN KEY (plot_id) REFERENCES plot(plot_id),
    FOREIGN KEY (cycle_id) REFERENCES planting_record(cycle_id)
);
