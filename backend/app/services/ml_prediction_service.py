from collections import Counter
import json
import logging
import os
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple, Union
import warnings
import numpy as np
import pandas as pd

from app.core.config import settings
from app.schemas.ml import (
    EmissionTrendResponse,
    ForecastEmissionPoint,
    HistoricalEmissionPoint,
    ModelMetadataInfo,
)
from app.utils.dates import normalize_month

logger = logging.getLogger("carboniq.ml")

# Standard expected feature names for the trained XGBoost pipeline
EXPECTED_MODEL_FEATURES = [
    "reporting_year",
    "reporting_month",
    "month_index",
    "electricity_kwh",
    "electricity_bill_inr",
    "distance_km",
    "actual_fuel_consumed_l",
    "fuel_quantity_kg",
    "fuel_efficiency_km_per_l",
    "electricity_used_kwh_for_ev",
    "fuel_expenditure_inr",
    "passengers_on_board",
    "vehicle_capacity",
    "waste_quantity_kg",
    "disposal_cost_inr",
    "waste_emission_factor_kgco2e_per_kg",
    "electricity_source",
    "transport_mode",
    "fuel_type",
    "fuel_calculation_method",
    "waste_category",
    "treatment_method",
    "collection_provider",
    "building_department",
]


class MlPredictionService:
    """
    Service for integrating external pre-trained ML emission forecasting models.
    Loads and caches 'carboniq_emissions_model.joblib' and 'metrics.json' in memory.
    Enforces strict safeguards:
    - Never generates fake predictions.
    - Never trains or replaces models at runtime.
    - Gracefully handles missing model artifacts or insufficient historical records.
    - Uses verified historical records to establish baseline operational inputs.
    """
    _model: Optional[Any] = None
    _metadata: Optional[Dict[str, Any]] = None
    _load_attempted: bool = False
    _artifact_path_resolved: Optional[Path] = None
    _metadata_path_resolved: Optional[Path] = None

    @classmethod
    def _resolve_path(cls, configured_path: str, is_metadata: bool = False) -> Path:
        """
        Resolves path relative to backend root and app directories safely,
        independent of the current working directory.
        """
        p = Path(configured_path)
        if p.is_absolute() and p.exists():
            return p

        filename = p.name
        # Possible root candidates
        current_file = Path(__file__).resolve()
        app_dir = current_file.parents[1]       # backend/app
        backend_dir = current_file.parents[2]   # backend
        repo_root = current_file.parents[3]     # repo root

        # Check default files if configured path is not found directly
        default_names = (
            ["metrics.json", "model_metadata.json"]
            if is_metadata
            else [
                "carboniq_emissions_model.joblib",
                "emission_trend_model.joblib",
                filename,
            ]
        )
        if filename not in default_names:
            default_names.insert(0, filename)

        search_directories = [
            backend_dir,
            app_dir,
            app_dir / "models",
            repo_root / "backend",
            Path.cwd(),
            Path.cwd() / "backend",
            Path.cwd() / "backend" / "app" / "models",
        ]

        for d in search_directories:
            for fname in default_names:
                cand = d / fname
                if cand.exists():
                    return cand

        # Fallback to backend_dir / filename
        return backend_dir / filename

    @classmethod
    def load_model(cls, force_reload: bool = False) -> Tuple[Optional[Any], Optional[Dict[str, Any]]]:
        """
        Loads the pre-trained ML model once into memory and caches it.
        Safe against repeated calls, missing files, and unpickling version warnings.
        """
        if cls._model is not None and not force_reload:
            return cls._model, cls._metadata

        cls._load_attempted = True
        model_path = cls._resolve_path(settings.ML_MODEL_PATH, is_metadata=False)
        metadata_path = cls._resolve_path(settings.ML_METADATA_PATH, is_metadata=True)
        cls._artifact_path_resolved = model_path
        cls._metadata_path_resolved = metadata_path

        # 1. Load evaluation metadata from metrics.json
        if metadata_path.exists():
            try:
                with open(metadata_path, "r", encoding="utf-8") as f:
                    cls._metadata = json.load(f)
                logger.info(f"Loaded ML model evaluation metrics from {metadata_path}")
            except Exception as e:
                logger.warning(f"Could not parse model metrics at {metadata_path}: {e}")
                cls._metadata = None
        else:
            logger.info(f"ML metadata file not found at {metadata_path}.")
            cls._metadata = None

        # 2. Check if model artifact exists
        if not model_path.exists():
            logger.info(
                f"ML model artifact not found at {model_path}. "
                "Interface is active in standby mode awaiting model artifact placement."
            )
            cls._model = None
            return None, cls._metadata

        # 3. Load model artifact safely with suppressed unpickle version warnings
        ext = model_path.suffix.lower()
        try:
            if ext in [".joblib", ".pkl", ".pickle"]:
                import joblib

                with warnings.catch_warnings():
                    warnings.simplefilter("ignore")
                    cls._model = joblib.load(model_path)

                logger.info(
                    f"Successfully loaded pre-trained ML model from {model_path} [{type(cls._model).__name__}]"
                )
            else:
                logger.error(f"Unsupported model artifact format '{ext}'. Expected .joblib or .pkl.")
                cls._model = None
        except Exception as e:
            logger.error(f"Failed to deserialize ML model artifact at {model_path}: {e}")
            cls._model = None

        return cls._model, cls._metadata

    @classmethod
    def get_model_info(cls) -> ModelMetadataInfo:
        """Returns structured metadata and evaluation metrics of the pre-trained ML model."""
        model, metadata = cls.load_model()
        model_path = cls._artifact_path_resolved or cls._resolve_path(settings.ML_MODEL_PATH)
        ext = model_path.suffix.lstrip(".").lower() or "joblib"

        feature_names = None
        if model is not None and hasattr(model, "feature_names_in_"):
            feature_names = list(model.feature_names_in_)
        elif model is not None:
            feature_names = EXPECTED_MODEL_FEATURES

        feature_count = len(feature_names) if feature_names else 24

        notes = (
            "Supervised XGBoost pipeline trained on multi-source activity data. "
            f"Evaluated on {metadata.get('test_rows', 2000)}-sample test holdout "
            f"(R²={round(metadata.get('R2', 0.976), 3)}, MAE={round(metadata.get('MAE_kgCO2e', 37.5), 1)} kg CO2e)."
            if metadata
            else "Pre-trained supervised emission regression model."
        )

        return ModelMetadataInfo(
            model_name="CarbonIQ Supervised Emissions Forecasting Model",
            model_version="1.0.0" if model is not None else "unloaded",
            format=ext,
            artifact_path=str(model_path.name),
            is_loaded=model is not None,
            algorithm="XGBoost Regressor Pipeline",
            feature_count=feature_count,
            feature_names=feature_names,
            evaluation_metrics=metadata,
            notes=notes if model is not None else "Awaiting model artifact deployment in backend root directory.",
        )

    @classmethod
    async def get_emissions_trend_forecast(
        cls,
        workspace_id: str,
        db: Any,
        forecast_horizon_months: int = 3,
    ) -> EmissionTrendResponse:
        """
        Builds historical emission trends from verified database records and,
        if an authorized ML artifact is available, performs ML forward forecasting.
        Safeguards:
        - Validates sufficient historical data (minimum 2 monthly observations).
        - Explicitly distinguishes historical observations from forecasted predictions.
        - If model artifact is missing, states limitation clearly and never fabricates mock values.
        - Discloses operational baseline assumption for activity feature projection.
        """
        # 1. Fetch chronological workspace records from MongoDB
        elec_cursor = db.electricity_records.find({"workspace_id": workspace_id}).sort("reporting_month", 1)
        trans_cursor = db.transportation_records.find({"workspace_id": workspace_id}).sort("date", 1)
        waste_cursor = db.waste_records.find({"workspace_id": workspace_id}).sort("date", 1)

        monthly_totals: Dict[str, Dict[str, Any]] = {}

        def get_or_create_month_slot(m: str) -> Dict[str, Any]:
            if m not in monthly_totals:
                monthly_totals[m] = {
                    "electricity_emissions": 0.0,
                    "transportation_emissions": 0.0,
                    "waste_emissions": 0.0,
                    "total_emissions": 0.0,
                    # Activity metrics for model features
                    "electricity_kwh": 0.0,
                    "electricity_bill_inr": 0.0,
                    "distance_km": 0.0,
                    "actual_fuel_consumed_l": 0.0,
                    "fuel_quantity_kg": 0.0,
                    "fuel_expenditure_inr": 0.0,
                    "passengers_list": [],
                    "capacities_list": [],
                    "waste_quantity_kg": 0.0,
                    "disposal_cost_inr": 0.0,
                    # Categorical trackers
                    "electricity_sources": [],
                    "transport_modes": [],
                    "fuel_types": [],
                    "waste_categories": [],
                    "treatment_methods": [],
                    "collection_providers": [],
                    "departments": [],
                }
            return monthly_totals[m]

        async for r in elec_cursor:
            m = normalize_month(r.get("reporting_month") or r.get("date") or "2026-01")
            slot = get_or_create_month_slot(m)
            em = float(r.get("calculated_emissions_kg", 0.0))
            slot["electricity_emissions"] += em
            slot["total_emissions"] += em
            slot["electricity_kwh"] += float(r.get("consumption_kwh", 0.0))
            if r.get("bill_amount_inr"):
                slot["electricity_bill_inr"] += float(r["bill_amount_inr"])
            if r.get("source"):
                slot["electricity_sources"].append(str(r["source"]))
            if r.get("building_or_department"):
                slot["departments"].append(str(r["building_or_department"]))

        async for r in trans_cursor:
            m = normalize_month(r.get("date") or "2026-01")
            slot = get_or_create_month_slot(m)
            em = float(r.get("calculated_emissions_kg", 0.0))
            slot["transportation_emissions"] += em
            slot["total_emissions"] += em
            slot["distance_km"] += float(r.get("distance_km", 0.0))
            if r.get("fuel_consumed_liters"):
                slot["actual_fuel_consumed_l"] += float(r["fuel_consumed_liters"])
            if r.get("fuel_quantity_kg"):
                slot["fuel_quantity_kg"] += float(r["fuel_quantity_kg"])
            if r.get("fuel_expenditure_inr"):
                slot["fuel_expenditure_inr"] += float(r["fuel_expenditure_inr"])
            if r.get("passenger_count") is not None:
                slot["passengers_list"].append(int(r["passenger_count"]))
            if r.get("vehicle_capacity") is not None:
                slot["capacities_list"].append(int(r["vehicle_capacity"]))
            if r.get("mode"):
                slot["transport_modes"].append(str(r["mode"]))
            if r.get("fuel_type"):
                slot["fuel_types"].append(str(r["fuel_type"]))

        async for r in waste_cursor:
            m = normalize_month(r.get("date") or "2026-01")
            slot = get_or_create_month_slot(m)
            em = float(r.get("calculated_emissions_kg", 0.0))
            slot["waste_emissions"] += em
            slot["total_emissions"] += em
            slot["waste_quantity_kg"] += float(r.get("quantity_kg", 0.0))
            if r.get("disposal_cost_inr"):
                slot["disposal_cost_inr"] += float(r["disposal_cost_inr"])
            if r.get("category"):
                slot["waste_categories"].append(str(r["category"]))
            if r.get("treatment_method"):
                slot["treatment_methods"].append(str(r["treatment_method"]))
            if r.get("collection_provider"):
                slot["collection_providers"].append(str(r["collection_provider"]))
            if r.get("building_or_department"):
                slot["departments"].append(str(r["building_or_department"]))

        sorted_months = sorted(monthly_totals.keys())

        # Build historical series
        historical_series: List[HistoricalEmissionPoint] = [
            HistoricalEmissionPoint(
                month=m,
                period=m,
                value=round(monthly_totals[m]["total_emissions"], 1),
                electricity_emissions_kg=round(monthly_totals[m]["electricity_emissions"], 1),
                transportation_emissions_kg=round(monthly_totals[m]["transportation_emissions"], 1),
                waste_emissions_kg=round(monthly_totals[m]["waste_emissions"], 1),
                is_forecast=False,
                data_quality="measured",
            )
            for m in sorted_months
        ]

        historical_legacy = [
            {
                "period": pt.month,
                "month": pt.month,
                "value": pt.value,
                "electricity_emissions_kg": pt.electricity_emissions_kg,
                "transportation_emissions_kg": pt.transportation_emissions_kg,
                "waste_emissions_kg": pt.waste_emissions_kg,
                "is_forecast": False,
            }
            for pt in historical_series
        ]

        model_info = cls.get_model_info()
        model_metrics = cls._metadata

        # Safeguard 1: Minimum historical data
        if len(sorted_months) < 2:
            return EmissionTrendResponse(
                status="insufficient_data",
                message=(
                    f"Workspace contains {len(sorted_months)} monthly period(s). At least 2 distinct monthly "
                    "reporting periods are required to calculate trend momentum and generate forecasts."
                ),
                model_available=model_info.is_loaded,
                forecast_type="monthly",
                target="total_emissions_kg",
                unit="kg CO2e",
                historical=historical_legacy,
                predictions=[],
                historical_series=historical_series,
                forecast_series=[],
                combined_series=[
                    {"month": pt.month, "value": pt.value, "is_forecast": False}
                    for pt in historical_series
                ],
                model_metrics=model_metrics,
                model_info=model_info,
                limitations="Insufficient historical records to extract temporal features or compute statistical forecast.",
            )

        model, metadata = cls.load_model()

        # Safeguard 2: Model artifact availability
        if model is None:
            return EmissionTrendResponse(
                status="model_artifact_missing",
                message=(
                    "Pre-trained ML model artifact is not currently loaded. Place 'carboniq_emissions_model.joblib' "
                    "and 'metrics.json' into backend/ to activate ML predictive inference."
                ),
                model_available=False,
                forecast_type="monthly",
                target="total_emissions_kg",
                unit="kg CO2e",
                historical=historical_legacy,
                predictions=[],
                historical_series=historical_series,
                forecast_series=[],
                combined_series=[
                    {"month": pt.month, "value": pt.value, "is_forecast": False}
                    for pt in historical_series
                ],
                model_metrics=model_metrics,
                model_info=model_info,
                limitations=(
                    "Forecast generation requires a trained model artifact (.joblib). "
                    "No synthetic or rule-based values are fabricated to substitute for the ML model."
                ),
            )

        # 2. Compute workspace operational baselines from verified historical data
        try:
            # Baseline activity metrics averaged across recorded periods
            avg_kwh = float(np.mean([monthly_totals[m]["electricity_kwh"] for m in sorted_months]))
            avg_elec_bill = float(np.mean([monthly_totals[m]["electricity_bill_inr"] for m in sorted_months]))
            if avg_elec_bill <= 0.0 and avg_kwh > 0.0:
                avg_elec_bill = avg_kwh * 8.0  # Commercial tariff baseline in India (~INR 8/kWh)

            avg_distance = float(np.mean([monthly_totals[m]["distance_km"] for m in sorted_months]))
            avg_fuel_l = float(np.mean([monthly_totals[m]["actual_fuel_consumed_l"] for m in sorted_months]))
            avg_fuel_kg = float(np.mean([monthly_totals[m]["fuel_quantity_kg"] for m in sorted_months]))
            avg_fuel_inr = float(np.mean([monthly_totals[m]["fuel_expenditure_inr"] for m in sorted_months]))
            if avg_fuel_inr <= 0.0 and avg_fuel_l > 0.0:
                avg_fuel_inr = avg_fuel_l * 90.0  # Average diesel fuel price in INR

            fuel_eff = round(avg_distance / avg_fuel_l, 2) if (avg_fuel_l > 0 and avg_distance > 0) else 5.0

            all_passengers = [p for m in sorted_months for p in monthly_totals[m]["passengers_list"]]
            avg_passengers = round(float(np.mean(all_passengers))) if all_passengers else 30

            all_capacities = [c for m in sorted_months for c in monthly_totals[m]["capacities_list"]]
            avg_capacity = round(float(np.mean(all_capacities))) if all_capacities else 45

            avg_waste_kg = float(np.mean([monthly_totals[m]["waste_quantity_kg"] for m in sorted_months]))
            avg_disposal_cost = float(np.mean([monthly_totals[m]["disposal_cost_inr"] for m in sorted_months]))
            if avg_disposal_cost <= 0.0 and avg_waste_kg > 0.0:
                avg_disposal_cost = avg_waste_kg * 5.0

            total_recorded_waste_kg = sum(monthly_totals[m]["waste_quantity_kg"] for m in sorted_months)
            total_recorded_waste_em = sum(monthly_totals[m]["waste_emissions"] for m in sorted_months)
            waste_ef = (
                round(total_recorded_waste_em / total_recorded_waste_kg, 4)
                if total_recorded_waste_kg > 0
                else 0.45
            )

            # Predominant categorical values from records
            def mode_or_default(cat_key: str, default: str) -> str:
                items = [item for m in sorted_months for item in monthly_totals[m][cat_key] if item]
                if items:
                    return Counter(items).most_common(1)[0][0]
                return default

            pred_elec_source = mode_or_default("electricity_sources", "Grid")
            pred_transport_mode = mode_or_default("transport_modes", "Bus")
            pred_fuel_type = mode_or_default("fuel_types", "Diesel")
            pred_fuel_method = "fuel_based" if avg_fuel_l > 0 else "distance_based"
            pred_waste_category = mode_or_default("waste_categories", "General")
            pred_treatment = mode_or_default("treatment_methods", "Landfill")
            pred_provider = mode_or_default("collection_providers", "Municipal")
            pred_department = mode_or_default("departments", "Main Campus")

            # Forecast future horizons (e.g. 1 to forecast_horizon_months)
            last_month_str = sorted_months[-1]
            last_year, last_month_num = int(last_month_str[:4]), int(last_month_str[5:7])

            # RMSE for confidence interval calculation from test holdout
            rmse = 76.96
            if metadata and "RMSE_kgCO2e" in metadata:
                try:
                    rmse = float(metadata["RMSE_kgCO2e"])
                except (ValueError, TypeError):
                    rmse = 76.96

            forecast_series: List[ForecastEmissionPoint] = []
            predictions_legacy: List[Dict[str, Any]] = []

            for step in range(1, forecast_horizon_months + 1):
                next_month_num = last_month_num + step
                next_year = last_year
                while next_month_num > 12:
                    next_month_num -= 12
                    next_year += 1

                target_month_str = f"{next_year:04d}-{next_month_num:02d}"
                month_index = len(sorted_months) + step

                # Assemble feature record adhering to model's 24-feature schema
                feature_row: Dict[str, Any] = {
                    "reporting_year": next_year,
                    "reporting_month": next_month_num,
                    "month_index": month_index,
                    "electricity_kwh": avg_kwh,
                    "electricity_bill_inr": avg_elec_bill,
                    "distance_km": avg_distance,
                    "actual_fuel_consumed_l": avg_fuel_l,
                    "fuel_quantity_kg": avg_fuel_kg,
                    "fuel_efficiency_km_per_l": fuel_eff,
                    "electricity_used_kwh_for_ev": 0.0,
                    "fuel_expenditure_inr": avg_fuel_inr,
                    "passengers_on_board": avg_passengers,
                    "vehicle_capacity": avg_capacity,
                    "waste_quantity_kg": avg_waste_kg,
                    "disposal_cost_inr": avg_disposal_cost,
                    "waste_emission_factor_kgco2e_per_kg": waste_ef,
                    "electricity_source": pred_elec_source,
                    "transport_mode": pred_transport_mode,
                    "fuel_type": pred_fuel_type,
                    "fuel_calculation_method": pred_fuel_method,
                    "waste_category": pred_waste_category,
                    "treatment_method": pred_treatment,
                    "collection_provider": pred_provider,
                    "building_department": pred_department,
                }

                input_df = pd.DataFrame([feature_row])
                raw_pred = model.predict(input_df)
                pred_val = float(raw_pred[0]) if hasattr(raw_pred, "__len__") else float(raw_pred)
                pred_val = max(0.0, round(pred_val, 1))

                ci_lower = max(0.0, round(pred_val - 1.96 * rmse, 1))
                ci_upper = round(pred_val + 1.96 * rmse, 1)

                pt = ForecastEmissionPoint(
                    month=target_month_str,
                    period=target_month_str,
                    value=pred_val,
                    predicted_emissions_kg=pred_val,
                    unit="kg CO2e",
                    is_forecast=True,
                    confidence_interval_lower=ci_lower,
                    confidence_interval_upper=ci_upper,
                    model_version=model_info.model_version,
                )
                forecast_series.append(pt)

                predictions_legacy.append(
                    {
                        "period": target_month_str,
                        "month": target_month_str,
                        "predicted_emissions_kg": pred_val,
                        "value": pred_val,
                        "unit": "kg CO2e",
                        "is_forecast": True,
                        "confidence_interval_lower": ci_lower,
                        "confidence_interval_upper": ci_upper,
                    }
                )

            # Combined series: seamlessly bridges historical to forecast
            combined: List[Dict[str, Any]] = []
            for i, pt in enumerate(historical_series):
                is_last_historical = i == len(historical_series) - 1
                combined.append(
                    {
                        "month": pt.month,
                        "period": pt.month,
                        "value": pt.value,
                        # Bridge to forecast on the last historical point so lines connect in Recharts
                        "forecast": pt.value if is_last_historical else None,
                        "is_forecast": False,
                    }
                )

            for pt in forecast_series:
                combined.append(
                    {
                        "month": pt.month,
                        "period": pt.month,
                        "value": None,
                        "forecast": pt.value,
                        "is_forecast": True,
                    }
                )

            limitations_list = [
                "Predictions generated by supervised XGBoost Regressor Pipeline (carboniq_emissions_model.joblib).",
                "Activity inputs (kWh, fuel, waste) are estimated based on observed historical operational baselines of the workspace.",
                "Forecast assumes operational continuity and does not anticipate unrecorded major policy shifts or grid factor changes.",
            ]

            return EmissionTrendResponse(
                status="ready",
                message=f"Generated {len(forecast_series)}-month emission trend forecast using pre-trained ML model.",
                model_available=True,
                forecast_type="monthly",
                target="total_emissions_kg",
                unit="kg CO2e",
                historical=historical_legacy,
                predictions=predictions_legacy,
                historical_series=historical_series,
                forecast_series=forecast_series,
                combined_series=combined,
                model_metrics=model_metrics,
                model_info=model_info,
                limitations=" ".join(limitations_list),
            )

        except Exception as e:
            logger.error(f"Error during ML inference: {e}", exc_info=True)
            return EmissionTrendResponse(
                status="error",
                message=f"Model inference failed: {str(e)}",
                model_available=False,
                forecast_type="monthly",
                target="total_emissions_kg",
                unit="kg CO2e",
                historical=historical_legacy,
                predictions=[],
                historical_series=historical_series,
                forecast_series=[],
                combined_series=[
                    {"month": pt.month, "value": pt.value, "is_forecast": False}
                    for pt in historical_series
                ],
                model_metrics=model_metrics,
                model_info=model_info,
                limitations="Inference failed due to feature schema mismatch or model incompatibility.",
            )
