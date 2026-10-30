from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field
from app.data.emission_factors import EMISSION_FACTORS, BENCHMARK_PRICES
from app.utils.ids import generate_id


class RouteConfigSummary(BaseModel):
    route_ids: List[str]
    route_names: List[str]
    buses_count: int
    students_served: int
    total_distance_km: float
    daily_fuel_consumption_liters: float
    monthly_fuel_cost_inr: float
    monthly_emissions_kg: float


class RouteOptimizationProposal(BaseModel):
    id: str
    title: str
    summary: str
    reason: str
    capacity_check_passed: bool
    current_config: RouteConfigSummary
    proposed_config: RouteConfigSummary
    estimated_distance_reduction_km: float
    estimated_fuel_savings_liters: float
    estimated_monthly_savings_inr: float
    estimated_emissions_reduction_kg: float
    feasibility: str  # "High" | "Medium" | "Needs Validation"
    required_validation: List[str]
    assumptions: List[str]
    missing_information: Optional[List[str]] = None
    status: str = "pending"  # "pending" | "accepted" | "rejected" | "implemented"


def optimize_bus_routes(
    routes_data: List[Dict[str, Any]],
    is_targeted: bool = False,
) -> List[RouteOptimizationProposal]:
    """
    Evaluates candidate bus routes for feasible consolidation opportunities.
    Considers student demand, seating capacity constraints, shared corridors,
    and realistic detour penalties without fabricating unverified GPS coordinates.
    """
    proposals: List[RouteOptimizationProposal] = []
    if len(routes_data) < 2:
        return proposals

    operating_days_per_month = 22
    diesel_price = BENCHMARK_PRICES["diesel_inr_per_l"]
    diesel_factor = EMISSION_FACTORS["fuel_diesel_standard"].value

    for i in range(len(routes_data)):
        for j in range(i + 1, len(routes_data)):
            r_a = routes_data[i]
            r_b = routes_data[j]

            # Compare destinations and intermediate stops
            dest_a = str(r_a.get("destination", "")).strip().lower()
            dest_b = str(r_b.get("destination", "")).strip().lower()
            same_destination = bool(dest_a and dest_b and dest_a == dest_b)

            stops_a = [str(s).strip().lower() for s in r_a.get("intermediate_stops", []) if str(s).strip()]
            stops_b = [str(s).strip().lower() for s in r_b.get("intermediate_stops", []) if str(s).strip()]
            shared_stops = [s for s in stops_a if s in stops_b]

            # Require either identical campus destination or confirmed shared intermediate pickup points
            if not (same_destination or len(shared_stops) > 0):
                continue

            students_a = int(r_a.get("assigned_students", 0))
            students_b = int(r_b.get("assigned_students", 0))
            total_students = students_a + students_b

            cap_a = int(r_a.get("seating_capacity", 40))
            cap_b = int(r_b.get("seating_capacity", 40))
            max_capacity = max(cap_a, cap_b)

            dist_a = float(r_a.get("distance_km", 0.0))
            dist_b = float(r_b.get("distance_km", 0.0))
            current_total_dist = dist_a + dist_b

            eff_a = max(1.0, float(r_a.get("fuel_efficiency_km_per_l", 4.5)))
            eff_b = max(1.0, float(r_b.get("fuel_efficiency_km_per_l", 4.5)))
            avg_eff = round((eff_a + eff_b) / 2.0, 2)

            trips_a = max(1, int(r_a.get("trips_per_day", 2)))
            trips_b = max(1, int(r_b.get("trips_per_day", 2)))
            max_trips = max(trips_a, trips_b)

            current_daily_fuel = round((dist_a * trips_a) / eff_a + (dist_b * trips_b) / eff_b, 1)

            name_a = str(r_a.get("route_name", f"Route {r_a.get('id', 'A')}"))
            name_b = str(r_b.get("route_name", f"Route {r_b.get('id', 'B')}"))
            id_a = str(r_a.get("id", "a"))
            id_b = str(r_b.get("id", "b"))

            buses_a = int(r_a.get("current_buses_count", 1))
            buses_b = int(r_b.get("current_buses_count", 1))

            current_config = RouteConfigSummary(
                route_ids=[id_a, id_b],
                route_names=[name_a, name_b],
                buses_count=buses_a + buses_b,
                students_served=total_students,
                total_distance_km=current_total_dist,
                daily_fuel_consumption_liters=current_daily_fuel,
                monthly_fuel_cost_inr=round(current_daily_fuel * operating_days_per_month * diesel_price, 0),
                monthly_emissions_kg=round(current_daily_fuel * operating_days_per_month * diesel_factor, 1),
            )

            # Constraint: Combined students must not exceed the capacity of a single consolidated vehicle
            capacity_check_passed = total_students <= max_capacity
            if not capacity_check_passed:
                # Direct single-trip consolidation is infeasible.
                # If candidate routes were explicitly targeted for optimization and each route
                # individually fits within vehicle capacity, evaluate staggered schedule optimization.
                if is_targeted and students_a <= cap_a and students_b <= cap_b:
                    proposed_config = RouteConfigSummary(
                        route_ids=[f"{id_a}-{id_b}-staggered"],
                        route_names=[f"Staggered: {name_a} + {name_b}"],
                        buses_count=1,
                        students_served=total_students,
                        total_distance_km=current_total_dist,
                        daily_fuel_consumption_liters=current_daily_fuel,
                        monthly_fuel_cost_inr=round(current_daily_fuel * operating_days_per_month * diesel_price, 0),
                        monthly_emissions_kg=round(current_daily_fuel * operating_days_per_month * diesel_factor, 1),
                    )

                    proposal = RouteOptimizationProposal(
                        id=generate_id("opt"),
                        title=f"Staggered Schedule Bus Optimization: {name_a} & {name_b}",
                        summary=(
                            f"Deploy 1 bus across staggered operating schedules for {name_a} ({students_a} students) "
                            f"and {name_b} ({students_b} students). Passengers are transported in two sequential trips "
                            f"without exceeding the {max_capacity}-seat capacity limit on any single trip."
                        ),
                        reason=(
                            f"Both routes travel to {r_a.get('destination', 'destination')}. Simultaneous consolidation is not feasible "
                            f"as combined demand ({total_students} students) exceeds maximum bus capacity ({max_capacity} seats). "
                            f"However, individual route demands ({students_a} and {students_b} students) each fit within {max_capacity} seats, "
                            f"allowing 1 bus to service both routes in staggered shifts."
                        ),
                        capacity_check_passed=False,
                        current_config=current_config,
                        proposed_config=proposed_config,
                        estimated_distance_reduction_km=0.0,
                        estimated_fuel_savings_liters=0.0,
                        estimated_monthly_savings_inr=0.0,
                        estimated_emissions_reduction_kg=0.0,
                        feasibility="Needs Validation",
                        required_validation=[
                            "Validate campus timetable and class schedules to confirm arrival windows allow sequential shifts.",
                            "Confirm vehicle turnaround and driver duty hours permit operating both routes consecutively.",
                            f"Verify that total simultaneous passenger count never exceeds {max_capacity} on any single trip.",
                        ],
                        assumptions=[
                            "1 bus operates sequential shifts for both routes; trips are not run simultaneously.",
                            f"Total daily distance remains {current_total_dist} km as both trips must be operated.",
                            "Fleet optimization reduces active fleet requirement from 2 buses to 1 bus.",
                        ],
                        missing_information=[
                            "Detailed class start times and permissible arrival windows are not provided.",
                            "Deadhead transit distance between the end of Route 1 and start of Route 2 is not specified.",
                        ],
                        status="pending",
                    )
                    proposals.append(proposal)
                continue

            dist_a = float(r_a.get("distance_km", 0.0))
            dist_b = float(r_b.get("distance_km", 0.0))
            current_total_dist = dist_a + dist_b

            eff_a = max(1.0, float(r_a.get("fuel_efficiency_km_per_l", 4.5)))
            eff_b = max(1.0, float(r_b.get("fuel_efficiency_km_per_l", 4.5)))
            avg_eff = round((eff_a + eff_b) / 2.0, 2)

            trips_a = max(1, int(r_a.get("trips_per_day", 2)))
            trips_b = max(1, int(r_b.get("trips_per_day", 2)))
            max_trips = max(trips_a, trips_b)

            # Modeled combined route distance: longest route plus a 15% detour penalty + stop overhead
            overhead_km = 3.0 if shared_stops else 6.0
            combined_dist = round(max(dist_a, dist_b) * 1.15 + overhead_km, 1)
            dist_reduction = max(0.0, round(current_total_dist - combined_dist, 1))

            current_daily_fuel = round((dist_a * trips_a) / eff_a + (dist_b * trips_b) / eff_b, 1)
            proposed_daily_fuel = round((combined_dist * max_trips) / avg_eff, 1)
            daily_fuel_savings = max(0.0, round(current_daily_fuel - proposed_daily_fuel, 1))

            monthly_fuel_savings = round(daily_fuel_savings * operating_days_per_month, 1)
            monthly_cost_savings = round(monthly_fuel_savings * diesel_price, 0)
            monthly_emissions_savings = round(monthly_fuel_savings * diesel_factor, 1)

            name_a = str(r_a.get("route_name", f"Route {r_a.get('id', 'A')}"))
            name_b = str(r_b.get("route_name", f"Route {r_b.get('id', 'B')}"))
            id_a = str(r_a.get("id", "a"))
            id_b = str(r_b.get("id", "b"))

            buses_a = int(r_a.get("current_buses_count", 1))
            buses_b = int(r_b.get("current_buses_count", 1))

            current_config = RouteConfigSummary(
                route_ids=[id_a, id_b],
                route_names=[name_a, name_b],
                buses_count=buses_a + buses_b,
                students_served=total_students,
                total_distance_km=current_total_dist,
                daily_fuel_consumption_liters=current_daily_fuel,
                monthly_fuel_cost_inr=round(current_daily_fuel * operating_days_per_month * diesel_price, 0),
                monthly_emissions_kg=round(current_daily_fuel * operating_days_per_month * diesel_factor, 1),
            )

            proposed_config = RouteConfigSummary(
                route_ids=[f"{id_a}-{id_b}-consolidated"],
                route_names=[f"Consolidated {name_a} + {name_b}"],
                buses_count=1,
                students_served=total_students,
                total_distance_km=combined_dist,
                daily_fuel_consumption_liters=proposed_daily_fuel,
                monthly_fuel_cost_inr=round(proposed_daily_fuel * operating_days_per_month * diesel_price, 0),
                monthly_emissions_kg=round(proposed_daily_fuel * operating_days_per_month * diesel_factor, 1),
            )

            shared_summary = (
                f"sharing {len(shared_stops)} intermediate stops"
                if shared_stops
                else f"both serving {r_a.get('destination', 'campus')}"
            )

            proposal = RouteOptimizationProposal(
                id=generate_id("opt"),
                title=f"Consolidate {name_a} & {name_b}",
                summary=(
                    f"Merge {name_a} ({students_a} students) and {name_b} ({students_b} students) "
                    f"into a single {max_capacity}-seater bus {shared_summary}."
                ),
                reason=(
                    f"Both routes travel along overlapping corridors to {r_a.get('destination', 'destination')}. "
                    f"Combined passenger demand ({total_students} students) is safely within the {max_capacity}-seat capacity limit."
                ),
                capacity_check_passed=True,
                current_config=current_config,
                proposed_config=proposed_config,
                estimated_distance_reduction_km=dist_reduction,
                estimated_fuel_savings_liters=monthly_fuel_savings,
                estimated_monthly_savings_inr=monthly_cost_savings,
                estimated_emissions_reduction_kg=monthly_emissions_savings,
                feasibility="High" if len(shared_stops) > 0 else "Medium",
                required_validation=[
                    "Verify morning pickup punctuality and schedule synchronization across both stops.",
                    f"Confirm that roads on intermediate stops allow a {max_capacity}-seater vehicle safely.",
                    "Review passenger agreement before changing published bus timings.",
                ],
                assumptions=[
                    f"Combined route distance modeled as {combined_dist} km (15% detour buffer + pickup overhead).",
                    f"Operating schedule: {operating_days_per_month} days/month with Diesel @ ₹{diesel_price}/L.",
                    f"Average fleet fuel efficiency: {avg_eff} km/L.",
                ],
                missing_information=[
                    "Live GPS turn-by-turn routing not active; distance estimated from reported route lengths.",
                    "Live traffic congestion metrics are not incorporated.",
                ],
                status="pending",
            )
            proposals.append(proposal)

    return proposals
