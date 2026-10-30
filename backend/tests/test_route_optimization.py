import pytest
from app.calculations.route_optimizer import optimize_bus_routes


def test_candidate_route_consolidation_algorithm():
    routes = [
        {
            "id": "route_A",
            "route_name": "Route A",
            "start_location": "Hebbal",
            "destination": "Main Campus",
            "intermediate_stops": ["Hebbal", "Jakkur Cross"],
            "distance_km": 30.0,
            "duration_minutes": 50,
            "trips_per_day": 2,
            "assigned_students": 20,
            "seating_capacity": 40,
            "fuel_efficiency_km_per_l": 5.0,
            "current_buses_count": 1,
        },
        {
            "id": "route_B",
            "route_name": "Route B",
            "start_location": "Sahakar Nagar",
            "destination": "Main Campus",
            "intermediate_stops": ["Sahakar Nagar", "Jakkur Cross"],
            "distance_km": 28.0,
            "duration_minutes": 45,
            "trips_per_day": 2,
            "assigned_students": 15,
            "seating_capacity": 40,
            "fuel_efficiency_km_per_l": 5.0,
            "current_buses_count": 1,
        },
    ]

    proposals = optimize_bus_routes(routes)
    assert len(proposals) == 1
    p = proposals[0]

    assert p.capacity_check_passed is True
    assert p.current_config.students_served == 35
    assert p.proposed_config.buses_count == 1
    # Current distance = 30 + 28 = 58 km
    assert p.current_config.total_distance_km == 58.0
    # Proposed distance = max(30, 28) * 1.15 + 3 = 34.5 + 3 = 37.5 -> 38 km
    assert p.proposed_config.total_distance_km < 58.0
    assert p.estimated_distance_reduction_km > 0
    assert p.estimated_fuel_savings_liters > 0
    assert p.estimated_monthly_savings_inr > 0
    assert p.feasibility == "High"  # Has shared stop "Jakkur Cross"


def test_overcapacity_routes_rejected():
    routes = [
        {
            "id": "route_1",
            "route_name": "Heavy 1",
            "destination": "Main Campus",
            "intermediate_stops": ["Common Stop"],
            "distance_km": 30.0,
            "assigned_students": 28,
            "seating_capacity": 40,
        },
        {
            "id": "route_2",
            "route_name": "Heavy 2",
            "destination": "Main Campus",
            "intermediate_stops": ["Common Stop"],
            "distance_km": 25.0,
            "assigned_students": 22,
            "seating_capacity": 40,
        },
    ]
    # Total = 50 students > 40 max capacity
    proposals = optimize_bus_routes(routes)
    assert len(proposals) == 0


def test_staggered_schedule_proposal_when_targeted():
    routes = [
        {
            "id": "route_A",
            "route_name": "Route A",
            "start_location": "Hebbal",
            "destination": "College Campus",
            "intermediate_stops": ["Hebbal"],
            "distance_km": 30.0,
            "duration_minutes": 50,
            "trips_per_day": 2,
            "assigned_students": 25,
            "seating_capacity": 40,
            "fuel_efficiency_km_per_l": 5.0,
            "current_buses_count": 1,
        },
        {
            "id": "route_B",
            "route_name": "Route B",
            "start_location": "Sahakar Nagar",
            "destination": "College Campus",
            "intermediate_stops": ["Sahakar Nagar"],
            "distance_km": 28.0,
            "duration_minutes": 45,
            "trips_per_day": 2,
            "assigned_students": 20,
            "seating_capacity": 40,
            "fuel_efficiency_km_per_l": 5.0,
            "current_buses_count": 1,
        },
    ]

    # Without targeted flag, direct consolidation rejects overcapacity (25+20=45 > 40)
    assert len(optimize_bus_routes(routes, is_targeted=False)) == 0

    # With targeted flag, staggered schedule optimization proposal is generated
    proposals = optimize_bus_routes(routes, is_targeted=True)
    assert len(proposals) == 1
    p = proposals[0]

    assert p.capacity_check_passed is False
    assert p.feasibility == "Needs Validation"
    assert p.current_config.students_served == 45
    assert p.current_config.buses_count == 2
    assert p.proposed_config.buses_count == 1
    assert p.proposed_config.total_distance_km == 58.0
    assert p.estimated_distance_reduction_km == 0.0
    assert p.estimated_fuel_savings_liters == 0.0
    assert p.estimated_monthly_savings_inr == 0.0
    assert p.estimated_emissions_reduction_kg == 0.0
    assert "staggered" in p.title.lower()
    assert "sequential" in p.summary.lower()




def test_unrelated_destinations_not_combined():
    routes = [
        {
            "id": "route_north",
            "route_name": "North",
            "destination": "Campus North",
            "intermediate_stops": ["Stop 1"],
            "assigned_students": 10,
            "seating_capacity": 40,
        },
        {
            "id": "route_south",
            "route_name": "South",
            "destination": "Campus South (Different City)",
            "intermediate_stops": ["Stop 2"],
            "assigned_students": 10,
            "seating_capacity": 40,
        },
    ]
    proposals = optimize_bus_routes(routes)
    assert len(proposals) == 0


def test_staggered_schedule_proposal_when_targeted():
    routes = [
        {
            "id": "route_A",
            "route_name": "Route A",
            "start_location": "Hebbal",
            "destination": "College Campus",
            "intermediate_stops": ["Hebbal"],
            "distance_km": 30.0,
            "duration_minutes": 50,
            "trips_per_day": 2,
            "assigned_students": 25,
            "seating_capacity": 40,
            "fuel_efficiency_km_per_l": 5.0,
            "current_buses_count": 1,
        },
        {
            "id": "route_B",
            "route_name": "Route B",
            "start_location": "Sahakar Nagar",
            "destination": "College Campus",
            "intermediate_stops": ["Sahakar Nagar"],
            "distance_km": 28.0,
            "duration_minutes": 45,
            "trips_per_day": 2,
            "assigned_students": 20,
            "seating_capacity": 40,
            "fuel_efficiency_km_per_l": 5.0,
            "current_buses_count": 1,
        },
    ]

    # Without targeted flag, direct consolidation rejects overcapacity (25+20=45 > 40)
    assert len(optimize_bus_routes(routes, is_targeted=False)) == 0

    # With targeted flag, staggered schedule optimization proposal is generated
    proposals = optimize_bus_routes(routes, is_targeted=True)
    assert len(proposals) == 1
    p = proposals[0]

    assert p.capacity_check_passed is False
    assert p.feasibility == "Needs Validation"
    assert p.current_config.students_served == 45
    assert p.current_config.buses_count == 2
    assert p.proposed_config.buses_count == 1
    assert p.proposed_config.total_distance_km == 58.0
    assert p.estimated_distance_reduction_km == 0.0
    assert p.estimated_fuel_savings_liters == 0.0
    assert p.estimated_monthly_savings_inr == 0.0
    assert p.estimated_emissions_reduction_kg == 0.0
    assert "staggered" in p.title.lower()
    assert "sequential" in p.summary.lower()


