from collections import defaultdict
from typing import Any, Dict, List, Optional
from app.calculations.transportation_calculator import calculate_transportation_emissions
from app.core.exceptions import EntityNotFoundException
from app.schemas.transportation import (
    TransportationCreateRequest,
    TransportationRecordResponse,
    TransportationSummaryResponse,
    TransportationUpdateRequest,
)
from app.utils.dates import normalize_month, utc_iso
from app.utils.ids import generate_id


async def create_transportation_record(
    req: TransportationCreateRequest,
    workspace_id: str,
    user_id: str,
    db: Any,
) -> TransportationRecordResponse:
    calc = calculate_transportation_emissions(
        distance_km=req.distance_km,
        fuel_type=req.fuel_type or "Diesel",
        fuel_consumed_liters=req.fuel_consumed_liters,
        fuel_efficiency_km_per_l=req.fuel_efficiency_km_per_l,
    )
    now = utc_iso()
    record_id = generate_id("trans")

    doc = {
        "id": record_id,
        "workspace_id": workspace_id,
        "creator_id": user_id,
        "date": req.date,
        "mode": req.mode,
        "distance_km": req.distance_km,
        "fuel_type": req.fuel_type or "Diesel",
        "fuel_consumed_liters": req.fuel_consumed_liters,
        "fuel_efficiency_km_per_l": req.fuel_efficiency_km_per_l,
        "fuel_expenditure_inr": req.fuel_expenditure_inr,
        "vehicle_id": req.vehicle_id,
        "passenger_count": req.passenger_count,
        "vehicle_capacity": req.vehicle_capacity,
        "route_name": req.route_name,
        "pickup_locations": req.pickup_locations,
        "destination": req.destination,
        "notes": req.notes,
        "calculation_method": calc.calculation_method,
        "calculated_emissions_kg": calc.calculated_emissions_kg,
        "emission_factor_used": calc.emission_factor_used,
        "factor_id": calc.factor_id,
        "factor_source": calc.factor_source,
        "factor_version": calc.factor_version,
        "calculation_boundary": calc.calculation_boundary,
        "created_at": now,
        "updated_at": now,
    }
    await db.transportation_records.insert_one(doc)
    return TransportationRecordResponse(**doc)


async def list_transportation_records(
    workspace_id: str,
    db: Any,
    skip: int = 0,
    limit: int = 100,
) -> List[TransportationRecordResponse]:
    cursor = db.transportation_records.find({"workspace_id": workspace_id}).sort("date", -1).skip(skip).limit(limit)
    records = []
    async for item in cursor:
        item.pop("_id", None)
        records.append(TransportationRecordResponse(**item))
    return records


async def get_transportation_record(
    record_id: str,
    workspace_id: str,
    db: Any,
) -> TransportationRecordResponse:
    doc = await db.transportation_records.find_one({"id": record_id, "workspace_id": workspace_id})
    if not doc:
        raise EntityNotFoundException(f"Transportation record {record_id} not found.")
    doc.pop("_id", None)
    return TransportationRecordResponse(**doc)


async def update_transportation_record(
    record_id: str,
    req: TransportationUpdateRequest,
    workspace_id: str,
    db: Any,
) -> TransportationRecordResponse:
    doc = await db.transportation_records.find_one({"id": record_id, "workspace_id": workspace_id})
    if not doc:
        raise EntityNotFoundException(f"Transportation record {record_id} not found.")

    updates: Dict[str, Any] = {"updated_at": utc_iso()}

    new_dist = req.distance_km if req.distance_km is not None else doc["distance_km"]
    new_fuel_type = req.fuel_type if req.fuel_type is not None else doc.get("fuel_type", "Diesel")
    new_fuel_consumed = req.fuel_consumed_liters if req.fuel_consumed_liters is not None else doc.get("fuel_consumed_liters")
    new_efficiency = req.fuel_efficiency_km_per_l if req.fuel_efficiency_km_per_l is not None else doc.get("fuel_efficiency_km_per_l")

    calc = calculate_transportation_emissions(
        distance_km=new_dist,
        fuel_type=new_fuel_type,
        fuel_consumed_liters=new_fuel_consumed,
        fuel_efficiency_km_per_l=new_efficiency,
    )

    updates["distance_km"] = new_dist
    updates["fuel_type"] = new_fuel_type
    updates["fuel_consumed_liters"] = new_fuel_consumed
    updates["fuel_efficiency_km_per_l"] = new_efficiency
    updates["calculation_method"] = calc.calculation_method
    updates["calculated_emissions_kg"] = calc.calculated_emissions_kg
    updates["emission_factor_used"] = calc.emission_factor_used
    updates["factor_id"] = calc.factor_id
    updates["factor_source"] = calc.factor_source
    updates["factor_version"] = calc.factor_version
    updates["calculation_boundary"] = calc.calculation_boundary

    if req.date is not None:
        updates["date"] = req.date
    if req.mode is not None:
        updates["mode"] = req.mode
    if req.fuel_expenditure_inr is not None:
        updates["fuel_expenditure_inr"] = req.fuel_expenditure_inr
    if req.vehicle_id is not None:
        updates["vehicle_id"] = req.vehicle_id
    if req.passenger_count is not None:
        updates["passenger_count"] = req.passenger_count
    if req.vehicle_capacity is not None:
        updates["vehicle_capacity"] = req.vehicle_capacity
    if req.route_name is not None:
        updates["route_name"] = req.route_name
    if req.pickup_locations is not None:
        updates["pickup_locations"] = req.pickup_locations
    if req.destination is not None:
        updates["destination"] = req.destination
    if req.notes is not None:
        updates["notes"] = req.notes

    await db.transportation_records.update_one({"id": record_id, "workspace_id": workspace_id}, {"$set": updates})
    updated_doc = await db.transportation_records.find_one({"id": record_id, "workspace_id": workspace_id})
    updated_doc.pop("_id", None)
    return TransportationRecordResponse(**updated_doc)


