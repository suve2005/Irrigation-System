# cleanup_duplicates.py
"""
One-shot cleanup:
  1. Backup polluted tables
  2. Deduplicate sensor_reading, weather_daily, daily_analytics, model_features_table
  3. Add UNIQUE KEYs to prevent future duplication
  4. Remove impossible-date rows (2047) and fix planting_date mismatch

Run with:  python cleanup_duplicates.py
"""
import sys
from database import get_db_connection

# -------------------------------------------------------------------
# What we consider "the same row" for each table
# -------------------------------------------------------------------
DEDUP = {
    # table                       key columns
    "sensor_reading":       ["node_id", "recorded_at"],
    "weather_daily":        ["plot_id", "recorded_date"],
    "daily_analytics":      ["plot_id", "cycle_id", "recorded_date"],
    "model_features_table": ["plot_id", "recorded_date", "hour_of_day"],
}

BACKUP_SUFFIX = "_bak"

# -------------------------------------------------------------------
def run(cursor, sql, args=()):
    cursor.execute(sql, args)
    return cursor

def count(cursor, table):
    cursor.execute(f"SELECT COUNT(*) FROM {table}")
    return cursor.fetchone()[0]

def table_exists(cursor, name):
    cursor.execute("""
        SELECT COUNT(*) FROM information_schema.tables
        WHERE table_schema = DATABASE() AND table_name = %s
    """, (name,))
    return cursor.fetchone()[0] > 0

def index_exists(cursor, table, index_name):
    cursor.execute("""
        SELECT COUNT(*) FROM information_schema.statistics
        WHERE table_schema = DATABASE()
          AND table_name = %s
          AND index_name = %s
    """, (table, index_name))
    return cursor.fetchone()[0] > 0

# -------------------------------------------------------------------
def backup(cursor, table):
    bak = table + BACKUP_SUFFIX
    if table_exists(cursor, bak):
        print(f"  [backup] {bak} already exists — skipping")
        return
    print(f"  [backup] creating {bak} ...", end=" ", flush=True)
    cursor.execute(f"CREATE TABLE {bak} AS SELECT * FROM {table}")
    print("done")

# -------------------------------------------------------------------
def dedup(cursor, table, key_cols):
    """
    Keep only the lowest-id row per key group.

    Uses a temp table to avoid the classic slow 'DELETE ... JOIN self'
    on big tables. Bounded memory, fast on any MySQL 5.7+/8.x.
    """
    print(f"\n  [dedup] {table}  (key: {key_cols})")
    before = count(cursor, table)
    print(f"          rows before: {before:,}")

    if before == 0:
        print(f"          empty, skipping")
        return

    id_col = None
    cursor.execute(f"SHOW COLUMNS FROM {table}")
    for (col, *_rest) in cursor.fetchall():
        if col.endswith("_id") and col not in key_cols:
            id_col = col
            break

    if id_col is None:
        # Fall back: use ROW_NUMBER over the full row ordering
        # (requires MySQL 8). We'll try, and warn if it fails.
        print(f"          no primary *_id column found — using ROW_NUMBER fallback")
        key_list = ", ".join(f"`{c}`" for c in key_cols)
        run(cursor, f"""
            CREATE TEMPORARY TABLE tmp_dedup AS
            SELECT * FROM (
                SELECT t.*,
                       ROW_NUMBER() OVER (PARTITION BY {key_list} ORDER BY 1) AS _rn
                FROM {table} t
            ) x
            WHERE _rn = 1
        """)
    else:
        key_list = ", ".join(f"`{c}`" for c in key_cols)
        print(f"          keeping lowest `{id_col}` per {key_cols}")
        run(cursor, f"""
            CREATE TEMPORARY TABLE tmp_dedup AS
            SELECT t.* FROM {table} t
            JOIN (
                SELECT MIN(`{id_col}`) AS keep_id
                FROM {table}
                GROUP BY {key_list}
            ) g ON t.`{id_col}` = g.keep_id
        """)

    # Drop the helper row-number column if it exists
    cursor.execute("SHOW COLUMNS FROM tmp_dedup")
    cols = [c[0] for c in cursor.fetchall()]
    if "_rn" in cols:
        run(cursor, "ALTER TABLE tmp_dedup DROP COLUMN _rn")

    after = count(cursor, "tmp_dedup")
    print(f"          rows after : {after:,}  (removed {before - after:,})")

    # Swap
    print(f"          swapping ...", end=" ", flush=True)
    run(cursor, f"DELETE FROM {table}")
    col_list = ", ".join(f"`{c}`" for c in cols if c != "_rn")
    run(cursor, f"INSERT INTO {table} ({col_list}) SELECT {col_list} FROM tmp_dedup")
    run(cursor, "DROP TEMPORARY TABLE tmp_dedup")
    print("done")

