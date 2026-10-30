import type {
  BusRoute,
  FuelType,
  RouteConfigSummary,
  RouteOptimizationProposal,
  SimulatorParams,
  SimulatorResults,
  TransportationMode,
  WasteTreatmentMethod,
} from '../types/sustainability'

/**
 * Standard Illustrative Emission Factors
 * Kept separate from UI components for clean future integration with FastAPI endpoints.
 * Units: kg CO2e per unit (kWh, Litre, kg).
 */
export const EMISSION_FACTORS = {
  // Electricity: Illustrative Indian CEA baseline grid average (~0.82 kg CO2e/kWh)
  electricityGrid: 0.82,

  // Transportation Fuel emission factors (kg CO2e per Litre / kg)
  fuels: {
    Diesel: 2.68,
    Petrol: 2.31,
    CNG: 2.75, // kg CO2e / kg
    Electric: 0.82, // mapped to grid per kWh equivalent
  } as Record<FuelType, number>,

  // Waste treatment net emission factors (kg CO2e per kg of waste)
  waste: {
    Composting: 0.10,
    Recycling: -0.45, // Net negative / avoided emissions benefit
    Landfill: 1.25, // Anaerobic decomposition factor
    Incineration: 0.42, // Thermal oxidation factor
    'Other / Unknown': 0.50,
  } as Record<WasteTreatmentMethod, number>,
}

export const BENCHMARK_PRICES = {
  electricityTariffInr: 8.5, // Estimated variable tariff ₹/kWh
  fuelInr: {
    Diesel: 94.5,
    Petrol: 104.2,
    CNG: 82.0,
    Electric: 8.5,
  } as Record<FuelType, number>,
}

/**
 * Calculates electricity emissions from consumption in kWh.
 * Formula: Emissions (kg CO2e) = consumption (kWh) × emission factor (kg CO2e/kWh)
 */
export function calculateElectricityEmissions(
  consumptionKwh: number,
  factor: number = EMISSION_FACTORS.electricityGrid
): number {
  if (consumptionKwh <= 0) return 0
  return Number((consumptionKwh * factor).toFixed(1))
}

/**
 * Calculates what-if savings for electricity reduction scenarios.
 */
export function calculateElectricitySavingsScenario(
  currentKwh: number,
  percentReduction: number,
  tariff: number = BENCHMARK_PRICES.electricityTariffInr
) {
  const kwhReduction = Number(((currentKwh * percentReduction) / 100).toFixed(1))
  const costSavings = Math.round(kwhReduction * tariff)
  const emissionsReduction = Number(
    (kwhReduction * EMISSION_FACTORS.electricityGrid).toFixed(1)
  )

  return {
    kwhReduction,
    costSavings,
    emissionsReduction,
    assumptions: [
      `Illustrative grid emission factor: ${EMISSION_FACTORS.electricityGrid} kg CO₂e/kWh`,
      `Estimated variable electricity tariff: ₹${tariff}/kWh (excluding fixed meter and demand charges)`,
    ],
  }
}

/**
 * Calculates transportation emissions with strict separation between
 * the actual-fuel method and distance-efficiency estimate.
 * Never calculates twice for the same activity.
 */
export interface TransportCalculationResult {
  emissionsKg: number
  calculatedFuelLiters: number
  method: 'actual_fuel' | 'distance_efficiency_estimate' | 'uncalculated'
  factorUsed: number
  explanation: string
}

