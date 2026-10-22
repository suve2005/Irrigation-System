from database import get_db_connection

def populate_model_features():
    db = get_db_connection()
    cursor = db.cursor()

    insert_query = """
    INSERT INTO model_features_table
        (hour_of_day, soil_moisture_vwc, soil_temp, canopy_air_temp, canopy_rh,
         temp_max, temp_min, relative_humidity, wind_speed, solar_rad, precipitation,
         eto, eto_3d_mean, rain_3d_sum, rain_7d_sum, dap, kc, taw,
         depletion_ratio_measured, depletion_ratio_simulated, sim_vs_measured_deviation,
         moisture_trend_3d, sensor_depth_cm, root_depth_zr, depletion_p,
         sand_pct, clay_pct, elevation, recorded_date, plot_id)
    SELECT
        HOUR(sr.recorded_at), sr.soil_moisture_vwc, sr.soil_temp, sr.canopy_air_temp, sr.canopy_rh,
        wd.temp_max, wd.temp_min, wd.relative_humidity, wd.wind_speed, wd.solar_rad, wd.precipitation,
        da.eto, da.eto_3d_mean, da.rain_3d_sum, da.rain_7d_sum, da.dap, da.kc, sp.taw,
        da.depletion_ratio_measured, da.depletion_ratio_simulated, da.sim_vs_measured_deviation,
        da.moisture_trend_3d, sr.sensor_depth_cm, c.root_depth_zr, c.depletion_p,
        sp.sand_pct, sp.clay_pct, p.elevation, DATE(sr.recorded_at), p.plot_id
    FROM (
        SELECT
            sr.*,
            n.plot_id,
            n.sensor_depth_cm,
            ROW_NUMBER() OVER (
                PARTITION BY n.plot_id, DATE(sr.recorded_at), HOUR(sr.recorded_at)
                ORDER BY sr.recorded_at DESC, sr.reading_id DESC
            ) AS hour_rank
        FROM sensor_reading AS sr
        JOIN node AS n ON n.node_id = sr.node_id
    ) AS sr
    JOIN plot p             ON sr.plot_id = p.plot_id
    JOIN soil_profile sp    ON sp.plot_id = p.plot_id
    JOIN daily_analytics da ON da.plot_id = p.plot_id AND da.recorded_date = DATE(sr.recorded_at)
    JOIN weather_daily wd   ON wd.plot_id = p.plot_id AND wd.recorded_date = DATE(sr.recorded_at)
    JOIN planting_record pr ON pr.plot_id = p.plot_id AND pr.cycle_id = da.cycle_id
    JOIN crop c             ON c.crop_id = pr.crop_id
    WHERE sr.hour_rank = 1
    ON DUPLICATE KEY UPDATE feature_id = model_features_table.feature_id

    cursor.execute(insert_query)
    db.commit()
    print(f"[MODEL FEATURES] Inserted {cursor.rowcount} new rows.")

    cursor.close()
    db.close()

if __name__ == "__main__":
    populate_model_features()
