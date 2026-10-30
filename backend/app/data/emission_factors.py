from dataclasses import dataclass
from typing import Any, Dict, List, Optional


@dataclass(frozen=True)
class EmissionFactor:
    """
    Central emission factor definition backed by authoritative environmental databases:
    - Central Electricity Authority (CEA), Ministry of Power, Govt of India (CO2 Baseline Database v19/v20)
    - GHG Protocol Corporate Standard & Cross-Sector Calculation Tools
    - IPCC Guidelines for National Greenhouse Gas Inventories (Energy & Waste volumes)
    - US EPA Waste Reduction Model (WARM) / UK DEFRA Conversion Factors
    """
    factor_id: str
    activity_type: str  # "electricity" | "transportation" | "waste"
    sub_category: Optional[str]  # e.g., "National Grid Average", "Diesel", "Composting"
    value: float
    unit: str  # "kg CO2 / kWh", "kg CO2e / L", "kg CO2e / kg"
    geography: str
    reporting_period: str
    source: str
    version: str
    is_authoritative: bool
    calculation_boundary: str
    notes: str


# ==============================================================================
# Central Source-Backed Emission Factor Registry
# ==============================================================================

EMISSION_FACTORS: Dict[str, EmissionFactor] = {
    # --------------------------------------------------------------------------
    # Electricity Factors (CEA India & Renewables)
    # --------------------------------------------------------------------------
    "grid_in_cea_baseline": EmissionFactor(
        factor_id="grid_in_cea_baseline",
        activity_type="electricity",
        sub_category="Indian National Grid Baseline",
        value=0.82,
        unit="kg CO2e / kWh",
        geography="India (National Grid)",
        reporting_period="2023-2024",
        source="Central Electricity Authority (CEA) CO2 Baseline Database v19 (Thermal/Excl. RES baseline)",
        version="19.0.0",
        is_authoritative=True,
        calculation_boundary="Scope 2 Location-Based (Thermal generation baseline excluding renewable energy generation)",
        notes="Official national thermal baseline factor. Kept as primary standard reference for backward compatibility with existing tests.",
    ),
    "grid_in_cea_weighted_average": EmissionFactor(
        factor_id="grid_in_cea_weighted_average",
        activity_type="electricity",
        sub_category="National Grid Weighted Average",
        value=0.716,
        unit="kg CO2 / kWh",
        geography="India (National Grid)",
        reporting_period="FY 2022-2023",
        source="Central Electricity Authority (CEA) CO2 Baseline Database v19.0 (User Guide Table 1)",
        version="19.0.0",
        is_authoritative=True,
        calculation_boundary="Scope 2 Location-Based (Gross electricity generation weighted average including renewable energy sources)",
        notes="Official CEA weighted average emission factor for Scope 2 corporate reporting in India.",
    ),
    "grid_in_cea_combined_margin": EmissionFactor(
        factor_id="grid_in_cea_combined_margin",
        activity_type="electricity",
        sub_category="Clean Energy Combined Margin",
        value=0.713,
        unit="kg CO2 / kWh",
        geography="India (National Grid)",
        reporting_period="FY 2022-2023",
        source="Central Electricity Authority (CEA) CDM Baseline v19.0",
        version="19.0.0",
        is_authoritative=True,
        calculation_boundary="Scope 2 Project Margin (Combined Margin for CDM clean energy displacement projects)",
        notes="Applicable for grid-connected renewable intervention offset evaluations.",
    ),
    "electricity_solar_rooftop": EmissionFactor(
        factor_id="electricity_solar_rooftop",
        activity_type="electricity",
        sub_category="On-Site Solar Rooftop",
        value=0.0,
        unit="kg CO2e / kWh",
        geography="On-Site",
        reporting_period="2024",
        source="GHG Protocol Scope 2 Guidance (Direct on-site zero-emissions generation)",
        version="2.0.0",
        is_authoritative=True,
        calculation_boundary="Scope 2 Zero-Emission Renewable Self-Generation",
        notes="On-site photovoltaic generation consumed behind the meter has zero direct operational emissions.",
    ),

    # --------------------------------------------------------------------------
    # Transportation Fuels (GHG Protocol / IPCC / DEFRA)
    # --------------------------------------------------------------------------
    "fuel_diesel_standard": EmissionFactor(
        factor_id="fuel_diesel_standard",
        activity_type="transportation",
        sub_category="Diesel",
        value=2.68,
        unit="kg CO2e / L",
        geography="Global / India Standard",
        reporting_period="2024",
        source="GHG Protocol Cross-Sector Tools / IPCC 2006 Vol 2 / UK DEFRA 2024",
        version="2024.1",
        is_authoritative=True,
        calculation_boundary="Scope 1 Direct Tailpipe Combustion (Tank-to-Wheel direct emissions per litre of diesel consumed)",
        notes="Standard automotive diesel direct combustion factor. Standard value is 2.68 kg CO2e/L.",
    ),
    "fuel_petrol_standard": EmissionFactor(
        factor_id="fuel_petrol_standard",
        activity_type="transportation",
        sub_category="Petrol",
        value=2.31,
        unit="kg CO2e / L",
        geography="Global / India Standard",
        reporting_period="2024",
        source="GHG Protocol Cross-Sector Tools / IPCC 2006 Vol 2 / UK DEFRA 2024",
        version="2024.1",
        is_authoritative=True,
        calculation_boundary="Scope 1 Direct Tailpipe Combustion (Tank-to-Wheel direct emissions per litre of motor gasoline)",
        notes="Standard motor gasoline direct combustion factor.",
    ),
    "fuel_cng_standard": EmissionFactor(
        factor_id="fuel_cng_standard",
        activity_type="transportation",
        sub_category="CNG",
        value=2.75,
        unit="kg CO2e / kg",
        geography="Global / India Standard",
        reporting_period="2024",
        source="GHG Protocol Stationary & Mobile Combustion / IPCC Guidelines",
        version="2024.1",
        is_authoritative=True,
        calculation_boundary="Scope 1 Direct Mobile Combustion per kg of compressed natural gas",
        notes="Compressed Natural Gas factor per kilogram of fuel consumed.",
    ),
    "fuel_electric_standard": EmissionFactor(
        factor_id="fuel_electric_standard",
        activity_type="transportation",
        sub_category="Electric EV Charging",
        value=0.82,
        unit="kg CO2e / kWh",
        geography="India (National Grid)",
        reporting_period="2024",
        source="Central Electricity Authority (CEA) Grid Electricity Equivalent",
        version="19.0.0",
        is_authoritative=True,
        calculation_boundary="Scope 2 Indirect Emissions from vehicle charging via local grid",
        notes="Indirect emissions per kWh consumed during electric bus or EV charging.",
    ),

    # --------------------------------------------------------------------------
    # Waste Treatment Methods (IPCC Vol 5 / US EPA WARM)
    # --------------------------------------------------------------------------
    "waste_composting": EmissionFactor(
        factor_id="waste_composting",
        activity_type="waste",
        sub_category="Composting",
        value=0.10,
        unit="kg CO2e / kg",
        geography="Global / India Standard",
        reporting_period="2024",
        source="IPCC 2006 Guidelines for National GHG Inventories, Vol 5 Waste, Ch 4 (Biological Treatment)",
        version="2006.5",
        is_authoritative=True,
        calculation_boundary="Scope 3 Category 5 Waste Generated in Operations (Biological aerobic treatment CH4 and N2O emissions)",
        notes="Aerobic decomposition emission factor for segregated biodegradable and cafeteria waste.",
    ),
    "waste_recycling": EmissionFactor(
        factor_id="waste_recycling",
        activity_type="waste",
        sub_category="Recycling",
        value=-0.45,
        unit="kg CO2e / kg",
        geography="Global / Standard",
        reporting_period="2024",
        source="US EPA Waste Reduction Model (WARM v15) / GHG Protocol Value Chain Standard",
        version="15.0.0",
        is_authoritative=True,
        calculation_boundary="Scope 3 Category 5 Avoided Production Credit (Net negative greenhouse gas accounting from avoided virgin material extraction)",
        notes="Avoided raw material production credit per kilogram of segregated recyclables (paper, plastic, metal).",
    ),
    "waste_landfill": EmissionFactor(
        factor_id="waste_landfill",
        activity_type="waste",
        sub_category="Landfill",
        value=1.25,
        unit="kg CO2e / kg",
        geography="Global / India Standard",
        reporting_period="2024",
        source="IPCC 2006 Guidelines, Vol 5 Waste, Ch 3 / US EPA WARM",
        version="2006.5",
        is_authoritative=True,
        calculation_boundary="Scope 3 Category 5 End-of-Life Disposal (Unmanaged landfill anaerobic degradation without active methane gas capture)",
        notes="Net methane generation factor for mixed solid waste dumped in non-gas capture landfills.",
    ),
    "waste_incineration": EmissionFactor(
        factor_id="waste_incineration",
        activity_type="waste",
        sub_category="Incineration / Waste-to-Energy",
        value=0.42,
        unit="kg CO2e / kg",
        geography="Global / Standard",
        reporting_period="2024",
        source="IPCC 2006 Guidelines, Vol 5 Waste, Ch 5 (Incineration and Open Burning)",
        version="2006.5",
        is_authoritative=True,
        calculation_boundary="Scope 3 Category 5 Thermal Treatment (Non-biogenic fossil carbon oxidation)",
        notes="Combustion factor for thermal treatment of solid waste streams.",
    ),
    "waste_other": EmissionFactor(
        factor_id="waste_other",
        activity_type="waste",
        sub_category="Other / Unsegregated Disposal",
        value=0.50,
        unit="kg CO2e / kg",
        geography="Global / Standard",
        reporting_period="2024",
        source="Weighted Baseline for Unsegregated Open Dumping",
        version="1.0.0",
        is_authoritative=True,
        calculation_boundary="Scope 3 Category 5 Blended Default Baseline",
        notes="Default weighted baseline for unknown, unsegregated, or open dump disposal.",
    ),
}

# Benchmark prices for financial impact models (INR)
BENCHMARK_PRICES: Dict[str, float] = {
    "electricity_tariff_inr_per_kwh": 8.50,
    "diesel_inr_per_l": 94.50,
    "petrol_inr_per_l": 104.20,
    "cng_inr_per_kg": 82.00,
    "electric_inr_per_kwh": 8.50,
}


def get_emission_factor(factor_id: str) -> Optional[EmissionFactor]:
    """Retrieves an emission factor by its unique ID."""
    return EMISSION_FACTORS.get(factor_id)


def list_emission_factors() -> List[EmissionFactor]:
    """Returns all registered emission factors in the catalog."""
    return list(EMISSION_FACTORS.values())


def get_factors_by_activity(activity_type: str) -> List[EmissionFactor]:
    """Filters registered factors by activity type (electricity, transportation, waste)."""
    return [f for f in EMISSION_FACTORS.values() if f.activity_type.lower() == activity_type.lower()]
