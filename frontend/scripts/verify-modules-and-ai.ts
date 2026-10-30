import {
  calculateElectricityEmissions,
  calculateElectricitySavingsScenario,
  calculateTransportationEmissions,
  calculateWasteEmissions,
  calculateWasteRecoveryRate,
  generateBusRouteOptimizations,
  EMISSION_FACTORS,
} from '../lib/calculations'
import { aiAdvisorsService } from '../services/ai-advisors.service'
import type {
  BusRoute,
  ElectricityRecord,
  TransportationRecord,
  WasteRecord,
} from '../types/sustainability'

let passed = 0
let total = 0

function assert(condition: boolean, testName: string, detail?: string) {
  total++
  if (condition) {
    console.log(`[PASS] ${testName}`)
    passed++
  } else {
    console.error(`[FAIL] ${testName}: ${detail || 'Assertion failed'}`)
    process.exitCode = 1
  }
}

async function runTests() {
  console.log('=== CARBONIQ MODULES & AI SUSTAINABILITY ADVISOR TEST SUITE ===\n')

  // TEST GROUP 1: Electricity Calculations
  console.log('--- TEST GROUP 1: Electricity Calculation Engine ---')
  const elecEmissions = calculateElectricityEmissions(1000)
  assert(elecEmissions === 820, '1000 kWh at 0.82 kg/kWh equals 820 kg CO2e')

  const scenario = calculateElectricitySavingsScenario(1240, 15)
  assert(scenario.kwhReduction === 186, '15% of 1240 kWh is 186 kWh')
  assert(scenario.costSavings === Math.round(186 * 8.5), 'Variable cost savings calculated at ₹8.5/kWh')
  assert(
    scenario.emissionsReduction === Number((186 * 0.82).toFixed(1)),
    'Emissions reduction is 186 * 0.82 = 152.5 kg CO2e'
  )

  // TEST GROUP 2: Transportation Calculations (No Double-Counting)
  console.log('\n--- TEST GROUP 2: Transportation & Fuel Calculations ---')
  const actualFuelResult = calculateTransportationEmissions({
    distanceKm: 500,
    fuelType: 'Diesel',
    fuelConsumedLiters: 100,
    fuelEfficiencyKmPerL: 5.0,
  })
  assert(
    actualFuelResult.method === 'actual_fuel',
    'Prioritizes actual fuel when fuelConsumedLiters is provided'
  )
  assert(actualFuelResult.emissionsKg === 268, '100L Diesel × 2.68 kg/L = 268 kg CO2e')

  const estFuelResult = calculateTransportationEmissions({
    distanceKm: 250,
    fuelType: 'Diesel',
    fuelEfficiencyKmPerL: 5.0,
  })
  assert(
    estFuelResult.method === 'distance_efficiency_estimate',
    'Uses distance ÷ efficiency when actual fuel is missing'
  )
  assert(estFuelResult.calculatedFuelLiters === 50, '250 km ÷ 5 km/L = 50 L')
  assert(estFuelResult.emissionsKg === 134, '50L Diesel × 2.68 kg/L = 134 kg CO2e')

  const uncalculatedResult = calculateTransportationEmissions({
    distanceKm: 250,
  })
  assert(
    uncalculatedResult.method === 'uncalculated',
    'Returns uncalculated status when required efficiency/fuel data is absent'
  )

  // TEST GROUP 3: Smart Bus Route Optimization Algorithm
  console.log('\n--- TEST GROUP 3: Smart Bus Route Optimization Engine ---')
  const testRoutes: BusRoute[] = [
    {
      id: 'rt-1',
      routeName: 'North 1',
      startLocation: 'Hebbal',
      destination: 'Campus Gate 1',
      intermediateStops: ['Jakkur'],
      distanceKm: 30,
      durationMinutes: 45,
      tripsPerDay: 2,
      operatingDaysPerWeek: 5,
      assignedStudents: 22,
      busId: 'BUS-1',
      fuelType: 'Diesel',
      fuelEfficiencyKmPerL: 5.0,
      seatingCapacity: 40,
      currentBusesCount: 1,
      status: 'active',
    },
    {
      id: 'rt-2',
      routeName: 'North 2',
      startLocation: 'Kogilu',
      destination: 'Campus Gate 1',
      intermediateStops: ['Jakkur'],
      distanceKm: 28,
      durationMinutes: 40,
      tripsPerDay: 2,
      operatingDaysPerWeek: 5,
      assignedStudents: 16,
      busId: 'BUS-2',
      fuelType: 'Diesel',
      fuelEfficiencyKmPerL: 5.0,
      seatingCapacity: 40,
      currentBusesCount: 1,
      status: 'active',
    },
  ]

  const proposals = generateBusRouteOptimizations(testRoutes)
  assert(proposals.length === 1, 'Identifies 1 feasible consolidation proposal')
  assert(proposals[0].capacityCheckPassed === true, 'Capacity check passes (22 + 16 = 38 <= 40 seats)')
  assert(proposals[0].estimatedDistanceReductionKm > 0, 'Distance reduction is positive')
  assert(proposals[0].estimatedFuelSavingsLiters > 0, 'Fuel savings are positive')
  assert(proposals[0].estimatedMonthlySavingsInr > 0, 'Monthly cost savings are calculated')
  assert(proposals[0].feasibility === 'High', 'Feasibility rated High due to shared stop')

  // TEST GROUP 4: Waste Calculations
  console.log('\n--- TEST GROUP 4: Waste Emissions & Recovery Calculations ---')
  const compostEmissions = calculateWasteEmissions(100, 'Composting')
  assert(compostEmissions === 10, '100 kg compost × 0.10 kg/kg = 10 kg CO2e')

  const recycleEmissions = calculateWasteEmissions(100, 'Recycling')
  assert(recycleEmissions === -45, '100 kg recycling × -0.45 kg/kg = -45 kg CO2e net avoided')

  const landfillEmissions = calculateWasteEmissions(100, 'Landfill')
  assert(landfillEmissions === 125, '100 kg landfill × 1.25 kg/kg = 125 kg CO2e')

  const recoveryRate = calculateWasteRecoveryRate(200, 500)
  assert(recoveryRate === 40, '200 kg recovered out of 500 kg total = 40%')

  // TEST GROUP 5: AI Sustainability Advisors
  console.log('\n--- TEST GROUP 5: AI Advisors Grounded In Data ---')
  const mockElecRecords: ElectricityRecord[] = [
    {
      id: 'e-1',
      reportingMonth: '2026-09',
      consumptionKwh: 1000,
      billAmountInr: 8500,
      buildingOrDepartment: 'Main',
      calculatedEmissionsKg: 820,
      emissionFactorUsed: 0.82,
      factorType: 'illustrative_grid_factor',
      createdAt: '2026-09-30T00:00:00.000Z',
    },
    {
      id: 'e-2',
      reportingMonth: '2026-10',
      consumptionKwh: 1200,
      billAmountInr: 10200,
      buildingOrDepartment: 'Main',
      calculatedEmissionsKg: 984,
      emissionFactorUsed: 0.82,
      factorType: 'illustrative_grid_factor',
      createdAt: '2026-10-31T00:00:00.000Z',
    },
  ]

  const elecReply = await aiAdvisorsService.queryElectricityAdvisor(
    'How much can I save by reducing electricity usage by 15%?',
    mockElecRecords
  )
  assert(
    elecReply.calculationBreakdown !== undefined,
    'Electricity advisor returns structured calculation breakdown'
  )
  assert(
    elecReply.content.includes('15% electricity reduction'),
    'Electricity advisor mentions 15% reduction target'
  )

  const elecPeakReply = await aiAdvisorsService.queryElectricityAdvisor(
    'Which month had the highest electricity consumption?',
    mockElecRecords
  )
  assert(
    elecPeakReply.content.includes('2026-10') && elecPeakReply.content.includes('1,200'),
    'Identifies 2026-10 as peak month with 1,200 kWh'
  )

  const transReply = await aiAdvisorsService.queryTransportationAdvisor(
    'Can any of my routes be combined?',
    [],
    testRoutes,
    proposals
  )
  assert(
    transReply.content.includes('Consolidate North 1 & North 2'),
    'Transport advisor identifies consolidation proposal'
  )

  const mockWasteRecords: WasteRecord[] = [
    {
      id: 'w-1',
      date: '2026-10-28',
      category: 'Recyclable',
      quantityKg: 100,
      treatmentMethod: 'Recycling',
      calculatedEmissionsKg: -45,
      status: 'Verified',
      createdAt: '2026-10-28T00:00:00.000Z',
    },
    {
      id: 'w-2',
      date: '2026-10-25',
      category: 'General',
      quantityKg: 100,
      treatmentMethod: 'Landfill',
      calculatedEmissionsKg: 125,
      status: 'Verified',
      createdAt: '2026-10-25T00:00:00.000Z',
    },
  ]

  const wasteReply = await aiAdvisorsService.queryWasteAdvisor(
    'How can we improve our recycling rate?',
    mockWasteRecords
  )
  assert(
    wasteReply.content.includes('50%'),
    'Waste advisor computes 50% recovery rate from records'
  )

  console.log(`\n========================================`)
  console.log(`TEST SUMMARY: ${passed}/${total} tests passed.`)
  console.log(`========================================\n`)
}

runTests().catch(console.error)
