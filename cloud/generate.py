# generate.py
import mysql.connector
from datetime import date, timedelta
import random
from database import get_db_connection


def generate_data():
    db = get_db_connection()
    cursor = db.cursor()

    print("Generating 10,000 rows of analytics...")
    start_date = date(2020, 1, 1)

    for i in range(10000):
        current = start_date + timedelta(days=i)
        cursor.execute("""
            INSERT INTO daily_analytics (plot_id, cycle_id, recorded_date, eto, dap, kc, depletion_ratio_measured) 
            VALUES (1, 1, %s, %s, %s, %s, %s)
        """, (current, random.uniform(3, 5), (i % 120) + 1, random.uniform(0.5, 1.1), random.uniform(0.1, 0.9)))

    db.commit()
    db.close()
    print("Generation complete!")


if __name__ == "__main__":
    generate_data()