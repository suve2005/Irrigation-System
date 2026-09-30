# quick_check.py
from database import get_db_connection
db = get_db_connection()
c = db.cursor()

# --- Step 1: is the target table already full? ---
c.execute("SELECT COUNT(*) FROM model_features_table")
n = c.fetchone()[0]
print(f"model_features_table row count : {n}")

c.execute("""SELECT MIN(recorded_date), MAX(recorded_date),
                    COUNT(DISTINCT recorded_date),
                    COUNT(DISTINCT hour_of_day)
             FROM model_features_table""")
print(f"  date range / distinct dates / distinct hours: {c.fetchone()}")

# --- Step 2: are the underlying tables even matching on date? ---
# (no NOT EXISTS, no JOINs to slow tables — just date overlap)
c.execute("""
    SELECT COUNT(DISTINCT DATE(sr.recorded_at))
    FROM sensor_reading sr
    WHERE EXISTS (
        SELECT 1 FROM daily_analytics da
        WHERE da.plot_id = 1
          AND da.recorded_date = DATE(sr.recorded_at)
    )
""")
print(f"sensor dates with a matching daily_analytics row : {c.fetchone()[0]}")

c.execute("""
    SELECT COUNT(DISTINCT DATE(sr.recorded_at))
    FROM sensor_reading sr
    WHERE EXISTS (
        SELECT 1 FROM weather_daily wd
        WHERE wd.plot_id = 1
          AND wd.recorded_date = DATE(sr.recorded_at)
    )
""")
print(f"sensor dates with a matching weather_daily row   : {c.fetchone()[0]}")

c.execute("SELECT COUNT(DISTINCT DATE(recorded_at)) FROM sensor_reading")
print(f"sensor distinct dates total                      : {c.fetchone()[0]}")

# --- Step 3: how many sensor rows have NO model_features row for their (date, hour)? ---
c.execute("""
    SELECT COUNT(*)
    FROM sensor_reading sr
    WHERE NOT EXISTS (
        SELECT 1 FROM model_features_table mft
        WHERE mft.plot_id = 1
          AND mft.recorded_date = DATE(sr.recorded_at)
          AND mft.hour_of_day = HOUR(sr.recorded_at)
    )
""")
print(f"sensor rows that still need a feature row       : {c.fetchone()[0]}")

c.close()
db.close()