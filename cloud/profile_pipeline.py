# profile_pipeline.py
"""
Benchmark the pipeline stages (feature engineering -> model features -> inference)
WITHOUT modifying any of the original files.
"""
from datetime import date, timedelta

from benchmark import profile, tracemalloc_diff, timer

# --- Your real modules (imported, not modified) ---
import feature_engineering as fe
import populate_model_features as pmf

try:
    import model as mdl
    HAVE_MODEL = True
except Exception as e:
    print(f"[WARN] Could not import model.py ({e}). Skipping inference benchmark.")
    HAVE_MODEL = False


TARGET_DATE = date.today()
PLOT_ID = 1
CYCLE_ID = 1


def run_feature_eng():
    fe.calculate_and_store_features(plot_id=PLOT_ID,
                                    cycle_id=CYCLE_ID,
                                    target_date=TARGET_DATE)


def run_populate():
    pmf.populate_model_features()


def run_inference():
    mdl.run_inference_from_db(target_date=TARGET_DATE)


if __name__ == "__main__":
    # 1) Feature engineering hits NASA / SoilGrids / elevation APIs,
    #    so keep iterations low. It also writes to the DB — if your
    #    schema has a unique constraint on (plot_id, recorded_date)
    #    you may want to pick a target_date that has not been written yet.
    profile(run_feature_eng, iterations=3, warmup=1, label="feature_engineering")

    # 2) populate_model_features is DB-heavy — safe to loop more.
    profile(run_populate, iterations=10, warmup=2, label="populate_model_features")

    # 3) TabPFN inference (also DB heavy).
    if HAVE_MODEL:
        profile(run_inference, iterations=5, warmup=1, label="model_inference")

        # If any stage above flagged "POSSIBLE LEAK", drill in with tracemalloc:
        tracemalloc_diff(run_inference, iterations=5, top=15)

    # 4) Sanity check: single-shot timer around a whole block
    with timer("full pipeline (one shot)"):
        run_feature_eng()
        run_populate()
        if HAVE_MODEL:
            run_inference()