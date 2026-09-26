# model.py 
from populate_model_features import populate_model_features
import pandas as pd
import warnings
from database import get_db_connection
from tabpfn import TabPFNClassifier # regression

warnings.filterwarnings('ignore', category=UserWarning)

def run_inference_from_db(target_date):
    db = get_db_connection()
    
    # Query the comprehensive view containing all 28 features
    query = "SELECT * FROM model_features_view ORDER BY recorded_date ASC"
    df = pd.read_sql(query, db)
    
    if df.empty or len(df) < 100:
        print("[MODEL] Not enough historical data in DB for TabPFN. Minimum 100 required.")
        db.close()
        return

    drop_cols = [        # columns to drop from X(training)
        "recorded_date", "plot_id", "feature_id",
        "depletion_ratio_measured",
        "depletion_ratio_simulated",
        "sim_vs_measured_deviation",
    ]
    X = df.drop(columns=[c for c in drop_cols if c in df.columns])
    X = X.select_dtypes(include="number")
    y = (df["depletion_ratio_measured"] > 0.5).astype(int)

    # Split: All rows except latest for training, latest row for prediction
    X_train = X.iloc[:-1] 
    y_train = y.iloc[:-1]
    X_today = X.iloc[[-1]] 

    # TabPFN is a zero-shot model, fitting configures the context
    classifier = TabPFNClassifier(device='cuda')
    classifier.fit(X_train, y_train)
    
    probability = classifier.predict_proba(X_today)[0][1]
    decision = 1 if probability > 0.7 else 0
    

    # Get analytics_id AND the values to compute time.
    # filter by plot_id to not pick the wrong row.
    cursor = db.cursor(dictionary=True)
    cursor.execute("""
        SELECT da.analytics_id, da.depletion_ratio_measured, sp.taw
        FROM daily_analytics da
        JOIN soil_profile sp ON sp.plot_id = da.plot_id
        WHERE da.plot_id = %s AND da.recorded_date = %s
        ORDER BY da.analytics_id DESC LIMIT 1
    """, (1, target_date))
    row = cursor.fetchone()

    if not row:
        print(f"[MODEL] No analytics row for {target_date}")
        db.close()
        return

    analytics_id = row["analytics_id"]

    # Work out how much water to add and how long to run the pump.
    SYSTEM_EFFICIENCY   = 0.90   # drip irrigation
    AREA_M2             = 100.0  # plot size
    FLOW_RATE_L_PER_MIN = 20.0   # pump flow

    if decision == 1 and row["depletion_ratio_measured"] is not None:
        dr_ratio = max(0.0, min(1.0, float(row["depletion_ratio_measured"])))
        dr_mm = dr_ratio * float(row["taw"])                    # water missing from root zone
        water_needed_mm = round(dr_mm / SYSTEM_EFFICIENCY, 2)   # add extra for drip losses
        volume_litres = water_needed_mm * AREA_M2
        pump_run_time_min = int(round(volume_litres / FLOW_RATE_L_PER_MIN))
    else:
        # Model said hold, or we have no depletion value -> no irrigation
        water_needed_mm = 0.0
        pump_run_time_min = 0

    # Fixed insertion, now adds these, water_needed_mm, pump_run_time_min, model_version, predicted_at
    cursor.execute("""
        INSERT INTO prediction
            (plot_id, analytics_id, probability, decision,
            water_needed_mm, pump_run_time_min, model_version, predicted_at)
        VALUES (%s, %s, %s, %s, %s, %s, %s, NOW())
    """, (1, analytics_id, float(probability), decision,
        water_needed_mm, pump_run_time_min, "tabpfn-v2-28feat"))

    db.commit()
    db.close()
    
    print(f"[MODEL] Inference complete. Probability: {probability:.2f} | Decision: {decision}")
