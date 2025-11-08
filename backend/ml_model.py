import sqlite3
import pandas as pd
from sklearn.linear_model import LinearRegression
from sklearn.model_selection import train_test_split
from sklearn.metrics import mean_squared_error
import joblib
from backend.database import get_db_path

def train_model():
    db_path = get_db_path()
    conn = sqlite3.connect(db_path)
    df = pd.read_sql_query("SELECT * FROM vessel_data", conn)
    conn.close()

    if df.empty:
        print("No data available to train the model.")
        return

    # Feature engineering
    df['scheduled_departure'] = pd.to_datetime(df['scheduled_departure'], errors='coerce', utc=True)
    df['left_dock'] = pd.to_datetime(df['left_dock'], errors='coerce', utc=True)

    # Drop rows where conversion failed
    df = df.dropna(subset=['scheduled_departure', 'left_dock'])

    df['delay'] = (df['left_dock'] - df['scheduled_departure']).dt.total_seconds() / 60

    # For simplicity, we'll use a few features. This can be expanded later.
    features = ['speed', 'heading', 'at_dock']
    target = 'delay'

    # Drop rows with missing values in features or target
    df = df.dropna(subset=features + [target])

    if df.empty:
        print("No data left after dropping rows with missing values.")
        return

    X = df[features]
    y = df[target]

    X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)

    model = LinearRegression()
    model.fit(X_train, y_train)

    # Evaluate the model
    y_pred = model.predict(X_test)
    mse = mean_squared_error(y_test, y_pred)
    rmse = mse ** 0.5
    print(f"Model RMSE: {rmse}")

    # Save the model
    joblib.dump(model, 'ferry_delay_model.pkl')

def predict_delay(features):
    model = joblib.load('ferry_delay_model.pkl')
    return model.predict(features)

if __name__ == "__main__":
    train_model()
