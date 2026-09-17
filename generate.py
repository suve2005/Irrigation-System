import mysql.connector
from datetime import date, timedelta
import random
from database import get_db_connection

def generate_data():
    db = get_db_connection()
    cursor = db.cursor()
    
    print("Setting up base reference data...")
    # 1. Temporarily disable checks to insert the root parent records safely
    cursor.execute("SET FOREIGN_KEY_CHECKS = 0;")
    
    # 2. Create Plot 1, Crop 1, and Planting Record 1 if they don't exist
    cursor.execute("INSERT IGNORE INTO plot (plot_id, latitude, longitude, elevation, zone_macro) VALUES (1, 6.9271, 79.8612, 10.0, 'Tropical')")
    cursor.execute("INSERT IGNORE INTO crop (crop_id, crop_name, variety, kc_ini, kc_mid, kc_end, root_depth_zr, depletion_p) VALUES (1, 'Chilli', 'Anaheim', 0.4, 1.05, 0.9, 0.6, 0.4)")
    cursor.execute("INSERT IGNORE INTO planting_record (cycle_id, plot_id, crop_id, planting_date) VALUES (1, 1, 1, '2020-01-01')")
    
    cursor.execute("SET FOREIGN_KEY_CHECKS = 1;")
    db.commit()

    print("Generating 2,000 rows of analytics for regression training...")
    start_date = date(2020, 1, 1)
    
    for i in range(2000):
        current = start_date + timedelta(days=i)
        depletion = random.uniform(0.1, 0.9)
        # Synthetic math: if depletion is high, we need more water (0 to 15mm)
        water_needed = max(0.0, (depletion - 0.4) * 25.0) 
        
        cursor.execute("""
            INSERT INTO daily_analytics (plot_id, cycle_id, recorded_date, eto, dap, kc, depletion_ratio_measured, target_water_mm) 
            VALUES (1, 1, %s, %s, %s, %s, %s, %s)
        """, (current, random.uniform(3, 5), (i%120)+1, random.uniform(0.5, 1.1), depletion, round(water_needed, 2)))
    
    db.commit()
    db.close()
    print("Generation complete! Safe to run model now.")

if __name__ == "__main__":
    generate_data()