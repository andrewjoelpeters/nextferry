import sqlite3
import pandas as pd
from sklearn.metrics import mean_squared_error
import joblib
from backend.database import get_db_path
from backend.ml_model import engineer_features

def load_data():
    db_path = get_db_path()
    conn = sqlite3.connect(db_path)
    df = pd.read_sql_query("SELECT * FROM vessel_data", conn)
    conn.close()
    return df

def predict_delays(df):
    numeric_features = ['speed', 'heading', 'hour_of_day']
    categorical_features = ['at_dock', 'day_of_week', 'departing_terminal_id', 'arriving_terminal_id']
    all_features = numeric_features + categorical_features

    # We need 'delay' for the rule-based prediction shift,
    # and it was already calculated in engineer_features as 'delay'
    df_features = df.dropna(subset=all_features + ['delay'])
    if df_features.empty:
        print("No data available for prediction after dropping NaNs.")
        return df

    try:
        ml_model = joblib.load('ferry_delay_model.pkl')
    except FileNotFoundError:
        print("Model file not found. Please train the model first.")
        return df

    df_features['ml_predicted_delay'] = ml_model.predict(df_features[all_features])

    # Simple rule-based model: use the previous delay for the same vessel
    # Sort by scheduled_departure to ensure shift makes sense
    df_features = df_features.sort_values(by=['vessel_id', 'scheduled_departure'])
    df_features['rule_based_predicted_delay'] = df_features.groupby('vessel_id')['delay'].transform('shift').fillna(0)

    return pd.merge(df, df_features[['id', 'ml_predicted_delay', 'rule_based_predicted_delay']], on='id', how='left')

def evaluate_and_save_results(df):
    if 'ml_predicted_delay' not in df.columns or 'rule_based_predicted_delay' not in df.columns:
        print("Predictions missing. Cannot evaluate.")
        return

    df = df.dropna(subset=['ml_predicted_delay', 'rule_based_predicted_delay', 'delay'])

    # Use 'timestamp' or something else as reference for horizon?
    # Original evaluation used (scheduled_departure - left_dock), which is -delay.
    # That doesn't seem right for "prediction horizon".
    # Usually, prediction horizon is how far in the future we are predicting from "now".
    # But in historical data, we don't have a clear "now".
    # Let's keep the original logic if it's what they wanted, or just do a global RMSE.

    ml_rmse = mean_squared_error(df['delay'], df['ml_predicted_delay']) ** 0.5
    rule_based_rmse = mean_squared_error(df['delay'], df['rule_based_predicted_delay']) ** 0.5

    print(f"Overall ML RMSE: {ml_rmse:.2f}")
    print(f"Overall Rule-based RMSE: {rule_based_rmse:.2f}")

    with open("evaluation_results.md", "w") as f:
        f.write("# Model Evaluation Results\n\n")
        f.write("| Model | RMSE |\n")
        f.write("|---|---|\n")
        f.write(f"| ML Model | {ml_rmse:.2f} |\n")
        f.write(f"| Rule-based Model | {rule_based_rmse:.2f} |\n")

def main():
    df = load_data()
    if df.empty:
        print("No data available for evaluation.")
        return
    df = engineer_features(df)
    df = predict_delays(df)
    evaluate_and_save_results(df)

if __name__ == "__main__":
    main()