export function calculateTransportationEmissions(params: {
  distanceKm: number
  fuelType?: FuelType
  fuelConsumedLiters?: number
  fuelEfficiencyKmPerL?: number
}): TransportCalculationResult {
  const fuelType = params.fuelType || 'Diesel'
  const factor = EMISSION_FACTORS.fuels[fuelType] || EMISSION_FACTORS.fuels.Diesel

  // Method 1: Actual fuel consumed is known
  if (params.fuelConsumedLiters !== undefined && params.fuelConsumedLiters > 0) {
    const emissions = Number((params.fuelConsumedLiters * factor).toFixed(1))
    return {
      emissionsKg: emissions,
      calculatedFuelLiters: params.fuelConsumedLiters,
      method: 'actual_fuel',
      factorUsed: factor,
      explanation: `Calculated from ${params.fuelConsumedLiters}L of actual ${fuelType} consumed × ${factor} kg CO₂e/L.`,
    }
  }

  // Method 2: Distance and fuel efficiency known
  if (
    params.distanceKm > 0 &&
    params.fuelEfficiencyKmPerL !== undefined &&
    params.fuelEfficiencyKmPerL > 0
  ) {
    const estimatedFuel = Number((params.distanceKm / params.fuelEfficiencyKmPerL).toFixed(2))
    const emissions = Number((estimatedFuel * factor).toFixed(1))
    return {
      emissionsKg: emissions,
      calculatedFuelLiters: estimatedFuel,
      method: 'distance_efficiency_estimate',
      factorUsed: factor,
      explanation: `Estimated from ${params.distanceKm} km ÷ ${params.fuelEfficiencyKmPerL} km/L = ${estimatedFuel}L ${fuelType} × ${factor} kg CO₂e/L.`,
    }
  }

  // Missing data: cannot calculate reliably
  return {
    emissionsKg: 0,
    calculatedFuelLiters: 0,
    method: 'uncalculated',
    factorUsed: factor,
    explanation:
      'Insufficient fuel or efficiency data. Enter actual litres or both distance and km/L efficiency.',
  }
}

/**
 * Calculates waste treatment emissions.
 * Formula: Emissions (kg CO2e) = quantity (kg) × treatment emission factor (kg CO2e/kg)
 */
export function calculateWasteEmissions(
  quantityKg: number,
  treatmentMethod?: WasteTreatmentMethod
): number {
  if (quantityKg <= 0) return 0
  const method = treatmentMethod || 'Other / Unknown'
  const factor = EMISSION_FACTORS.waste[method] || EMISSION_FACTORS.waste['Other / Unknown']
  return Number((quantityKg * factor).toFixed(1))
}

/**
 * Evaluates candidate bus routes for consolidation opportunities.
 * Considers student counts, bus capacities, distance, and realistic detour modeling.
 */
