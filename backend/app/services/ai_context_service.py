import asyncio
from collections import defaultdict
import logging
import re
from typing import Any, Dict, List, Optional, Tuple

import numpy as np

from app.calculations.electricity_calculator import calculate_electricity_savings_scenario
from app.calculations.route_optimizer import optimize_bus_routes
from app.calculations.waste_calculator import calculate_recycling_rate
from app.data.emission_factors import EMISSION_FACTORS
from app.services.ml_prediction_service import MlPredictionService
from app.utils.dates import normalize_month

logger = logging.getLogger("carboniq.ai.context")


class AiContextService:
    """
    Centralized, secure AI Context Builder for CarbonIQ's four AI assistants:
    1. Electricity Advisor
    2. Transportation Advisor
    3. Waste Advisor
    4. Interactive Sustainability Analyst

    Architectural Standards:
    - Mandatory workspace isolation: all queries filter strictly on authenticated workspace_id.
    - Grounded strictly in verified database records and deterministic Python calculators.
    - Zero numerical hallucinations: LLM explains verified facts, never invents numbers.
    - Intelligent query-aware context selection: supplies relevant historical depth without
      overloading prompt tokens or inducing latency.
    - Integrates the XGBoost emissions model via MlPredictionService only when statistically valid.
    """

    # -------------------------------------------------------------------------
    # Internal Helpers
    # -------------------------------------------------------------------------
    @staticmethod
    async def _get_workspace_meta(workspace_id: str, db: Any) -> Dict[str, Any]:
        """Loads workspace metadata (type, organization name) safely."""
        workspace = await db.workspaces.find_one({"id": workspace_id}, projection={"_id": 0, "name": 1, "type": 1, "organization": 1})
        name = workspace.get("name") if workspace else "Active Workspace"
        ws_type = workspace.get("type", "organization") if workspace else "organization"
        return {
            "workspace_id": workspace_id,
            "workspace_name": name,
            "workspace_type": ws_type,
            "standard_units": {
                "electricity": "kWh",
                "transportation": "km, L",
                "waste": "kg",
                "emissions": "kg CO2e",
                "currency": "INR (₹)",
            },
        }

    @staticmethod
    def _classify_query_intent(query: str) -> Dict[str, Any]:
        """
        Classifies query intent to guide selective context inclusion.
        Determines if the user is asking about trends, peaks, savings, forecasts, or specific periods.
        """
        q = (query or "").lower().strip()
        is_trend = bool(re.search(r"\b(trend|trends|history|historical|over time|month[- ]over[- ]month|mom|change|changes|past|increase|increased|decrease|decreased|growth|evolution)\b", q))
        is_peak = bool(re.search(r"\b(highest|peak|maximum|max|lowest|minimum|min|worst|best|spike|anomaly)\b", q))
        is_savings = bool(re.search(r"\b(save|saving|savings|reduce|reduction|cut|efficiency|efficient|opportunity|opportunities|scenario|percentage|percent|%)\b", q))
        is_forecast = bool(re.search(r"\b(forecast|forecasting|predict|prediction|predictions|future|next month|next quarter|xgboost|project|projection)\b", q))
        is_comparison = bool(re.search(r"\b(compare|comparison|versus|vs|previous|prior|last month|difference)\b", q))
        is_fleet = bool(re.search(r"\b(bus|buses|route|routes|fleet|transit|student|students|occupancy|corridor|combine|consolidation|deadhead)\b", q))

        pct_match = re.search(r"(\d+)%", q)
        target_pct = float(pct_match.group(1)) if pct_match else None

        # Detect specific month mention (e.g. 2026-01, jan, february)
        month_match = re.search(r"\b(202\d[-/]\d{1,2})\b", q)
        specific_month = normalize_month(month_match.group(1)) if month_match else None

        return {
            "is_trend": is_trend,
            "is_peak": is_peak,
            "is_savings": is_savings,
            "is_forecast": is_forecast,
            "is_comparison": is_comparison,
            "is_fleet": is_fleet,
            "target_savings_pct": target_pct,
            "specific_month": specific_month,
        }

    @staticmethod
    def _compute_mom_comparison(
        latest_val: float,
        previous_val: Optional[float],
        unit: str,
        metric_name: str,
    ) -> Optional[Dict[str, Any]]:
        """
        Safely computes Month-over-Month change, handling zero denominators and missing previous periods.
        """
        if previous_val is None:
            return None

        diff = round(latest_val - previous_val, 1)
        if previous_val > 0.0:
            pct = round((diff / previous_val) * 100.0, 1)
        elif previous_val == 0.0 and latest_val > 0.0:
            pct = 100.0
        else:
            pct = 0.0

        direction = "increased" if diff > 0.0 else "decreased" if diff < 0.0 else "steady"
        return {
            "metric": metric_name,
            "current_value": latest_val,
            "previous_value": previous_val,
            "absolute_change": diff,
            "percentage_change": pct,
            "trend_direction": direction,
            "unit": unit,
            "formatted_change": f"{direction.capitalize()} by {abs(diff)} {unit} ({pct:+0.1f}%)",
        }

    # -------------------------------------------------------------------------
    # 1. Electricity AI Context Builder
    # -------------------------------------------------------------------------
    @classmethod
    async def build_electricity_context(
        cls,
        workspace_id: str,
        db: Any,
        user_query: str,
    ) -> Dict[str, Any]:
        """
        Builds rich, historical and current-period context for Electricity AI.
        Includes monthly chronological trends, department breakdowns, CEA baseline factor,
        historical peak/trough analysis, and verified savings scenarios.
        """
        meta = await cls._get_workspace_meta(workspace_id, db)
        intent = cls._classify_query_intent(user_query)

        # Retrieve workspace electricity records with selective field projection
        projection = {
            "reporting_month": 1,
            "consumption_kwh": 1,
            "calculated_emissions_kg": 1,
            "bill_amount_inr": 1,
            "source": 1,
            "building_or_department": 1,
            "_id": 0,
        }
        cursor = db.electricity_records.find(
            {"workspace_id": workspace_id},
            projection=projection,
        ).sort("reporting_month", 1)
        records = [r async for r in cursor]

        if not records:
            return {
                "workspace": meta,
                "record_count": 0,
                "has_records": False,
                "data_limitations": ["No electricity records have been logged in this workspace yet."],
            }

        # 1. Monthly Aggregation
        monthly_map: Dict[str, Dict[str, float]] = defaultdict(lambda: {"kwh": 0.0, "emissions": 0.0, "bill": 0.0, "records": 0})
        dept_map: Dict[str, float] = defaultdict(float)
        sources_set = set()

        for r in records:
            m = normalize_month(r.get("reporting_month") or "2026-01")
            kwh = float(r.get("consumption_kwh", 0.0))
            em = float(r.get("calculated_emissions_kg", 0.0))
            bill = float(r.get("bill_amount_inr", 0.0) or 0.0)
            dept = str(r.get("building_or_department") or "Facility")
            src = str(r.get("source") or "Grid")

            monthly_map[m]["kwh"] += kwh
            monthly_map[m]["emissions"] += em
            monthly_map[m]["bill"] += bill
            monthly_map[m]["records"] += 1
            dept_map[dept] += kwh
            sources_set.add(src)

        sorted_months = sorted(monthly_map.keys())
        total_kwh = sum(data["kwh"] for data in monthly_map.values())
        total_emissions = sum(data["emissions"] for data in monthly_map.values())
        total_bill = sum(data["bill"] for data in monthly_map.values())

        # Chronological Monthly Series with MoM changes
        monthly_series: List[Dict[str, Any]] = []
        for i, m in enumerate(sorted_months):
            data = monthly_map[m]
            prev_kwh = monthly_map[sorted_months[i - 1]]["kwh"] if i > 0 else None
            mom = cls._compute_mom_comparison(data["kwh"], prev_kwh, "kWh", "Consumption") if i > 0 else None
            monthly_series.append({
                "month": m,
                "consumption_kwh": round(data["kwh"], 1),
                "emissions_kg": round(data["emissions"], 1),
                "bill_inr": round(data["bill"], 0) if data["bill"] > 0 else None,
                "record_count": data["records"],
                "mom_comparison": mom,
            })

        latest_month_str = sorted_months[-1]
        latest_data = monthly_map[latest_month_str]
        prev_month_str = sorted_months[-2] if len(sorted_months) > 1 else None
        prev_data = monthly_map[prev_month_str] if prev_month_str else None

        # Historical Peak and Trough Periods
        peak_month = max(sorted_months, key=lambda m: monthly_map[m]["kwh"])
        trough_month = min(sorted_months, key=lambda m: monthly_map[m]["kwh"])
        avg_monthly_kwh = round(total_kwh / len(sorted_months), 1)
        avg_monthly_emissions = round(total_emissions / len(sorted_months), 1)

        # Department breakdown
        department_breakdown = [
            {
                "department": dept,
                "consumption_kwh": round(kwh, 1),
                "percentage_share": round((kwh / total_kwh) * 100.0, 1) if total_kwh > 0 else 0.0,
            }
            for dept, kwh in sorted(dept_map.items(), key=lambda x: x[1], reverse=True)
        ]

        # Verified Deterministic Savings Scenario
        target_pct = intent["target_savings_pct"] or 15.0
        scenario = calculate_electricity_savings_scenario(latest_data["kwh"], target_pct)
        grid_factor = EMISSION_FACTORS["grid_in_cea_baseline"]

        # Assemble selective context
        # For trend queries: provide all historical periods. Otherwise provide recent 4 periods.
        selected_history = monthly_series if (intent["is_trend"] or len(monthly_series) <= 4) else monthly_series[-4:]

        limitations = []
        if len(sorted_months) < 2:
            limitations.append("Workspace has only 1 monthly observation. Trend comparisons require at least 2 distinct periods.")
        if total_bill == 0.0:
            limitations.append("Electricity bills (INR) not recorded; financial estimates use CEA benchmark commercial tariff of ₹8.0/kWh.")

        return {
            "module": "electricity",
            "workspace": meta,
            "has_records": True,
            "total_records_analyzed": len(records),
            "reporting_period": f"{sorted_months[0]} to {sorted_months[-1]}" if len(sorted_months) > 1 else sorted_months[0],
            "current_period": {
                "month": latest_month_str,
                "consumption_kwh": round(latest_data["kwh"], 1),
                "calculated_emissions_kg": round(latest_data["emissions"], 1),
                "bill_inr": round(latest_data["bill"], 0) if latest_data["bill"] > 0 else None,
                "generation_sources": sorted(sources_set),
            },
            "previous_period_comparison": cls._compute_mom_comparison(
                latest_data["kwh"],
                prev_data["kwh"] if prev_data else None,
                "kWh",
                "Electricity Consumption",
            ),
            "historical_statistics": {
                "months_recorded": len(sorted_months),
                "average_monthly_kwh": avg_monthly_kwh,
                "average_monthly_emissions_kg": avg_monthly_emissions,
                "peak_month": {
                    "month": peak_month,
                    "consumption_kwh": round(monthly_map[peak_month]["kwh"], 1),
                    "emissions_kg": round(monthly_map[peak_month]["emissions"], 1),
                },
                "lowest_month": {
                    "month": trough_month,
                    "consumption_kwh": round(monthly_map[trough_month]["kwh"], 1),
                    "emissions_kg": round(monthly_map[trough_month]["emissions"], 1),
                },
            },
            "historical_monthly_trends": selected_history,
            "department_breakdown": department_breakdown[:5],
            "modeled_savings_scenario": {
                "target_reduction_percent": target_pct,
                "baseline_month": latest_month_str,
                "kwh_reduction": scenario.kwh_reduction,
                "emissions_reduction_kg": scenario.emissions_reduction_kg,
                "estimated_monthly_savings_inr": scenario.cost_savings_inr,
                "assumed_tariff_inr_per_kwh": scenario.tariff_inr_per_kwh,
                "assumptions": scenario.assumptions,
            },
            "authoritative_emission_factor": {
                "factor_id": grid_factor.factor_id,
                "value": grid_factor.value,
                "unit": grid_factor.unit,
                "source": grid_factor.source,
            },
            "data_limitations": limitations,
        }

    # -------------------------------------------------------------------------
    # 2. Transportation AI Context Builder
    # -------------------------------------------------------------------------
    @classmethod
    async def build_transportation_context(
        cls,
        workspace_id: str,
        db: Any,
        user_query: str,
    ) -> Dict[str, Any]:
        """
        Builds comprehensive, historical and fleet-specific context for Transportation AI.
        Concurrently queries bus routes and trip logs, computing occupancy rates, peak fuel routes,
        historical monthly mileage trends, and deterministic route optimization proposals.
        """
        meta = await cls._get_workspace_meta(workspace_id, db)
        intent = cls._classify_query_intent(user_query)

        # Concurrently fetch bus routes and transportation logs with lean projections
        routes_proj = {
            "route_name": 1,
            "distance_km": 1,
            "assigned_students": 1,
            "seating_capacity": 1,
            "destination": 1,
            "trips_per_day": 1,
            "fuel_efficiency_km_per_l": 1,
            "_id": 0,
        }
        trans_proj = {
            "date": 1,
            "distance_km": 1,
            "calculated_emissions_kg": 1,
            "fuel_consumed_liters": 1,
            "fuel_type": 1,
            "fuel_efficiency_km_per_l": 1,
            "fuel_expenditure_inr": 1,
            "mode": 1,
            "route_name": 1,
            "_id": 0,
        }

        async def _fetch_routes():
            return [r async for r in db.bus_routes.find({"workspace_id": workspace_id}, projection=routes_proj)]

        async def _fetch_trans():
            return [t async for t in db.transportation_records.find({"workspace_id": workspace_id}, projection=trans_proj).sort("date", 1)]

        routes, trans_records = await asyncio.gather(_fetch_routes(), _fetch_trans())

        if not routes and not trans_records:
            return {
                "workspace": meta,
                "record_count": 0,
                "has_records": False,
                "data_limitations": ["No fleet logs or bus transit routes have been registered for this workspace."],
            }

        # 1. Analyze Bus Routes & Occupancy
        total_routes = len(routes)
        total_assigned_students = sum(r.get("assigned_students", 0) for r in routes)
        total_seats = sum(r.get("seating_capacity", 40) for r in routes)
        overall_occupancy_pct = round((total_assigned_students / total_seats) * 100.0, 1) if total_seats > 0 else 0.0

        low_occupancy_routes = [
            {
                "route_name": r.get("route_name"),
                "assigned_students": r.get("assigned_students", 0),
                "seating_capacity": r.get("seating_capacity", 40),
                "occupancy_rate_pct": round((r.get("assigned_students", 0) / max(1, r.get("seating_capacity", 40))) * 100.0, 1),
            }
            for r in routes
            if r.get("seating_capacity", 40) > 0 and (r.get("assigned_students", 0) / r.get("seating_capacity", 40)) < 0.6
        ]

        # Peak fuel consumption route
        peak_fuel_route = None
        if routes:
            peak_route_doc = max(
                routes,
                key=lambda x: (x.get("distance_km", 0.0) * x.get("trips_per_day", 2)) / max(1.0, x.get("fuel_efficiency_km_per_l", 4.5)),
            )
            daily_l = round(
                (peak_route_doc.get("distance_km", 0.0) * peak_route_doc.get("trips_per_day", 2))
                / max(1.0, peak_route_doc.get("fuel_efficiency_km_per_l", 4.5)),
                1,
            )
            peak_fuel_route = {
                "route_name": peak_route_doc.get("route_name"),
                "distance_km": peak_route_doc.get("distance_km"),
                "trips_per_day": peak_route_doc.get("trips_per_day", 2),
                "fuel_efficiency_km_per_l": peak_route_doc.get("fuel_efficiency_km_per_l", 4.5),
                "daily_fuel_liters": daily_l,
            }

        # Route Optimization Proposals (deterministic calculation)
        proposals = optimize_bus_routes(routes) if routes else []
        top_proposal = None
        if proposals:
            p = proposals[0]
            top_proposal = {
                "title": p.title,
                "summary": p.summary,
                "distance_reduction_km_per_day": p.estimated_distance_reduction_km,
                "estimated_monthly_fuel_savings_liters": p.estimated_fuel_savings_liters,
                "estimated_monthly_cost_savings_inr": p.estimated_monthly_savings_inr,
                "estimated_monthly_emissions_reduction_kg": p.estimated_emissions_reduction_kg,
                "feasibility": p.feasibility,
            }

        # 2. Monthly Historical Travel Aggregation
        monthly_map: Dict[str, Dict[str, float]] = defaultdict(lambda: {"distance": 0.0, "fuel": 0.0, "emissions": 0.0, "expenditure": 0.0, "trips": 0})
        mode_map: Dict[str, float] = defaultdict(float)

        for t in trans_records:
            m = normalize_month(t.get("date") or "2026-01")
            dist = float(t.get("distance_km", 0.0))
            em = float(t.get("calculated_emissions_kg", 0.0))
            fuel = float(t.get("fuel_consumed_liters", 0.0) or (dist / max(1.0, t.get("fuel_efficiency_km_per_l", 4.5))))
            exp = float(t.get("fuel_expenditure_inr", 0.0) or 0.0)
            mode = str(t.get("mode") or "Bus / Transit")

            monthly_map[m]["distance"] += dist
            monthly_map[m]["fuel"] += fuel
            monthly_map[m]["emissions"] += em
            monthly_map[m]["expenditure"] += exp
            monthly_map[m]["trips"] += 1
            mode_map[mode] += em

        sorted_months = sorted(monthly_map.keys())
        total_distance = sum(data["distance"] for data in monthly_map.values())
        total_emissions = sum(data["emissions"] for data in monthly_map.values())
        total_fuel = sum(data["fuel"] for data in monthly_map.values())

        monthly_series: List[Dict[str, Any]] = []
        for i, m in enumerate(sorted_months):
            data = monthly_map[m]
            prev_em = monthly_map[sorted_months[i - 1]]["emissions"] if i > 0 else None
            mom = cls._compute_mom_comparison(data["emissions"], prev_em, "kg CO2e", "Emissions") if i > 0 else None
            monthly_series.append({
                "month": m,
                "distance_km": round(data["distance"], 1),
                "fuel_liters": round(data["fuel"], 1),
                "emissions_kg": round(data["emissions"], 1),
                "trips": data["trips"],
                "mom_comparison": mom,
            })

        latest_month = sorted_months[-1] if sorted_months else "Current"
        latest_data = monthly_map[latest_month] if sorted_months else None
        prev_month = sorted_months[-2] if len(sorted_months) > 1 else None
        prev_data = monthly_map[prev_month] if prev_month else None

        selected_history = monthly_series if (intent["is_trend"] or len(monthly_series) <= 4) else monthly_series[-4:]

        limitations = []
        if not trans_records and routes:
            limitations.append("Individual trip odometers are unlogged; emissions are estimated based on bus route distances and baseline fuel efficiency.")
        if len(sorted_months) < 2:
            limitations.append("Single-period dataset; month-over-month mobility trend comparisons require multiple observations.")

        return {
            "module": "transportation",
            "workspace": meta,
            "has_records": True,
            "total_fleet_records": len(trans_records),
            "total_routes_configured": total_routes,
            "reporting_period": f"{sorted_months[0]} to {sorted_months[-1]}" if len(sorted_months) > 1 else (sorted_months[0] if sorted_months else "Active Schedule"),
            "current_period": {
                "month": latest_month,
                "distance_km": round(latest_data["distance"], 1) if latest_data else 0.0,
                "fuel_liters": round(latest_data["fuel"], 1) if latest_data else 0.0,
                "calculated_emissions_kg": round(latest_data["emissions"], 1) if latest_data else 0.0,
            },
            "previous_period_comparison": cls._compute_mom_comparison(
                latest_data["emissions"] if latest_data else 0.0,
                prev_data["emissions"] if prev_data else None,
                "kg CO2e",
                "Fleet Emissions",
            ),
            "historical_monthly_trends": selected_history,
            "historical_statistics": {
                "total_distance_km": round(total_distance, 1),
                "total_fuel_liters": round(total_fuel, 1),
                "total_emissions_kg": round(total_emissions, 1),
                "average_monthly_emissions_kg": round(total_emissions / max(1, len(sorted_months)), 1) if sorted_months else 0.0,
            },
            "bus_fleet_metrics": {
                "total_routes": total_routes,
                "total_assigned_students": total_assigned_students,
                "overall_occupancy_percent": overall_occupancy_pct,
                "low_occupancy_corridors_count": len(low_occupancy_routes),
                "low_occupancy_sample": low_occupancy_routes[:3],
                "peak_fuel_route": peak_fuel_route,
            },
            "route_optimization_proposal": top_proposal,
            "data_limitations": limitations,
        }

    # -------------------------------------------------------------------------
    # 3. Waste AI Context Builder
    # -------------------------------------------------------------------------
    @classmethod
    async def build_waste_context(
        cls,
        workspace_id: str,
        db: Any,
        user_query: str,
    ) -> Dict[str, Any]:
        """
        Builds rigorous circularity and waste management context.
        Accurately distinguishes positive landfill emissions from negative circular diversion credits
        (avoided methane generation). Calculates monthly recycling recovery trends and category breakdown.
        """
        meta = await cls._get_workspace_meta(workspace_id, db)
        intent = cls._classify_query_intent(user_query)

        waste_proj = {
            "date": 1,
            "quantity_kg": 1,
            "calculated_emissions_kg": 1,
            "treatment_method": 1,
            "category": 1,
            "disposal_cost_inr": 1,
            "_id": 0,
        }
        cursor = db.waste_records.find({"workspace_id": workspace_id}, projection=waste_proj).sort("date", 1)
        records = [r async for r in cursor]

        if not records:
            return {
                "workspace": meta,
                "record_count": 0,
                "has_records": False,
                "data_limitations": ["No solid waste stream records have been logged in this workspace yet."],
            }

        # 1. Historical Monthly Aggregation
        monthly_map: Dict[str, Dict[str, float]] = defaultdict(lambda: {"total_kg": 0.0, "recycled_kg": 0.0, "emissions": 0.0, "cost": 0.0, "records": 0})
        cat_map: Dict[str, float] = defaultdict(float)
        treat_map: Dict[str, float] = defaultdict(float)

        for r in records:
            m = normalize_month(r.get("date") or "2026-01")
            qty = float(r.get("quantity_kg", 0.0))
            em = float(r.get("calculated_emissions_kg", 0.0))
            cost = float(r.get("disposal_cost_inr", 0.0) or 0.0)
            treat = str(r.get("treatment_method") or "Other").strip()
            cat = str(r.get("category") or "General").strip()

            monthly_map[m]["total_kg"] += qty
            monthly_map[m]["emissions"] += em
            monthly_map[m]["cost"] += cost
            monthly_map[m]["records"] += 1
            cat_map[cat] += qty
            treat_map[treat] += qty

            if treat.lower() in ["recycling", "recycled", "composting", "composted"] or cat.lower() in ["recyclable", "organic"]:
                monthly_map[m]["recycled_kg"] += qty

        sorted_months = sorted(monthly_map.keys())
        total_qty = sum(data["total_kg"] for data in monthly_map.values())
        total_recycled = sum(data["recycled_kg"] for data in monthly_map.values())
        overall_recycling_rate = calculate_recycling_rate(total_recycled, total_qty) or 0.0
        total_emissions = sum(data["emissions"] for data in monthly_map.values())

        monthly_series: List[Dict[str, Any]] = []
        for i, m in enumerate(sorted_months):
            data = monthly_map[m]
            m_rate = calculate_recycling_rate(data["recycled_kg"], data["total_kg"]) or 0.0
            prev_rate = calculate_recycling_rate(monthly_map[sorted_months[i - 1]]["recycled_kg"], monthly_map[sorted_months[i - 1]]["total_kg"]) if i > 0 else None
            mom = cls._compute_mom_comparison(m_rate, prev_rate, "%", "Recycling Rate") if i > 0 else None
            monthly_series.append({
                "month": m,
                "total_kg": round(data["total_kg"], 1),
                "recycled_kg": round(data["recycled_kg"], 1),
                "recycling_rate_percent": round(m_rate, 1),
                "emissions_kg": round(data["emissions"], 1),
                "mom_comparison": mom,
            })

        latest_month = sorted_months[-1]
        latest_data = monthly_map[latest_month]
        prev_month = sorted_months[-2] if len(sorted_months) > 1 else None
        prev_data = monthly_map[prev_month] if prev_month else None

        latest_rate = calculate_recycling_rate(latest_data["recycled_kg"], latest_data["total_kg"]) or 0.0
        prev_rate = calculate_recycling_rate(prev_data["recycled_kg"], prev_data["total_kg"]) if prev_data else None

        # Category Breakdown
        category_breakdown = [
            {
                "category": c,
                "quantity_kg": round(qty, 1),
                "percentage_share": round((qty / total_qty) * 100.0, 1) if total_qty > 0 else 0.0,
            }
            for c, qty in sorted(cat_map.items(), key=lambda x: x[1], reverse=True)
        ]

        # Treatment Method Breakdown
        treatment_breakdown = [
            {
                "treatment_method": t,
                "quantity_kg": round(qty, 1),
                "percentage_share": round((qty / total_qty) * 100.0, 1) if total_qty > 0 else 0.0,
            }
            for t, qty in sorted(treat_map.items(), key=lambda x: x[1], reverse=True)
        ]

        selected_history = monthly_series if (intent["is_trend"] or len(monthly_series) <= 4) else monthly_series[-4:]

        limitations = []
        if len(sorted_months) < 2:
            limitations.append("Waste trend analysis requires at least two recorded monthly collection cycles.")

        return {
            "module": "waste",
            "workspace": meta,
            "has_records": True,
            "total_records_analyzed": len(records),
            "reporting_period": f"{sorted_months[0]} to {sorted_months[-1]}" if len(sorted_months) > 1 else sorted_months[0],
            "current_period": {
                "month": latest_month,
                "total_waste_kg": round(latest_data["total_kg"], 1),
                "recycled_kg": round(latest_data["recycled_kg"], 1),
                "recycling_rate_percent": round(latest_rate, 1),
                "net_emissions_kg": round(latest_data["emissions"], 1),
            },
            "previous_period_comparison": cls._compute_mom_comparison(
                latest_rate,
                prev_rate,
                "%",
                "Recycling Diversion Rate",
            ),
            "historical_monthly_trends": selected_history,
            "historical_statistics": {
                "total_waste_generated_kg": round(total_qty, 1),
                "total_waste_recycled_kg": round(total_recycled, 1),
                "cumulative_recycling_rate_percent": round(overall_recycling_rate, 1),
                "net_circular_emissions_kg": round(total_emissions, 1),
            },
            "category_breakdown": category_breakdown[:5],
            "treatment_breakdown": treatment_breakdown,
            "circular_accounting_note": (
                "Under IPCC guidelines and GHG Protocol Scope 3, recycling and composting yield negative emissions "
                "representing avoided landfill methane. This represents an avoided emission credit, not active carbon removal."
            ),
            "data_limitations": limitations,
        }

    # -------------------------------------------------------------------------
    # 4. Interactive Sustainability Analyst (Cross-Category Synthesis) Context
    # -------------------------------------------------------------------------
    @classmethod
    async def build_insights_context(
        cls,
        workspace_id: str,
        db: Any,
        user_query: str,
    ) -> Dict[str, Any]:
        """
        Builds complete enterprise sustainability synthesis context across Electricity,
        Transportation, and Waste. Dynamically incorporates ML predictions from MlPredictionService,
        historical MoM portfolio changes, and deterministic route optimization opportunities.
        """
        meta = await cls._get_workspace_meta(workspace_id, db)
        intent = cls._classify_query_intent(user_query)

        # 1. Concurrently gather lean projected records across all three collections and bus routes count
        elec_proj = {"reporting_month": 1, "consumption_kwh": 1, "calculated_emissions_kg": 1, "_id": 0}
        trans_proj = {"date": 1, "distance_km": 1, "calculated_emissions_kg": 1, "_id": 0}
        waste_proj = {"date": 1, "quantity_kg": 1, "calculated_emissions_kg": 1, "_id": 0}

        async def _get_elec():
            return [r async for r in db.electricity_records.find({"workspace_id": workspace_id}, projection=elec_proj)]

        async def _get_trans():
            return [r async for r in db.transportation_records.find({"workspace_id": workspace_id}, projection=trans_proj)]

        async def _get_waste():
            return [r async for r in db.waste_records.find({"workspace_id": workspace_id}, projection=waste_proj)]

        async def _get_routes():
            return [r async for r in db.bus_routes.find({"workspace_id": workspace_id}, projection={"_id": 0, "route_name": 1, "distance_km": 1, "assigned_students": 1, "seating_capacity": 1, "fuel_efficiency_km_per_l": 1, "trips_per_day": 1})]

        elec_records, trans_records, waste_records, bus_routes = await asyncio.gather(
            _get_elec(),
            _get_trans(),
            _get_waste(),
            _get_routes(),
        )

        total_records_count = len(elec_records) + len(trans_records) + len(waste_records)
        if total_records_count == 0:
            return {
                "workspace": meta,
                "has_records": False,
                "total_records_analyzed": 0,
                "data_limitations": ["No activity records logged across Electricity, Transportation, or Waste in this workspace."],
            }

        # 2. Multi-category Monthly Chronological Timeline
        monthly_totals: Dict[str, Dict[str, float]] = defaultdict(lambda: {"electricity": 0.0, "transportation": 0.0, "waste": 0.0, "net_total": 0.0})

        for r in elec_records:
            m = normalize_month(r.get("reporting_month") or "2026-01")
            em = float(r.get("calculated_emissions_kg", 0.0))
            monthly_totals[m]["electricity"] += em
            monthly_totals[m]["net_total"] += em

        for r in trans_records:
            m = normalize_month(r.get("date") or "2026-01")
            em = float(r.get("calculated_emissions_kg", 0.0))
            monthly_totals[m]["transportation"] += em
            monthly_totals[m]["net_total"] += em

        for r in waste_records:
            m = normalize_month(r.get("date") or "2026-01")
            em = float(r.get("calculated_emissions_kg", 0.0))
            monthly_totals[m]["waste"] += em
            monthly_totals[m]["net_total"] += em

        sorted_months = sorted(monthly_totals.keys())

        # Cumulative totals
        elec_total = round(sum(d["electricity"] for d in monthly_totals.values()), 1)
        trans_total = round(sum(d["transportation"] for d in monthly_totals.values()), 1)
        waste_total = round(sum(d["waste"] for d in monthly_totals.values()), 1)
        net_total = round(elec_total + trans_total + waste_total, 1)

        # Gross Positive Emissions (denominator for proportion calculations)
        positive_categories: List[Tuple[str, float, int]] = []
        if trans_total > 0:
            positive_categories.append(("Transportation", trans_total, len(trans_records)))
        if elec_total > 0:
            positive_categories.append(("Electricity", elec_total, len(elec_records)))
        if waste_total > 0:
            positive_categories.append(("Waste", waste_total, len(waste_records)))

        gross_positive_emissions = round(sum(c[1] for c in positive_categories), 1) if positive_categories else 0.0

        # Largest emission source
        largest_source_info = None
        if positive_categories:
            sorted_positive = sorted(positive_categories, key=lambda x: x[1], reverse=True)
            top_name, top_val, top_cnt = sorted_positive[0]
            pct_gross = round((top_val / gross_positive_emissions) * 100.0, 1) if gross_positive_emissions > 0 else 0.0
            pct_net = round((top_val / net_total) * 100.0, 1) if net_total > 0 else None
            largest_source_info = {
                "category": top_name,
                "emissions_kg": top_val,
                "percentage_of_gross_positive": pct_gross,
                "percentage_of_net_total": pct_net,
                "contributing_record_count": top_cnt,
            }

        # Categories structured details
        categories_data = [
            {
                "name": "Electricity",
                "emissions_kg": elec_total,
                "record_count": len(elec_records),
                "percentage_of_gross": round((elec_total / gross_positive_emissions) * 100.0, 1) if gross_positive_emissions > 0 and elec_total > 0 else 0.0,
                "percentage_of_net": round((elec_total / net_total) * 100.0, 1) if net_total > 0 and elec_total > 0 else None,
                "status": "positive",
                "scope": "Scope 2 Purchased Electricity (CEA Baseline v19)",
            },
            {
                "name": "Transportation",
                "emissions_kg": trans_total,
                "record_count": len(trans_records),
                "percentage_of_gross": round((trans_total / gross_positive_emissions) * 100.0, 1) if gross_positive_emissions > 0 and trans_total > 0 else 0.0,
                "percentage_of_net": round((trans_total / net_total) * 100.0, 1) if net_total > 0 and trans_total > 0 else None,
                "status": "positive",
                "scope": "Scope 1 Fleet Transit (Direct Tailpipe Fuel)",
            },
            {
                "name": "Waste",
                "emissions_kg": waste_total,
                "record_count": len(waste_records),
                "percentage_of_gross": None,
                "percentage_of_net": round((waste_total / net_total) * 100.0, 1) if net_total > 0 else None,
                "status": "negative_credit" if waste_total < 0 else "positive" if waste_total > 0 else "zero",
                "scope": "Scope 3 Circular Stream (Recycling/Composting avoidance offset)",
            },
        ]

        # Monthly chronological series with MoM change
        monthly_series: List[Dict[str, Any]] = []
        for i, m in enumerate(sorted_months):
            data = monthly_totals[m]
            prev_net = monthly_totals[sorted_months[i - 1]]["net_total"] if i > 0 else None
            mom = cls._compute_mom_comparison(data["net_total"], prev_net, "kg CO2e", "Net Portfolio Emissions") if i > 0 else None
            monthly_series.append({
                "month": m,
                "electricity_emissions_kg": round(data["electricity"], 1),
                "transportation_emissions_kg": round(data["transportation"], 1),
                "waste_emissions_kg": round(data["waste"], 1),
                "net_total_emissions_kg": round(data["net_total"], 1),
                "mom_comparison": mom,
            })

        latest_month = sorted_months[-1]
        latest_data = monthly_totals[latest_month]
        prev_month = sorted_months[-2] if len(sorted_months) > 1 else None
        prev_data = monthly_totals[prev_month] if prev_month else None

        # Peak and lowest total emission months
        peak_net_month = max(sorted_months, key=lambda m: monthly_totals[m]["net_total"])
        trough_net_month = min(sorted_months, key=lambda m: monthly_totals[m]["net_total"])

        # 3. Integrate ML Prediction Service (XGBoost pipeline)
        ml_context: Dict[str, Any] = {
            "is_available": False,
            "status": "unloaded",
            "forecast_points": [],
        }

        # Check if ML forecasting is valid and should be included
        try:
            model_info = MlPredictionService.get_model_info()
            ml_context["model_version"] = model_info.model_version
            ml_context["algorithm"] = model_info.algorithm
            ml_context["evaluation_metrics"] = model_info.evaluation_metrics
            ml_context["is_loaded"] = model_info.is_loaded

            if model_info.is_loaded and len(sorted_months) >= 2:
                # Obtain ML forecast points
                forecast_res = await MlPredictionService.get_emissions_trend_forecast(
                    workspace_id=workspace_id,
                    db=db,
                    forecast_horizon_months=3,
                )
                if forecast_res.status == "success" and forecast_res.forecast_series:
                    ml_context["is_available"] = True
                    ml_context["status"] = "success"
                    ml_context["forecast_points"] = [
                        {
                            "month": pt.month,
                            "predicted_emissions_kg": pt.predicted_emissions_kg,
                            "unit": pt.unit,
                            "confidence_interval_95_pct": [pt.confidence_interval_lower, pt.confidence_interval_upper],
                        }
                        for pt in forecast_res.forecast_series
                    ]
                    ml_context["operational_baseline_assumption"] = (
                        "Forward predictions evaluate temporal trend features with feature inputs normalized against "
                        "workspace historical operational averages."
                    )
                else:
                    ml_context["status"] = forecast_res.status
                    ml_context["limitations"] = forecast_res.limitations or "Forecast not available for current data distribution."
            elif len(sorted_months) < 2:
                ml_context["status"] = "insufficient_history"
                ml_context["limitations"] = "At least 2 distinct monthly reporting periods are required for statistical trend momentum and XGBoost forecast generation."
        except Exception as ml_err:
            logger.warning("Could not obtain ML prediction context: %s", ml_err)
            ml_context["status"] = "error"
            ml_context["limitations"] = "ML forecasting pipeline temporarily unavailable."

        # Fleet route optimization if bus routes exist
        route_proposals = optimize_bus_routes(bus_routes) if bus_routes else []
        route_opportunity = None
        if route_proposals:
            rp = route_proposals[0]
            route_opportunity = {
                "title": rp.title,
                "summary": rp.summary,
                "monthly_fuel_savings_liters": rp.estimated_fuel_savings_liters,
                "monthly_cost_savings_inr": rp.estimated_monthly_savings_inr,
                "monthly_emissions_reduction_kg": rp.estimated_emissions_reduction_kg,
            }

        selected_history = monthly_series if (intent["is_trend"] or len(monthly_series) <= 6) else monthly_series[-6:]

        limitations = []
        if len(sorted_months) < 2:
            limitations.append("Multi-month historical trend analysis requires at least two distinct reporting periods.")
        if len(elec_records) == 0:
            limitations.append("Electricity consumption unrecorded for this workspace.")
        if len(trans_records) == 0 and len(bus_routes) == 0:
            limitations.append("Transportation activity unrecorded for this workspace.")
        if len(waste_records) == 0:
            limitations.append("Solid waste streams unrecorded for this workspace.")

        return {
            "module": "insights",
            "workspace": meta,
            "has_records": True,
            "total_records_analyzed": total_records_count,
            "reporting_period": f"{sorted_months[0]} to {sorted_months[-1]}" if len(sorted_months) > 1 else sorted_months[0],
            "portfolio_totals": {
                "total_net_emissions_kg": net_total,
                "total_gross_positive_emissions_kg": gross_positive_emissions,
                "largest_source": largest_source_info,
            },
            "current_period": {
                "month": latest_month,
                "net_emissions_kg": round(latest_data["net_total"], 1),
                "electricity_emissions_kg": round(latest_data["electricity"], 1),
                "transportation_emissions_kg": round(latest_data["transportation"], 1),
                "waste_emissions_kg": round(latest_data["waste"], 1),
            },
            "previous_period_comparison": cls._compute_mom_comparison(
                latest_data["net_total"],
                prev_data["net_total"] if prev_data else None,
                "kg CO2e",
                "Net Portfolio Emissions",
            ),
            "historical_statistics": {
                "months_recorded": len(sorted_months),
                "average_monthly_net_emissions_kg": round(net_total / len(sorted_months), 1),
                "peak_month": {
                    "month": peak_net_month,
                    "net_emissions_kg": round(monthly_totals[peak_net_month]["net_total"], 1),
                },
                "lowest_month": {
                    "month": trough_net_month,
                    "net_emissions_kg": round(monthly_totals[trough_net_month]["net_total"], 1),
                },
            },
            "historical_monthly_trends": selected_history,
            "categories_summary": categories_data,
            "bus_fleet_opportunity": route_opportunity,
            "ml_prediction_forecasting": ml_context,
            "data_limitations": limitations,
        }

