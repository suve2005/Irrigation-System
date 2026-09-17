import pandas as pd
import numpy as np
import torch
import gc
from database import get_db_connection
from tabpfn import TabPFNRegressor

def run_inference_from_db(target_date):
    db = get_db_connection()
    
    # FETCH DATA
    query = "SELECT analytics_id, eto, dap, kc, depletion_ratio_measured, target_water_mm FROM daily_analytics"
    df = pd.read_sql(query, db)
    db.close()
    
    # Keep the last 1000 rows to optimize VRAM
    df = df.tail(1000).reset_index(drop=True)
    
    if df.empty or len(df) < 50:
        print("[MODEL] Not enough data in database.")
        return

    # PREPARE DATA - Convert to float32 for CUDA compatibility
    X = df[['eto', 'dap', 'kc', 'depletion_ratio_measured']].astype(np.float32)
    y = df['target_water_mm'].astype(np.float32)

    X_train = X.iloc[:-1].values
    y_train = y.iloc[:-1].values
    X_today = X.iloc[[-1]].values
    current_analytics_id = int(df.iloc[-1]['analytics_id'])

    device = 'cuda' if torch.cuda.is_available() else 'cpu'
    print(f"[MODEL] Executing inference on device: {device.upper()}")
    
    if device == 'cuda':
        torch.cuda.empty_cache()

    regressor = None
    try:
        # FIXED: Removed N_ensemble parameter
        regressor = TabPFNRegressor(device=device)
        regressor.fit(X_train, y_train)
        
        water_needed_mm = float(regressor.predict(X_today)[0])
        water_needed_mm = max(0.0, round(water_needed_mm, 2))
        
        # Calculate pump run time (10 m² plot, 5 L/min pump)
        water_liters = water_needed_mm * 10
        run_time_min = int(water_liters / 5)

        # WRITE PREDICTION TO DB
        db_write = get_db_connection()
        cursor = db_write.cursor()
        cursor.execute(
            "INSERT INTO prediction (plot_id, analytics_id, water_needed_mm, pump_run_time_min, model_version) VALUES (1, %s, %s, %s, %s)",
            (current_analytics_id, water_needed_mm, run_time_min, "tabpfn-reg-v1")
        )
        db_write.commit()
        cursor.close()
        db_write.close()
        
        print(f"[MODEL SUCCESS] Water needed: {water_needed_mm} mm. Pump run time: {run_time_min} mins.")
        
    finally:
        # Safe cleanup block
        if regressor is not None:
            del regressor
        if device == 'cuda':
            torch.cuda.empty_cache()
        gc.collect()