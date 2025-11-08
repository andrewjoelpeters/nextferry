# Machine Learning Model for Ferry Delay Prediction

This document provides an overview of the machine learning model used to predict ferry delays in the VesselWatch application.

## Model Function Signature

The prediction model is a simple linear regression model. The function signature for making predictions is:

```python
def predict_delay(features):
    """
    Predicts the delay in minutes for a given set of features.

    Args:
        features (pandas.DataFrame): A DataFrame containing the features for prediction.
            The required columns are 'speed', 'heading', and 'at_dock'.

    Returns:
        numpy.ndarray: An array of predicted delays in minutes.
    """
```

## Model Training

The model is trained on historical vessel data collected from the WSDOT API. The training process involves the following steps:

1.  **Data Loading:** The historical data is loaded from a SQLite database (`ferry_data.db`).
2.  **Feature Engineering:** The `delay` is calculated by subtracting the `scheduled_departure` from the `left_dock` time.
3.  **Model Training:** A linear regression model is trained on the data using the `speed`, `heading`, and `at_dock` features to predict the `delay`.
4.  **Model Saving:** The trained model is saved to a file named `ferry_delay_model.pkl`.

### Daily Re-training

Currently, the model is trained on a static dataset. A future improvement will be to set up a daily re-training pipeline to keep the model up-to-date with the latest data.

## Data Storage and Access

The historical vessel data is stored in a SQLite database named `ferry_data.db`. The database is populated by a background task that collects data from the WSDOT API every five minutes. The data is stored in the `vessel_data` table.

## Evaluation

The ML model was evaluated against the existing rule-based logic using the root mean squared error (RMSE) of the predicted departure time vs. the actual departure time. The results are as follows:

| Model              | RMSE |
| ------------------ | ---- |
| ML Model           | 1.58 |
| Rule-based Model   | 2.43 |

As the results show, the ML model provides a significant improvement in prediction accuracy over the rule-based logic.
