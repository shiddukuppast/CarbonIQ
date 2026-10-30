from collections import defaultdict
from typing import Any, Dict, List, Optional
from app.calculations.electricity_calculator import calculate_electricity_emissions
from app.core.exceptions import EntityNotFoundException
from app.schemas.electricity import (
    ElectricityCreateRequest,
    ElectricityRecordResponse,
    ElectricitySummaryResponse,
    ElectricityUpdateRequest,
    MonthlyElectricityTrend,
)
from app.utils.dates import utc_iso
from app.utils.ids import generate_id


async def create_electricity_record(
    req: ElectricityCreateRequest,
    workspace_id: str,
    user_id: str,
    db: Any,
) -> ElectricityRecordResponse:
    calc = calculate_electricity_emissions(req.consumption_kwh, source=req.source)
    now = utc_iso()
    record_id = generate_id("elec")

    doc = {
        "id": record_id,
        "workspace_id": workspace_id,
        "creator_id": user_id,
        "reporting_month": req.reporting_month,
        "consumption_kwh": req.consumption_kwh,
        "source": req.source or "Grid",
        "bill_amount_inr": req.bill_amount_inr,
        "building_or_department": req.building_or_department,
        "notes": req.notes,
        "calculated_emissions_kg": calc.calculated_emissions_kg,
        "emission_factor_used": calc.emission_factor_used,
        "factor_id": calc.factor_id,
        "factor_type": calc.factor_type,
        "factor_source": calc.factor_source,
        "factor_version": calc.factor_version,
        "calculation_boundary": calc.calculation_boundary,
        "created_at": now,
        "updated_at": now,
    }
    await db.electricity_records.insert_one(doc)
    return ElectricityRecordResponse(**doc)


async def list_electricity_records(
    workspace_id: str,
    db: Any,
    month: Optional[str] = None,
    skip: int = 0,
    limit: int = 100,
) -> List[ElectricityRecordResponse]:
    query: Dict[str, Any] = {"workspace_id": workspace_id}
    if month:
        query["reporting_month"] = month

    cursor = db.electricity_records.find(query).sort("reporting_month", -1).skip(skip).limit(limit)
    records = []
    async for item in cursor:
        item.pop("_id", None)
        item.setdefault("source", "Grid")
        records.append(ElectricityRecordResponse(**item))
    return records


async def get_electricity_record(
    record_id: str,
    workspace_id: str,
    db: Any,
) -> ElectricityRecordResponse:
    doc = await db.electricity_records.find_one({"id": record_id, "workspace_id": workspace_id})
    if not doc:
        raise EntityNotFoundException(f"Electricity record {record_id} not found.")
    doc.pop("_id", None)
    doc.setdefault("source", "Grid")
    return ElectricityRecordResponse(**doc)


async def update_electricity_record(
    record_id: str,
    req: ElectricityUpdateRequest,
    workspace_id: str,
    db: Any,
) -> ElectricityRecordResponse:
    doc = await db.electricity_records.find_one({"id": record_id, "workspace_id": workspace_id})
    if not doc:
        raise EntityNotFoundException(f"Electricity record {record_id} not found.")

    updates: Dict[str, Any] = {"updated_at": utc_iso()}
    new_consumption = req.consumption_kwh if req.consumption_kwh is not None else doc["consumption_kwh"]
    new_source = req.source if req.source is not None else doc.get("source", "Grid")

    if req.consumption_kwh is not None or req.source is not None:
        calc = calculate_electricity_emissions(new_consumption, source=new_source)
        updates["consumption_kwh"] = new_consumption
        updates["source"] = new_source
        updates["calculated_emissions_kg"] = calc.calculated_emissions_kg
        updates["emission_factor_used"] = calc.emission_factor_used
        updates["factor_id"] = calc.factor_id
        updates["factor_type"] = calc.factor_type
        updates["factor_source"] = calc.factor_source
        updates["factor_version"] = calc.factor_version
        updates["calculation_boundary"] = calc.calculation_boundary

    if req.reporting_month is not None:
        updates["reporting_month"] = req.reporting_month
    if req.bill_amount_inr is not None:
        updates["bill_amount_inr"] = req.bill_amount_inr
    if req.building_or_department is not None:
        updates["building_or_department"] = req.building_or_department
    if req.notes is not None:
        updates["notes"] = req.notes

    await db.electricity_records.update_one({"id": record_id, "workspace_id": workspace_id}, {"$set": updates})
    updated_doc = await db.electricity_records.find_one({"id": record_id, "workspace_id": workspace_id})
    updated_doc.pop("_id", None)
    updated_doc.setdefault("source", "Grid")
    return ElectricityRecordResponse(**updated_doc)


