# CarbonIQ Machine Learning Model Directory

This directory holds the pre-trained ML model artifact and metadata for emission trend forecasting.

## Expected Artifacts

1. `emission_trend_model.joblib` (or `.pkl`)
   - Pre-trained supervised regression model (e.g., scikit-learn, XGBoost, or Ridge regression).
   - Trained externally to forecast future monthly emissions based on historical activity and temporal features.

2. `model_metadata.json`
   - Metadata schema defining feature names, feature order, model version, and validation metrics:
   ```json
   {
     "model_name": "CarbonIQ Monthly Emissions Forecaster",
     "model_version": "1.0.0",
     "algorithm": "RidgeRegression",
     "feature_names": [
       "month",
       "quarter",
       "lag_1_emissions",
       "lag_2_emissions",
       "rolling_3m_mean",
       "electricity_emissions_kg",
       "transportation_emissions_kg",
       "waste_emissions_kg"
     ],
     "metrics": {
       "mae_kg": 42.5,
       "rmse_kg": 58.2,
       "r2_score": 0.88,
       "std_err": 24.1
     },
     "description": "Trained on historical institutional monthly emissions datasets."
   }
   ```

## Production Safeguards

- The backend will **never** train models at startup.
- If the artifact is absent, the backend responds with `status: "model_artifact_missing"` and does **not** fabricate fake predictions.

