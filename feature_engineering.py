from database import get_db_connection
from datetime import date
import random

def calculate_and_store_features(plot_id: int, cycle_id: int, target_date: date):
    db = get_db_connection()
    cursor = db.cursor(dictionary=True)
    
    # 1. Mock calculations (normally aggregated from sensor_reading table)
    eto = round(random.uniform(3.0, 5.0), 2)
    dap = 45
    kc = 1.05
    depletion_measured = round(random.uniform(0.1, 0.9), 3)
    target_water_mm = max(0.0, round((depletion_measured - 0.4) * 25.0, 2))

    # 2. SQL query with 8 placeholders matching 8 columns
    insert_query = """
    INSERT INTO daily_analytics 
    (plot_id, cycle_id, recorded_date, eto, dap, kc, depletion_ratio_measured, target_water_mm)
    VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
    """
    
    # 3. Tuple containing exactly 8 variables
    values = (plot_id, cycle_id, target_date, eto, dap, kc, depletion_measured, target_water_mm)
    
    cursor.execute(insert_query, values)
    
    db.commit()
    cursor.close()
    db.close()
    print(f"[FEATURE ENG] Saved daily analytics for {target_date}")