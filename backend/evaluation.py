import sqlite3
import pandas as pd
from sklearn.metrics import mean_squared_error
import joblib
from backend.database import get_db_path

def load_data():
    db_path = get_db_path()
    conn = sqlite3.connect(db_path)
    df = pd.read_sql_query("SELECT * FROM vessel_data", conn)
    conn.close()
    return df

def prepare_data(df):
    df['scheduled_departure'] = pd.to_datetime(df['scheduled_departure'], errors='coerce', utc=True)
    df['left_dock'] = pd.to_datetime(df['left_dock'], errors='coerce', utc=True)
    df = df.dropna(subset=['scheduled_departure', 'left_dock'])
    df['actual_delay'] = (df['left_dock'] - df['scheduled_departure']).dt.total_seconds() / 60
    return df

def predict_delays(df):
    features = ['speed', 'heading', 'at_dock']
    df_features = df.dropna(subset=features)
    ml_model = joblib.load('ferry_delay_model.pkl')
    df_features['ml_predicted_delay'] = ml_model.predict(df_features[features])
    df_features['rule_based_predicted_delay'] = df_features.groupby('vessel_id')['actual_delay'].transform('shift').fillna(0)
    return pd.merge(df, df_features[['id', 'ml_predicted_delay', 'rule_based_predicted_delay']], on='id', how='left')

def evaluate_and_save_results(df):
    df = df.dropna(subset=['ml_predicted_delay', 'rule_based_predicted_delay'])
    df['prediction_horizon'] = (df['scheduled_departure'] - df['left_dock']).dt.total_seconds() / 60

    bins = [-60, -30, -15, -5, 0]
    labels = ['30-60', '15-30', '5-15', '0-5']
    df['horizon_group'] = pd.cut(df['prediction_horizon'], bins=bins, labels=labels, right=False)

    results = []
    for group in labels:
        subset = df[df['horizon_group'] == group]
        if not subset.empty:
            ml_rmse = mean_squared_error(subset['actual_delay'], subset['ml_predicted_delay']) ** 0.5
            rule_based_rmse = mean_squared_error(subset['actual_delay'], subset['rule_based_predicted_delay']) ** 0.5
            results.append((group, ml_rmse, rule_based_rmse))

    with open("evaluation_results.md", "w") as f:
        f.write("# Model Evaluation Results\n\n")
        f.write("| Prediction Horizon (minutes) | ML Model RMSE | Rule-based Model RMSE |\n")
        f.write("|---|---|---|\n")
        for group, ml_rmse, rule_based_rmse in results:
            f.write(f"| {group} | {ml_rmse:.2f} | {rule_based_rmse:.2f} |\n")

def main():
    df = load_data()
    if df.empty:
        print("No data available for evaluation.")
        return
    df = prepare_data(df)
    df = predict_delays(df)
    evaluate_and_save_results(df)

if __name__ == "__main__":
    main()
