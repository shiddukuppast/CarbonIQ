import pytest
from app.calculations.electricity_calculator import (
    calculate_electricity_emissions,
    calculate_electricity_savings_scenario,
)
from app.calculations.savings_calculator import (
    simulate_electricity_savings,
    simulate_transportation_savings,
    simulate_waste_savings,
)
from app.calculations.transportation_calculator import calculate_transportation_emissions
from app.calculations.waste_calculator import calculate_recycling_rate, calculate_waste_emissions


def test_electricity_emissions_formula():
    res = calculate_electricity_emissions(1240.0)
    assert res.is_valid is True
    # 1240 * 0.82 = 1016.8
    assert res.calculated_emissions_kg == 1016.8
    assert res.emission_factor_used == 0.82
    assert res.factor_type == "illustrative_grid_factor"


def test_electricity_negative_consumption():
    res = calculate_electricity_emissions(-10.0)
    assert res.is_valid is False
    assert res.calculated_emissions_kg == 0.0


def test_electricity_savings_scenario():
    # 1,240 kWh × 15% reduction = 186 kWh reduction
    # Tariff @ ₹8.5/kWh = 186 * 8.5 = ₹1,581
    scenario = calculate_electricity_savings_scenario(1240.0, 15.0, tariff_inr=8.5)
    assert scenario.kwh_reduction == 186.0
    assert scenario.cost_savings_inr == 1581.0
    assert scenario.emissions_reduction_kg == round(186.0 * 0.82, 1)


def test_transportation_emissions_methods_separation():
    # Method 1: Actual fuel (100 L Diesel * 2.68 = 268 kg CO2e)
    m1 = calculate_transportation_emissions(
        distance_km=450.0,
        fuel_type="Diesel",
        fuel_consumed_liters=100.0,
        fuel_efficiency_km_per_l=4.5,
    )
    assert m1.calculation_method == "actual_fuel"
    assert m1.calculated_fuel_liters == 100.0
    assert m1.calculated_emissions_kg == 268.0

    # Method 2: Distance / Efficiency (450 / 4.5 = 100 L Petrol * 2.31 = 231 kg CO2e)
    m2 = calculate_transportation_emissions(
        distance_km=450.0,
        fuel_type="Petrol",
        fuel_consumed_liters=None,
        fuel_efficiency_km_per_l=4.5,
    )
    assert m2.calculation_method == "distance_efficiency_estimate"
    assert m2.calculated_fuel_liters == 100.0
    assert m2.calculated_emissions_kg == 231.0

    # Missing both: uncalculated
    m3 = calculate_transportation_emissions(distance_km=200.0)
    assert m3.calculation_method == "uncalculated"
    assert m3.calculated_emissions_kg == 0.0


def test_waste_emissions_and_net_credits():
    compost = calculate_waste_emissions(50.0, "Composting")
    assert compost.calculated_emissions_kg == 5.0  # 50 * 0.10

    recycle = calculate_waste_emissions(100.0, "Recycling")
    assert recycle.calculated_emissions_kg == -45.0  # 100 * -0.45

    landfill = calculate_waste_emissions(80.0, "Landfill")
    assert landfill.calculated_emissions_kg == 100.0  # 80 * 1.25


def test_waste_recycling_rate_edge_cases():
    assert calculate_recycling_rate(0, 0) is None
    assert calculate_recycling_rate(50, 100) == 50.0
    assert calculate_recycling_rate(100, 100) == 100.0


def test_simulators_do_not_modify_state():
    sim_elec = simulate_electricity_savings(1000.0, 20.0)
    assert sim_elec.difference["kwh_reduction"] == 200.0
    assert sim_elec.estimated_cost_savings_inr == 1700.0  # 200 * 8.5

    sim_trans = simulate_transportation_savings(1000.0, 10.0, fuel_efficiency_km_per_l=5.0)
    assert sim_trans.difference["distance_reduction_km"] == 100.0
    assert sim_trans.difference["fuel_savings_liters"] == 20.0  # 100 / 5

    sim_waste = simulate_waste_savings(500.0, 10.0, target_recycling_percent=50.0)
    assert sim_waste.difference["quantity_reduction_kg"] == 50.0