async def delete_electricity_record(
    record_id: str,
    workspace_id: str,
    db: Any,
) -> Dict[str, Any]:
    res = await db.electricity_records.delete_one({"id": record_id, "workspace_id": workspace_id})
    if res.deleted_count == 0:
        raise EntityNotFoundException(f"Electricity record {record_id} not found.")
    return {"success": True, "deleted_id": record_id}


async def get_electricity_summary(
    workspace_id: str,
    db: Any,
) -> ElectricitySummaryResponse:
    cursor = db.electricity_records.find({"workspace_id": workspace_id}).sort("reporting_month", 1)
    records = []
    async for item in cursor:
        item.pop("_id", None)
        item.setdefault("source", "Grid")
        records.append(item)

    if not records:
        return ElectricitySummaryResponse(
            total_consumption_kwh=0.0,
            total_bill_inr=0.0,
            total_calculated_emissions_kg=0.0,
            record_count=0,
            monthly_trends=[],
            department_breakdown=[],
            previous_period_comparison=None,
        )

    total_kwh = sum(float(r.get("consumption_kwh") or r.get("kwh") or 0.0) for r in records)
    total_bill = sum(float(r.get("bill_amount_inr") or r.get("cost_inr") or 0.0) for r in records)
    total_emissions = sum(float(r.get("calculated_emissions_kg") or r.get("emissions_kg") or 0.0) for r in records)

    # Monthly Trends Aggregation
    month_map: Dict[str, Dict[str, float]] = defaultdict(lambda: {"consumption_kwh": 0.0, "bill_amount_inr": 0.0, "emissions": 0.0})
    dept_map: Dict[str, float] = defaultdict(float)

    for r in records:
        raw_m = r.get("reporting_month") or r.get("date") or r.get("period") or r.get("month") or "2026-01"
        from app.utils.dates import normalize_month
        m = normalize_month(str(raw_m))
        kwh = float(r.get("consumption_kwh") or r.get("kwh") or 0.0)
        bill = float(r.get("bill_amount_inr") or r.get("cost_inr") or 0.0)
        em = float(r.get("calculated_emissions_kg") or r.get("emissions_kg") or 0.0)

        month_map[m]["consumption_kwh"] += kwh
        month_map[m]["bill_amount_inr"] += bill
        month_map[m]["emissions"] += em

        dept = r.get("building_or_department") or "Unassigned"
        dept_map[dept] += kwh

    monthly_trends = [
        MonthlyElectricityTrend(
            reporting_month=m,
            consumption_kwh=round(data["consumption_kwh"], 1),
            bill_amount_inr=round(data["bill_amount_inr"], 0),
            calculated_emissions_kg=round(data["emissions"], 1),
        )
        for m, data in sorted(month_map.items())
    ]

    dept_breakdown = [
        {
            "department": d,
            "consumption_kwh": round(kwh, 1),
            "percentage": round((kwh / total_kwh) * 100, 1) if total_kwh > 0 else 0.0,
        }
        for d, kwh in sorted(dept_map.items(), key=lambda x: x[1], reverse=True)
    ]

    # Comparison of the latest two months
    comparison = None
    if len(monthly_trends) >= 2:
        latest = monthly_trends[-1]
        previous = monthly_trends[-2]
        kwh_diff = round(latest.consumption_kwh - previous.consumption_kwh, 1)
        pct_change = round((kwh_diff / previous.consumption_kwh) * 100, 1) if previous.consumption_kwh > 0 else 0.0
        comparison = {
            "latest_month": latest.reporting_month,
            "previous_month": previous.reporting_month,
            "kwh_difference": kwh_diff,
            "percentage_change": pct_change,
            "trend_direction": "increased" if kwh_diff > 0 else "decreased" if kwh_diff < 0 else "unchanged",
        }

    return ElectricitySummaryResponse(
        total_consumption_kwh=round(total_kwh, 1),
        total_bill_inr=round(total_bill, 0),
        total_calculated_emissions_kg=round(total_emissions, 1),
        record_count=len(records),
        monthly_trends=monthly_trends,
        department_breakdown=dept_breakdown,
        previous_period_comparison=comparison,
    )
