# model.py
import pandas as pd
import warnings
from database import get_db_connection
from tabpfn import TabPFNClassifier

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

    # Isolate metadata columns
    metadata_cols = ['recorded_date', 'plot_id']
    
    # Define exactly 28 features Matrix
    X = df.drop(columns=metadata_cols, errors='ignore')
    
    # Derive target synthetically from historical measured depletion
    y = (df['depletion_ratio_measured'] > 0.5).astype(int) 

    # Split: All rows except latest for training, latest row for prediction
    X_train = X.iloc[:-1] 
    y_train = y.iloc[:-1]
    X_today = X.iloc[[-1]] 

    # TabPFN is a zero-shot model, fitting configures the context
    classifier = TabPFNClassifier(device='cpu')
    classifier.fit(X_train, y_train)
    
    probability = classifier.predict_proba(X_today)[0][1]
    decision = 1 if probability > 0.7 else 0
    
    # Get corresponding daily_analytics ID for the foreign key
    cursor = db.cursor(dictionary=True)
    cursor.execute("SELECT analytics_id FROM daily_analytics WHERE recorded_date = %s ORDER BY analytics_id DESC LIMIT 1", (target_date,))
    analytics_id = cursor.fetchone()['analytics_id']

    # Insert Prediction
    cursor.execute(
        "INSERT INTO prediction (plot_id, analytics_id, probability, decision, model_version) VALUES (%s, %s, %s, %s, %s)",
        (1, analytics_id, float(probability), decision, "tabpfn-v2-28feat")
    )
    db.commit()
    db.close()
    
    print(f"[MODEL] Inference complete. Probability: {probability:.2f} | Decision: {decision}")