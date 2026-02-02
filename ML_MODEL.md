# Machine Learning Model for Ferry Delay Prediction

This document provides an overview of the machine learning model used to predict ferry delays in the VesselWatch application.

## Model Function Signature

The prediction model uses a scikit-learn Pipeline. The function signature for making predictions is:

```python
def predict_delay(features: List[PredictionFeatures]):
    """
    Predicts the delay in minutes for a given set of features.

    Args:
        features (List[PredictionFeatures]): A list of PredictionFeatures objects.
            Required fields: speed, heading, at_dock, scheduled_departure,
            departing_terminal_id, arriving_terminal_id.

    Returns:
        numpy.ndarray: An array of predicted delays in minutes.
    """
```

## Model Training

The model is trained on historical vessel data collected from the WSDOT API. The training process involves the following steps:

1.  **Data Loading:** The historical data is loaded from a SQLite database (`ferry_data.db`).
2.  **Feature Engineering:**
    - `delay` is calculated as the target variable (difference between `left_dock` and `scheduled_departure`).
    - `hour_of_day` and `day_of_week` are extracted from `scheduled_departure`.
3.  **Model Training:** A `Pipeline` is used, consisting of:
    - **Preprocessing:** `ColumnTransformer` that applies `StandardScaler` to numeric features (`speed`, `heading`, `hour_of_day`) and `OneHotEncoder` to categorical features (`at_dock`, `day_of_week`, `departing_terminal_id`, `arriving_terminal_id`).
    - **Regressor:** A `LinearRegression` model.
4.  **Model Saving:** The trained pipeline is saved to `ferry_delay_model.pkl`.

### Daily Re-training

Currently, the model is trained on a static dataset. A future improvement will be to set up a daily re-training pipeline to keep the model up-to-date with the latest data.

## Data Storage and Access

The historical vessel data is stored in a SQLite database named `ferry_data.db`. The database is populated by a background task that collects data from the WSDOT API every five minutes. The data is stored in the `vessel_data` table.

## Evaluation

The ML model is evaluated against a simple rule-based model (which assumes the next sailing's delay will be the same as the previous one for that vessel).

Latest evaluation results:

| Model | RMSE |
|---|---|
| ML Model | 5.41 |
| Rule-based Model | 5.47 |

*Note: Results are based on generated mock data for demonstration purposes.*