# -------------------------------------------------------------------
def add_unique_key(cursor, table, key_cols):
    """Add UNIQUE KEY if it doesn't exist. Prevents future duplication."""
    idx_name = "uq_" + "_".join(key_cols)
    if index_exists(cursor, table, idx_name):
        print(f"  [index] {idx_name} already exists on {table}")
        return
    key_list = ", ".join(f"`{c}`" for c in key_cols)
    print(f"  [index] adding UNIQUE KEY {idx_name} on {table} ({key_list}) ...",
          end=" ", flush=True)
    try:
        run(cursor, f"ALTER TABLE {table} ADD UNIQUE KEY {idx_name} ({key_list})")
        print("done")
    except Exception as e:
        print(f"FAILED: {e}")

# -------------------------------------------------------------------
def remove_impossible_dates(cursor):
    """
    daily_analytics got rows up to 2047 because of a date bug in
    generate.py. Anything after today is definitely wrong.
    """
    print("\n  [clean] removing future-dated rows from daily_analytics")
    for tbl in ("daily_analytics", "weather_daily", "model_features_table"):
        try:
            run(cursor, f"DELETE FROM {tbl} WHERE recorded_date > CURDATE()")
            print(f"          {tbl}: deleted {cursor.rowcount:,} rows")
        except Exception as e:
            print(f"          {tbl}: skipped ({e})")

# -------------------------------------------------------------------
def fix_planting_date(cursor):
    """
    generate.py builds data from 2020-01-01 but planting_record says
    2026-01-01. Fix the record so DAP is positive everywhere.
    """
    print("\n  [clean] aligning planting_date to earliest sensor data")
    run(cursor, "SELECT MIN(DATE(recorded_at)) FROM sensor_reading")
    row = cursor.fetchone()
    if not row or not row[0]:
        print("          no sensor data — skipping")
        return
    earliest = row[0]
    print(f"          earliest sensor date: {earliest}")
    run(cursor, "UPDATE planting_record SET planting_date = %s WHERE cycle_id = 1",
        (earliest,))
    print(f"          updated {cursor.rowcount} planting_record row(s)")

# -------------------------------------------------------------------
def main():
    print("=" * 60)
    print(" Duplicate cleanup — will modify your DB")
    print("=" * 60)
    ans = input("Type YES to continue: ").strip()
    if ans != "YES":
        print("Aborted.")
        sys.exit(0)

    db = get_db_connection()
    cursor = db.cursor()

    try:
        print("\n--- 1. BACKUPS ---")
        for t in DEDUP:
            backup(cursor, t)
        db.commit()

        print("\n--- 2. DEDUPLICATION ---")
        for t, cols in DEDUP.items():
            dedup(cursor, t, cols)
            db.commit()

        print("\n--- 3. UNIQUE KEYS ---")
        for t, cols in DEDUP.items():
            add_unique_key(cursor, t, cols)
        db.commit()

        print("\n--- 4. IMPOSSIBLE DATES ---")
        remove_impossible_dates(cursor)
        db.commit()

        print("\n--- 5. PLANTING DATE ---")
        fix_planting_date(cursor)
        db.commit()

        print("\n--- FINAL COUNTS ---")
        for t in DEDUP:
            print(f"  {t:<25} {count(cursor, t):>10,}")

        print("\nDone. Backups are named <table>_bak.")
        print("Drop them with DROP TABLE <name>_bak; once you're confident.")

    except Exception as e:
        db.rollback()
        print(f"\n!! ERROR, rolled back: {e}")
        raise
    finally:
        cursor.close()
        db.close()

if __name__ == "__main__":
    main()