export function generateBusRouteOptimizations(routes: BusRoute[]): RouteOptimizationProposal[] {
  const proposals: RouteOptimizationProposal[] = []
  if (routes.length < 2) return proposals

  // Filter routes that share destinations (e.g., Main Campus)
  for (let i = 0; i < routes.length; i++) {
    for (let j = i + 1; j < routes.length; j++) {
      const rA = routes[i]
      const rB = routes[j]

      // Check if both serve the same destination or have overlapping intermediate stops
      const sameDestination =
        rA.destination.trim().toLowerCase() === rB.destination.trim().toLowerCase()
      const sharedStops = rA.intermediateStops.filter((stop) =>
        rB.intermediateStops.some((s) => s.toLowerCase() === stop.toLowerCase())
      )

      if (sameDestination || sharedStops.length > 0) {
        const totalStudents = rA.assignedStudents + rB.assignedStudents
        const maxBusCapacity = Math.max(rA.seatingCapacity, rB.seatingCapacity)
        const capacityCheckPassed = totalStudents <= maxBusCapacity

        // Only propose consolidation if combined students do not exceed max capacity
        if (capacityCheckPassed) {
          const combinedDistanceKm = Math.round(
            Math.max(rA.distanceKm, rB.distanceKm) * 1.15 + (sharedStops.length > 0 ? 3 : 6)
          )
          const currentTotalDistance = rA.distanceKm + rB.distanceKm
          const distanceReduction = Math.max(0, currentTotalDistance - combinedDistanceKm)

          const avgEfficiency = (rA.fuelEfficiencyKmPerL + rB.fuelEfficiencyKmPerL) / 2
          const currentDailyFuel = Number(
            (
              (rA.distanceKm * rA.tripsPerDay) / rA.fuelEfficiencyKmPerL +
              (rB.distanceKm * rB.tripsPerDay) / rB.fuelEfficiencyKmPerL
            ).toFixed(1)
          )
          const proposedDailyFuel = Number(
            ((combinedDistanceKm * Math.max(rA.tripsPerDay, rB.tripsPerDay)) / avgEfficiency).toFixed(1)
          )
          const dailyFuelSavings = Math.max(0, Number((currentDailyFuel - proposedDailyFuel).toFixed(1)))

          const operatingDaysPerMonth = 22
          const monthlyFuelSavings = Math.round(dailyFuelSavings * operatingDaysPerMonth)
          const dieselPrice = BENCHMARK_PRICES.fuelInr.Diesel
          const monthlyCostSavings = Math.round(monthlyFuelSavings * dieselPrice)
          const emissionsFactor = EMISSION_FACTORS.fuels.Diesel
          const monthlyEmissionsSavings = Math.round(monthlyFuelSavings * emissionsFactor)

          const currentConfig: RouteConfigSummary = {
            routeIds: [rA.id, rB.id],
            routeNames: [rA.routeName, rB.routeName],
            busesCount: rA.currentBusesCount + rB.currentBusesCount,
            studentsServed: totalStudents,
            totalDistanceKm: currentTotalDistance,
            dailyFuelConsumptionLiters: currentDailyFuel,
            monthlyFuelCostInr: Math.round(currentDailyFuel * operatingDaysPerMonth * dieselPrice),
            monthlyEmissionsKg: Math.round(currentDailyFuel * operatingDaysPerMonth * emissionsFactor),
          }

          const proposedConfig: RouteConfigSummary = {
            routeIds: [`${rA.id}-${rB.id}-combined`],
            routeNames: [`Consolidated ${rA.routeName} + ${rB.routeName}`],
            busesCount: 1, // 1 consolidated high-capacity bus
            studentsServed: totalStudents,
            totalDistanceKm: combinedDistanceKm,
            dailyFuelConsumptionLiters: proposedDailyFuel,
            monthlyFuelCostInr: Math.round(proposedDailyFuel * operatingDaysPerMonth * dieselPrice),
            monthlyEmissionsKg: Math.round(proposedDailyFuel * operatingDaysPerMonth * emissionsFactor),
          }

          proposals.push({
            id: `opt-${rA.id}-${rB.id}`,
            title: `Consolidate ${rA.routeName} & ${rB.routeName}`,
            summary: `Merge Route ${rA.routeName} (${rA.assignedStudents} students) and ${rB.routeName} (${rB.assignedStudents} students) into a single 40-seater route serving shared stops.`,
            reason: `Both routes travel to ${rA.destination} with overlapping corridors. Combined passenger load (${totalStudents} students) is within the ${maxBusCapacity}-seat capacity limit.`,
            capacityCheckPassed: true,
            currentConfig,
            proposedConfig,
            estimatedDistanceReductionKm: distanceReduction,
            estimatedFuelSavingsLiters: monthlyFuelSavings,
            estimatedMonthlySavingsInr: monthlyCostSavings,
            estimatedEmissionsReductionKg: monthlyEmissionsSavings,
            feasibility: sharedStops.length > 0 ? 'High' : 'Medium',
            requiredValidation: [
              'Verify morning pickup times and shift schedules between both stops',
              'Check whether road turning radius permits 40-seater bus on intermediate residential sectors',
              'Confirm student boarding punctuality before finalizing combined schedule',
            ],
            status: 'pending',
          })
        }
      }
    }
  }

  return proposals
}

/**
 * Calculates what-if projection metrics for the savings simulator.
 */
export function calculateSavingsProjection({
  electricityReduction,
  transportReduction,
  wasteReduction,
}: SimulatorParams): SimulatorResults {
  const savingsMonthly = Math.round(
    (6800 * (electricityReduction * 0.5 + transportReduction * 0.3 + wasteReduction * 0.2)) / 100
  )
  const emissionsImprovementPercent = Math.round(
    (electricityReduction * 0.46 + transportReduction * 0.31 + wasteReduction * 0.14) / 3
  )
  const baselineEmissions = 2480
  const proposedEmissions =
    baselineEmissions - Math.round((baselineEmissions * emissionsImprovementPercent) / 100)
  const projectedKwhReduction = Math.round((1240 * electricityReduction) / 100)
  const projectedWasteReduction = Math.round((420 * wasteReduction) / 100)

  return {
    savingsMonthly,
    emissionsImprovementPercent,
    proposedEmissions,
    projectedKwhReduction,
    projectedWasteReduction,
  }
}

/**
 * Calculates waste recovery rate percentage.
 */
export function calculateWasteRecoveryRate(recycled: number, totalGenerated: number): number {
  if (totalGenerated <= 0) return 0
  return Math.round((recycled / totalGenerated) * 100)
}

/**
 * Formats currency values in Indian Rupees (INR).
 */
export function formatCurrencyINR(amount: number): string {
  return `₹${amount.toLocaleString('en-IN')}`
}
