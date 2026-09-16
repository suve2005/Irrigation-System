# feature_engineering.py
from database import get_db_connection
from datetime import date
import random


def calculate_and_store_features(plot_id: int, cycle_id: int, target_date: date):
    """
    Step 1: Fetch raw data from DB.
    Step 2: Calculate features and save back to DB (daily_analytics).
    """
    db = get_db_connection()
    cursor = db.cursor(dictionary=True)

    # 1. Fetch live data from the database
    cursor.execute("""
        SELECT AVG(soil_moisture_vwc) as avg_moisture, AVG(soil_temp) as avg_temp
        FROM sensor_reading 
        WHERE DATE(recorded_at) = %s
    """, (target_date,))
    raw_data = cursor.fetchone()

    # (Mock Feature Calculations based on raw data)
    eto = round(random.uniform(3.0, 5.0), 2)
    dap = 45
    kc = 1.05
    depletion_measured = round(random.uniform(0.1, 0.9), 3)

    # 2. Send calculated values back to the DB
    insert_query = """
    INSERT INTO daily_analytics 
    (plot_id, cycle_id, recorded_date, eto, dap, kc, depletion_ratio_measured)
    VALUES (%s, %s, %s, %s, %s, %s, %s)
    """
    cursor.execute(insert_query, (plot_id, cycle_id, target_date, eto, dap, kc, depletion_measured))

    db.commit()
    cursor.close()
    db.close()
    print(f"[FEATURE ENG] Calculated and saved analytics for {target_date}")