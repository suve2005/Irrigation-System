# cleanup_duplicates_v2.py
"""
Second pass. Only touches daily_analytics and model_features_table.
Handles the FK from prediction.analytics_id -> daily_analytics.analytics_id.
Safe to re-run; skips anything already clean.
"""
import sys
from database import get_db_connection


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
          AND table_name = %s AND index_name = %s
    """, (table, index_name))
    return cursor.fetchone()[0] > 0


def dedup_with_fk_off(cursor, table, key_cols, id_col):
    """
    Deduplicate `table`, keeping the lowest `id_col` per key group.
    Wraps the swap in SET FOREIGN_KEY_CHECKS=0/1 so child tables
    (like prediction) don't block the DELETE.
    """
    print(f"\n  [dedup] {table}  (key: {key_cols})")
    before = count(cursor, table)
    print(f"          rows before: {before:,}")

    key_list = ", ".join(f"`{c}`" for c in key_cols)

    # 1. Build the keep-list
    print(f"          building keep-list ...", end=" ", flush=True)
    run(cursor, f"""
        CREATE TEMPORARY TABLE tmp_keep AS
        SELECT MIN(`{id_col}`) AS keep_id
        FROM {table}
        GROUP BY {key_list}
    """)
    print("done")

    # 2. Materialize the survivor rows
    print(f"          materializing survivors ...", end=" ", flush=True)
    run(cursor, f"""
        CREATE TEMPORARY TABLE tmp_dedup AS
        SELECT t.* FROM {table} t
        JOIN tmp_keep k ON t.`{id_col}` = k.keep_id
    """)
    after = count(cursor, "tmp_dedup")
    print(f"done ({after:,} rows)")

    if after == before:
        print(f"          no duplicates — skipping swap")
        run(cursor, "DROP TEMPORARY TABLE tmp_keep")
        run(cursor, "DROP TEMPORARY TABLE tmp_dedup")
        return

    # 3. Swap with FKs temporarily off
    print(f"          swapping (FK checks off) ...", end=" ", flush=True)
    run(cursor, "SET FOREIGN_KEY_CHECKS = 0")
    try:
        run(cursor, f"DELETE FROM {table}")
        cursor.execute(f"SHOW COLUMNS FROM tmp_dedup")
        cols = [c[0] for c in cursor.fetchall()]
        col_list = ", ".join(f"`{c}`" for c in cols)
        run(cursor, f"INSERT INTO {table} ({col_list}) SELECT {col_list} FROM tmp_dedup")
    finally:
        run(cursor, "SET FOREIGN_KEY_CHECKS = 1")
    print("done")

    run(cursor, "DROP TEMPORARY TABLE tmp_keep")
    run(cursor, "DROP TEMPORARY TABLE tmp_dedup")
    print(f"          rows after : {after:,}  (removed {before - after:,})")


def clean_orphan_predictions(cursor):
    """After dedup, some prediction rows point at analytics_ids that no longer exist."""
    print(f"\n  [clean] removing orphan predictions ...", end=" ", flush=True)
    run(cursor, """
        DELETE p FROM prediction p
        LEFT JOIN daily_analytics da ON p.analytics_id = da.analytics_id
        WHERE da.analytics_id IS NULL
    """)
    print(f"done ({cursor.rowcount:,} orphan(s) removed)")


def add_unique_key(cursor, table, key_cols):
    idx_name = "uq_" + "_".join(key_cols)
    if index_exists(cursor, table, idx_name):
        print(f"  [index] {idx_name} already on {table}")
        return
    key_list = ", ".join(f"`{c}`" for c in key_cols)
    print(f"  [index] adding {idx_name} on {table} ...", end=" ", flush=True)
    try:
        run(cursor, f"ALTER TABLE {table} ADD UNIQUE KEY {idx_name} ({key_list})")
        print("done")
    except Exception as e:
        print(f"FAILED: {e}")


def main():
    print("=" * 60)
    print(" Cleanup pass 2 — daily_analytics & model_features_table")
    print("=" * 60)
    if input("Type YES to continue: ").strip() != "YES":
        print("Aborted."); sys.exit(0)

    db = get_db_connection()
    cursor = db.cursor()
    try:
        # daily_analytics first (child table prediction references it)
        dedup_with_fk_off(cursor, "daily_analytics",
                          ["plot_id", "cycle_id", "recorded_date"],
                          "analytics_id")
        db.commit()

        clean_orphan_predictions(cursor)
        db.commit()

        # model_features_table has no children referencing it
        dedup_with_fk_off(cursor, "model_features_table",
                          ["plot_id", "recorded_date", "hour_of_day"],
                          "feature_id")
        db.commit()

        # Add unique keys
        print("\n--- UNIQUE KEYS ---")
        add_unique_key(cursor, "daily_analytics",
                       ["plot_id", "cycle_id", "recorded_date"])
        add_unique_key(cursor, "model_features_table",
                       ["plot_id", "recorded_date", "hour_of_day"])
        db.commit()

        print("\n--- FINAL COUNTS ---")
        for t in ("sensor_reading", "weather_daily",
                  "daily_analytics", "model_features_table", "prediction"):
            print(f"  {t:<25} {count(cursor, t):>10,}")

        print("\nDone.")
    except Exception as e:
        db.rollback()
        print(f"\n!! ERROR (rolled back): {e}")
        raise
    finally:
        cursor.close()
        db.close()


if __name__ == "__main__":
    main()