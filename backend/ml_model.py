import sqlite3
import pandas as pd
from sklearn.linear_model import LinearRegression
from sklearn.model_selection import train_test_split
from sklearn.metrics import mean_squared_error
import joblib
from backend.database import get_db_path
from pydantic import BaseModel
from typing import List

class PredictionFeatures(BaseModel):
    speed: float
    heading: float
    at_dock: bool

def load_data():
    db_path = get_db_path()
    conn = sqlite3.connect(db_path)
    df = pd.read_sql_query("SELECT * FROM vessel_data", conn)
    conn.close()
    return df

def engineer_features(df):
    df['scheduled_departure'] = pd.to_datetime(df['scheduled_departure'], errors='coerce', utc=True)
    df['left_dock'] = pd.to_datetime(df['left_dock'], errors='coerce', utc=True)
    df = df.dropna(subset=['scheduled_departure', 'left_dock'])
    df['delay'] = (df['left_dock'] - df['scheduled_departure']).dt.total_seconds() / 60
    return df

def train_and_save_model(df):
    features = ['speed', 'heading', 'at_dock']
    target = 'delay'
    df = df.dropna(subset=features + [target])

    if df.empty:
        print("No data left after dropping rows with missing values.")
        return

    # Sort by departure time to prevent data leakage
    df = df.sort_values(by='scheduled_departure')

    # Split data into training and testing sets based on time
    train_size = int(0.8 * len(df))
    train_df = df.iloc[:train_size]
    test_df = df.iloc[train_size:]

    X_train = train_df[features]
    y_train = train_df[target]
    X_test = test_df[features]
    y_test = test_df[target]

    model = LinearRegression()
    model.fit(X_train, y_train)

    y_pred = model.predict(X_test)
    mse = mean_squared_error(y_test, y_pred)
    rmse = mse ** 0.5
    print(f"Model RMSE: {rmse}")

    joblib.dump(model, 'ferry_delay_model.pkl')

def predict_delay(features: List[PredictionFeatures]):
    model = joblib.load('ferry_delay_model.pkl')
    df = pd.DataFrame([f.dict() for f in features])
    return model.predict(df)

def main():
    df = load_data()
    if df.empty:
        print("No data available to train the model.")
        return
    df = engineer_features(df)
    train_and_save_model(df)

if __name__ == "__main__":
    main()
