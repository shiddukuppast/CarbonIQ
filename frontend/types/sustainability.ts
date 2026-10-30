export interface MonthlyEmission {
  month: string
  value: number
}

export interface ResourceBreakdown {
  name: string
  value: number
  color: string
}

export interface ElectricityData {
  month: string
  usage: number
  cost: number
}

export interface WasteData {
  month: string
  generated: number
  recycled: number
}

export interface Recommendation {
  id: string
  title: string
  category: 'Electricity' | 'Transport' | 'Waste'
  impact: 'High' | 'Medium' | 'Quick win' | 'Low'
  savingsMonthly: string
  difficulty: 'High' | 'Medium' | 'Low effort'
}

export interface SimulatorParams {
  electricityReduction: number
  transportReduction: number
  wasteReduction: number
}

export interface SimulatorResults {
  savingsMonthly: number
  emissionsImprovementPercent: number
  proposedEmissions: number
  projectedKwhReduction: number
  projectedWasteReduction: number
}

/**
 * Electricity Record model
 */
export interface ElectricityRecord {
  id: string
  reportingMonth: string // YYYY-MM
  consumptionKwh: number
  source?: string
  billAmountInr?: number
  buildingOrDepartment?: string
  notes?: string
  calculatedEmissionsKg: number
  emissionFactorUsed: number // kg CO2e / kWh
  factorType: string
  factorSource?: string
  factorVersion?: string
  calculationBoundary?: string
  createdAt: string
}

/**
 * Transportation Record model
 */
export type TransportationMode = 'Bus' | 'Fleet Van' | 'Car' | 'Two-Wheeler' | 'Public Transit'
export type FuelType = 'Diesel' | 'Petrol' | 'CNG' | 'Electric'

export interface TransportationRecord {
  id: string
  date: string // YYYY-MM-DD or YYYY-MM
  mode: TransportationMode
  distanceKm: number
  fuelType?: FuelType
  fuelConsumedLiters?: number
  fuelEfficiencyKmPerL?: number
  fuelExpenditureInr?: number
  vehicleId?: string
  passengerCount?: number
  vehicleCapacity?: number
  routeName?: string
  pickupLocations?: string[]
  destination?: string
  notes?: string
  calculationMethod: 'actual_fuel' | 'distance_efficiency_estimate' | 'uncalculated'
  calculatedEmissionsKg: number
  factorSource?: string
  factorVersion?: string
  calculationBoundary?: string
  createdAt: string
}

/**
 * Bus Route model for Smart Bus Route Optimization
 */
export interface BusRoute {
  id: string
  routeName: string
  startLocation: string
  destination: string
  intermediateStops: string[]
  distanceKm: number
  durationMinutes: number
  tripsPerDay: number
  operatingDaysPerWeek: number
  assignedStudents: number
  busId: string
  fuelType: 'Diesel' | 'CNG' | 'Electric'
  fuelEfficiencyKmPerL: number
  fuelConsumptionPerDayLiters?: number
  seatingCapacity: number
  currentBusesCount: number
  status: 'active' | 'consolidated' | 'under_review'
  notes?: string
}

/**
 * AI Route Optimization Proposal
 */
export interface RouteConfigSummary {
  routeIds: string[]
  routeNames: string[]
  busesCount: number
  studentsServed: number
  totalDistanceKm: number
  dailyFuelConsumptionLiters: number
  monthlyFuelCostInr: number
  monthlyEmissionsKg: number
}

export interface RouteOptimizationProposal {
  id: string
  title: string
  summary: string
  reason: string
  capacityCheckPassed: boolean
  currentConfig: RouteConfigSummary
  proposedConfig: RouteConfigSummary
  estimatedDistanceReductionKm: number
  estimatedFuelSavingsLiters: number
  estimatedMonthlySavingsInr: number
  estimatedEmissionsReductionKg: number
  feasibility: 'High' | 'Medium' | 'Needs Validation'
  requiredValidation: string[]
  status: 'pending' | 'accepted' | 'rejected'
}

/**
 * Waste Record model
 */
export type WasteCategory = 'Biodegradable' | 'Recyclable' | 'General' | 'E-waste'
export type WasteTreatmentMethod = 'Composting' | 'Recycling' | 'Landfill' | 'Incineration' | 'Other / Unknown'

export interface WasteRecord {
  id: string
  date: string // YYYY-MM-DD or YYYY-MM
  category: WasteCategory
  quantityKg: number
  unit?: string
  treatmentMethod?: WasteTreatmentMethod
  buildingOrDepartment?: string
  collectionProvider?: string
  disposalCostInr?: number
  notes?: string
  calculatedEmissionsKg: number
  emissionFactorUsed?: number
  factorSource?: string
  factorVersion?: string
  calculationBoundary?: string
  status: 'Verified' | 'Estimated' | 'Pending'
  createdAt: string
}

export interface MetricItem {
  label: string
  value: string | number
  unit?: string
  subtext?: string
  trend?: 'up' | 'down' | 'neutral'
}

export interface KeyFindingItem {
  title?: string
  description: string
  category?: string
}

export interface RecommendationItem {
  title: string
  explanation?: string
  priority?: 'High' | 'Medium' | 'Low' | string
  expected_benefit?: string
  impact?: string
  category?: string
  action_url?: string
  action_label?: string
}

export interface StructuredAiPayload {
  intent?: 'direct' | 'comparative' | 'recommendation' | 'analytical' | 'comprehensive' | string
  direct_answer: string
  explanation?: string
  reporting_period?: string
  metrics?: MetricItem[]
  key_findings?: KeyFindingItem[]
  recommendations?: RecommendationItem[]
  data_limitations?: string[]
  confidence_score?: string | number
}

/**
 * AI Advisor Chat Message model
 */
export interface AiChatMessage {
  id: string
  role: 'user' | 'assistant'
  content: string
  timestamp: string
  calculationBreakdown?: {
    formula: string
    inputs: Record<string, string | number>
    assumptions?: string[]
    result: string
  }
  suggestedFollowUps?: string[]
  structuredPayload?: StructuredAiPayload
}
