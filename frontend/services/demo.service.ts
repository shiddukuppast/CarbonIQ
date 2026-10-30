import {
  DEFAULT_ELECTRICITY_DATA,
  DEFAULT_MONTHLY_EMISSIONS,
  DEFAULT_RECOMMENDATIONS,
  DEFAULT_RESOURCE_BREAKDOWN,
  DEFAULT_WASTE_DATA,
} from '../lib/constants'
import type { ActivityRecord } from '../types/dashboard'
import type {
  ElectricityData,
  MonthlyEmission,
  Recommendation,
  ResourceBreakdown,
  WasteData,
} from '../types/sustainability'

export const INITIAL_ACTIVITY_RECORDS: ActivityRecord[] = [
  {
    id: 'act-1',
    date: 'Oct 28, 2026',
    category: 'Electricity',
    activity: 'Monthly meter reading',
    quantity: '1,240 kWh',
    status: 'Verified',
  },
  {
    id: 'act-2',
    date: 'Oct 25, 2026',
    category: 'Transportation',
    activity: 'Route fuel log',
    quantity: '148 L',
    status: 'Reviewed',
  },
  {
    id: 'act-3',
    date: 'Oct 21, 2026',
    category: 'Waste',
    activity: 'Recycling collection',
    quantity: '218 kg',
    status: 'Reviewed',
  },
  {
    id: 'act-4',
    date: 'Oct 16, 2026',
    category: 'Electricity',
    activity: 'Office lighting check',
    quantity: '86 kWh',
    status: 'Verified',
  },
]

export const demoService = {
  getMonthlyEmissions(): MonthlyEmission[] {
    return [...DEFAULT_MONTHLY_EMISSIONS]
  },

  getResourceBreakdown(): ResourceBreakdown[] {
    return [...DEFAULT_RESOURCE_BREAKDOWN]
  },

  getElectricityHistory(): ElectricityData[] {
    return [...DEFAULT_ELECTRICITY_DATA]
  },

  getWasteHistory(): WasteData[] {
    return [...DEFAULT_WASTE_DATA]
  },

  getRecommendations(): Recommendation[] {
    return [...DEFAULT_RECOMMENDATIONS]
  },

  getRecentActivities(): ActivityRecord[] {
    return [...INITIAL_ACTIVITY_RECORDS]
  },

  getAiAnswer(question: string): string {
    const q = question.toLowerCase()
    if (q.includes('electric') || q.includes('energy') || q.includes('power')) {
      return 'Electricity is currently your largest contributor at 46% of estimated emissions. Start with lighting and HVAC schedules for the clearest near-term opportunity.'
    }
    if (q.includes('recycl') || q.includes('waste') || q.includes('trash')) {
      return 'Your current recovery rate is 52%. Source separation stations and clearer signage could improve recycling quality.'
    }
    return 'Transport contributes 31% of estimated emissions. Consolidating two low-use routes is the strongest modeled opportunity in this demo.'
  },
}
