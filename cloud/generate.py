# generate.py
import math
import random
from datetime import date, timedelta

from database import get_db_connection
from feature_engineering import calculate_kc


def generate_data():
    db = get_db_connection()
    cursor = db.cursor(dictionary=True)

    # crop + soil constants for cycle 1
    cursor.execute("""
        SELECT c.*, pr.planting_date, sp.field_capacity, sp.taw
        FROM planting_record pr
        JOIN crop c ON pr.crop_id = c.crop_id
        JOIN soil_profile sp ON sp.plot_id = pr.plot_id
        WHERE pr.cycle_id = 1
    """)
    crop = cursor.fetchone()
    planting_date = crop["planting_date"]
    taw = float(crop["taw"])

    print("Generating 10,000 days of data...")
    start_date = date(2020, 1, 1)

    # carry depletion across days so it behaves like a real field
    depletion_mm = 0.0
    rain_hist = []
    eto_hist = []
    vwc_hist = []

    for i in range(10000):
        current = start_date + timedelta(days=i)
        doy = current.timetuple().tm_yday
        dap = (current - planting_date).days

        # --- crop + weather for the day ---
        kc = calculate_kc(dap, crop)

        # ETo follows the seasons (peak around April)
        eto = 4.5 + 1.5 * math.sin(2 * math.pi * (doy - 100) / 365)
        eto = max(1.0, eto)

        # rain is occasional and heavy
        rain = random.uniform(2, 25) if random.random() < 0.15 else 0.0

        # --- water balance ---
        etc = kc * eto
        depletion_mm = max(0.0, min(taw, depletion_mm - rain + etc))
        ratio = depletion_mm / taw

        # VWC that matches this depletion, as a fraction
        vwc = float(crop["field_capacity"]) - depletion_mm / (crop["root_depth_zr"] * 1000)

        # --- keep rolling history ---
        rain_hist.append(rain)
        eto_hist.append(eto)
        vwc_hist.append(vwc)

        rain_3d = sum(rain_hist[-3:])
        rain_7d = sum(rain_hist[-7:])
        eto_3d = sum(eto_hist[-3:]) / min(3, len(eto_hist))
        trend_3d = (vwc_hist[-1] - vwc_hist[-4]) / 3 if len(vwc_hist) >= 4 else 0.0

        # --- weather values ---
        temp_max = 30 + 3 * math.sin(2 * math.pi * (doy - 100) / 365)
        temp_min = temp_max - 8
        rh = 70 + random.uniform(-10, 10)
        wind = 2.5 + random.uniform(-0.5, 0.5)
        solar = 15 + 5 * math.sin(2 * math.pi * (doy - 100) / 365)

        # --- write weather ---
        cursor.execute("""
            INSERT INTO weather_daily
                (plot_id, recorded_date, temp_max, temp_min, relative_humidity,
                 wind_speed, solar_rad, precipitation)
            VALUES (1, %s, %s, %s, %s, %s, %s, %s)
            ON DUPLICATE KEY UPDATE
                temp_max = VALUES(temp_max),
                temp_min = VALUES(temp_min),
                relative_humidity = VALUES(relative_humidity),
                wind_speed = VALUES(wind_speed),
                solar_rad = VALUES(solar_rad),
                precipitation = VALUES(precipitation)
        """, (current, temp_max, temp_min, rh, wind, solar, rain))

        # --- write sensor reading (vwc stored as percent) ---
        cursor.execute("""
            INSERT INTO sensor_reading
                (node_id, recorded_at, soil_moisture_vwc, soil_temp,
                 canopy_air_temp, canopy_rh, battery_voltage)
            VALUES (1, %s, %s, %s, %s, %s, 4.1)
        """, (f"{current} 12:00:00", vwc * 100, temp_max - 5, temp_max, rh))

        # --- write analytics ---
        cursor.execute("""
            INSERT INTO daily_analytics
                (plot_id, cycle_id, recorded_date, eto, dap, kc,
                 rain_3d_sum, rain_7d_sum, eto_3d_mean, moisture_trend_3d,
                 depletion_ratio_measured, depletion_ratio_simulated,
                 sim_vs_measured_deviation)
            VALUES (1, 1, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, 0)
            ON DUPLICATE KEY UPDATE
                eto = VALUES(eto),
                dap = VALUES(dap),
                kc = VALUES(kc),
                rain_3d_sum = VALUES(rain_3d_sum),
                rain_7d_sum = VALUES(rain_7d_sum),
                eto_3d_mean = VALUES(eto_3d_mean),
                moisture_trend_3d = VALUES(moisture_trend_3d),
                depletion_ratio_measured = VALUES(depletion_ratio_measured),
                depletion_ratio_simulated = VALUES(depletion_ratio_simulated)
        """, (current, eto, dap, kc, rain_3d, rain_7d, eto_3d,
              trend_3d, ratio, ratio))

        if (i + 1) % 1000 == 0:
            print(f"  {i + 1} days written")

    db.commit()
    cursor.close()
    db.close()
    print("Done.")


if __name__ == "__main__":
    generate_data()