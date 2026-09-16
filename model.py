# model.py
import pandas as pd
import warnings
import torch
from database import get_db_connection
from tabpfn import TabPFNClassifier

# Hide the Pandas SQL warning to keep the terminal clean
warnings.filterwarnings('ignore', category=UserWarning)

def run_inference_from_db(target_date):
    """
    Step 3: Fetch engineered features from DB, run TabPFN, log prediction.
    """
    db = get_db_connection()
    
    # Request data from the database (Table) instead of feature engineering
    query = "SELECT eto, dap, kc, depletion_ratio_measured FROM daily_analytics"
    df = pd.read_sql(query, db)
    
    if df.empty or len(df) < 100:
        print("[MODEL] Not enough historical data in DB for TabPFN.")
        db.close()
        return

    # Prepare Context (Historical) vs Current Row (Target Date)
    X = df.drop(columns=['target_irrigate'], errors='ignore')
    # Synthetic target for the sake of the pipeline
    y = (df['depletion_ratio_measured'] > 0.5).astype(int) 

    X_train = X.iloc[:-1] # History
    y_train = y.iloc[:-1]
    X_today = X.iloc[[-1]] # Latest row fetched from DB

    # Run Model - Removed N_ensemble to fix the TypeError
    classifier = TabPFNClassifier(device='cuda')
    classifier.fit(X_train, y_train)
    
    # Predict probability for class 1 (Irrigate)
    probability = classifier.predict_proba(X_today)[0][1]
    decision = 1 if probability > 0.7 else 0
    
    # Save Prediction to DB
    cursor = db.cursor()
    cursor.execute(
        "INSERT INTO prediction (probability, decision, model_version) VALUES (%s, %s, %s)",
        (float(probability), decision, "tabpfn-v1")
    )
    db.commit()
    db.close()
    
    print(f"[MODEL] Inference complete. Probability: {probability:.2f} | Decision: {decision}")