async def delete_transportation_record(
    record_id: str,
    workspace_id: str,
    db: Any,
) -> Dict[str, Any]:
    res = await db.transportation_records.delete_one({"id": record_id, "workspace_id": workspace_id})
    if res.deleted_count == 0:
        raise EntityNotFoundException(f"Transportation record {record_id} not found.")
    return {"success": True, "deleted_id": record_id}


async def get_transportation_summary(
    workspace_id: str,
    db: Any,
) -> TransportationSummaryResponse:
    cursor = db.transportation_records.find({"workspace_id": workspace_id}).sort("date", 1)
    records = []
    async for item in cursor:
        item.pop("_id", None)
        records.append(item)

    if not records:
        return TransportationSummaryResponse(
            total_distance_km=0.0,
            total_fuel_liters=0.0,
            total_expenditure_inr=0.0,
            total_calculated_emissions_kg=0.0,
            record_count=0,
            mode_breakdown=[],
            monthly_trends=[],
        )

    total_dist = sum(float(r.get("distance_km") or r.get("distance") or 0.0) for r in records)
    total_fuel = sum(
        float(r.get("fuel_consumed_liters") or r.get("fuel_liters") or (
            (float(r.get("distance_km", 0.0) or 0.0) / float(r["fuel_efficiency_km_per_l"]))
            if r.get("fuel_efficiency_km_per_l") and float(r["fuel_efficiency_km_per_l"]) > 0 else 0.0
        ))
        for r in records
    )
    total_expenditure = sum(float(r.get("fuel_expenditure_inr") or r.get("expenditure_inr") or 0.0) for r in records)
    total_emissions = sum(float(r.get("calculated_emissions_kg") or r.get("emissions_kg") or 0.0) for r in records)

    mode_map: Dict[str, Dict[str, float]] = defaultdict(lambda: {"distance_km": 0.0, "emissions": 0.0, "trips": 0})
    month_map: Dict[str, Dict[str, float]] = defaultdict(lambda: {"distance_km": 0.0, "fuel_liters": 0.0, "emissions": 0.0})

    for r in records:
        mode = r.get("mode", "Other")
        dist = float(r.get("distance_km") or r.get("distance") or 0.0)
        em = float(r.get("calculated_emissions_kg") or r.get("emissions_kg") or 0.0)
        mode_map[mode]["distance_km"] += dist
        mode_map[mode]["emissions"] += em
        mode_map[mode]["trips"] += 1

        raw_m = r.get("date") or r.get("reporting_month") or r.get("month") or "2026-01"
        month_key = normalize_month(str(raw_m))
        month_map[month_key]["distance_km"] += dist
        month_map[month_key]["emissions"] += em
        eff = float(r.get("fuel_efficiency_km_per_l") or 0.0)
        if r.get("fuel_consumed_liters"):
            month_map[month_key]["fuel_liters"] += float(r["fuel_consumed_liters"])
        elif eff > 0:
            month_map[month_key]["fuel_liters"] += dist / eff

    mode_breakdown = [
        {
            "mode": m,
            "distance_km": round(data["distance_km"], 1),
            "calculated_emissions_kg": round(data["emissions"], 1),
            "percentage": round((data["emissions"] / total_emissions) * 100, 1) if total_emissions > 0 else 0.0,
            "trips_count": data["trips"],
        }
        for m, data in sorted(mode_map.items(), key=lambda x: x[1]["emissions"], reverse=True)
    ]

    monthly_trends = [
        {
            "month": m,
            "distance_km": round(data["distance_km"], 1),
            "fuel_liters": round(data["fuel_liters"], 1),
            "emissions_kg": round(data["emissions"], 1),
        }
        for m, data in sorted(month_map.items())
    ]

    return TransportationSummaryResponse(
        total_distance_km=round(total_dist, 1),
        total_fuel_liters=round(total_fuel, 1),
        total_expenditure_inr=round(total_expenditure, 0),
        total_calculated_emissions_kg=round(total_emissions, 1),
        record_count=len(records),
        mode_breakdown=mode_breakdown,
        monthly_trends=monthly_trends,
    )
