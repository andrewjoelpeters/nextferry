import sqlite3
import pandas as pd
import numpy as np
from sklearn.linear_model import LinearRegression
from sklearn.model_selection import train_test_split
from sklearn.metrics import mean_squared_error
from sklearn.compose import ColumnTransformer
from sklearn.preprocessing import OneHotEncoder, StandardScaler
from sklearn.pipeline import Pipeline
import joblib
from backend.database import get_db_path
from pydantic import BaseModel, ConfigDict
from typing import List, Optional
from datetime import datetime

class PredictionFeatures(BaseModel):
    model_config = ConfigDict(arbitrary_types_allowed=True)

    speed: float
    heading: float
    at_dock: bool
    scheduled_departure: datetime
    departing_terminal_id: int
    arriving_terminal_id: int

def load_data():
    db_path = get_db_path()
    conn = sqlite3.connect(db_path)
    df = pd.read_sql_query("SELECT * FROM vessel_data", conn)
    conn.close()
    return df

def engineer_features(df):
    df = df.copy()
    df['scheduled_departure'] = pd.to_datetime(df['scheduled_departure'], errors='coerce', utc=True)

    # Drop rows with invalid scheduled_departure
    df = df.dropna(subset=['scheduled_departure'])

    # Features derived from scheduled_departure
    df['hour_of_day'] = df['scheduled_departure'].dt.hour
    df['day_of_week'] = df['scheduled_departure'].dt.dayofweek

    # If 'left_dock' is present, we calculate the target 'delay'
    if 'left_dock' in df.columns:
        df['left_dock'] = pd.to_datetime(df['left_dock'], errors='coerce', utc=True)
        # Drop rows where we can't calculate delay
        df = df.dropna(subset=['left_dock'])
        df['delay'] = (df['left_dock'] - df['scheduled_departure']).dt.total_seconds() / 60

    return df

def train_and_save_model(df):
    numeric_features = ['speed', 'heading', 'hour_of_day']
    categorical_features = ['at_dock', 'day_of_week', 'departing_terminal_id', 'arriving_terminal_id']
    target = 'delay'

    all_features = numeric_features + categorical_features
    df = df.dropna(subset=all_features + [target])

    if df.empty:
        print("No data left after dropping rows with missing values.")
        return

    # Sort by departure time to prevent data leakage
    df = df.sort_values(by='scheduled_departure')

    X = df[all_features]
    y = df[target]

    # Split data into training and testing sets based on time
    train_size = int(0.8 * len(df))
    X_train = X.iloc[:train_size]
    X_test = X.iloc[train_size:]
    y_train = y.iloc[:train_size]
    y_test = y.iloc[train_size:]

    # Preprocessing pipeline
    preprocessor = ColumnTransformer(
        transformers=[
            ('num', StandardScaler(), numeric_features),
            ('cat', OneHotEncoder(handle_unknown='ignore'), categorical_features)
        ]
    )

    # Full pipeline with model
    model_pipeline = Pipeline(steps=[
        ('preprocessor', preprocessor),
        ('regressor', LinearRegression())
    ])

    model_pipeline.fit(X_train, y_train)

    y_pred = model_pipeline.predict(X_test)
    mse = mean_squared_error(y_test, y_pred)
    rmse = mse ** 0.5
    print(f"Model RMSE: {rmse}")

    joblib.dump(model_pipeline, 'ferry_delay_model.pkl')
    print("Model saved to ferry_delay_model.pkl")

_MODEL_CACHE = None

def predict_delay(features: List[PredictionFeatures]):
    global _MODEL_CACHE
    if _MODEL_CACHE is None:
        try:
            _MODEL_CACHE = joblib.load('ferry_delay_model.pkl')
        except FileNotFoundError:
            print("Model file not found. Please train the model first.")
            return np.zeros(len(features))

    df = pd.DataFrame([f.model_dump() for f in features])
    df = engineer_features(df)

    # Ensure all required features are present
    required_features = ['speed', 'heading', 'hour_of_day', 'at_dock', 'day_of_week', 'departing_terminal_id', 'arriving_terminal_id']
    return _MODEL_CACHE.predict(df[required_features])

def main():
    df = load_data()
    if df.empty:
        print("No data available to train the model.")
        return
    df = engineer_features(df)
    train_and_save_model(df)

if __name__ == "__main__":
    main()
