import {
  BarChart3,
  BrainCircuit,
  BusFront,
  FileText,
  Recycle,
  Target,
  Zap,
} from 'lucide-react'
import type { NavItem } from '../types/dashboard'
import type {
  ElectricityData,
  MonthlyEmission,
  Recommendation,
  ResourceBreakdown,
  WasteData,
} from '../types/sustainability'

export const COLOR_GREEN = '#285943'
export const COLOR_MINT = '#A8C3A0'
export const COLOR_OLIVE = '#B6B86B'

export const DEFAULT_MONTHLY_EMISSIONS: MonthlyEmission[] = [
  { month: 'May', value: 2080 },
  { month: 'Jun', value: 2240 },
  { month: 'Jul', value: 2160 },
  { month: 'Aug', value: 2380 },
  { month: 'Sep', value: 2520 },
  { month: 'Oct', value: 2480 },
]

export const DEFAULT_RESOURCE_BREAKDOWN: ResourceBreakdown[] = [
  { name: 'Electricity', value: 46, color: COLOR_GREEN },
  { name: 'Transport', value: 31, color: '#8DAE83' },
  { name: 'Waste', value: 14, color: COLOR_OLIVE },
  { name: 'Other', value: 9, color: '#D6DED2' },
]

export const DEFAULT_ELECTRICITY_DATA: ElectricityData[] = [
  { month: 'May', usage: 980, cost: 9700 },
  { month: 'Jun', usage: 1080, cost: 11000 },
  { month: 'Jul', usage: 1020, cost: 10400 },
  { month: 'Aug', usage: 1160, cost: 12100 },
  { month: 'Sep', usage: 1190, cost: 13700 },
  { month: 'Oct', usage: 1240, cost: 14500 },
]

export const DEFAULT_WASTE_DATA: WasteData[] = [
  { month: 'May', generated: 320, recycled: 108 },
  { month: 'Jun', generated: 350, recycled: 132 },
  { month: 'Jul', generated: 340, recycled: 148 },
  { month: 'Aug', generated: 390, recycled: 171 },
  { month: 'Sep', generated: 410, recycled: 195 },
  { month: 'Oct', generated: 420, recycled: 218 },
]

export const DASHBOARD_NAV_ITEMS: NavItem[] = [
  { id: 'overview', label: 'Overview', href: '/dashboard', icon: BarChart3 },
  { id: 'electricity', label: 'Electricity', href: '/dashboard/electricity', icon: Zap },
  { id: 'transportation', label: 'Transportation', href: '/dashboard/transportation', icon: BusFront },
  { id: 'waste', label: 'Waste management', href: '/dashboard/waste', icon: Recycle },
  { id: 'insights', label: 'AI insights', href: '/dashboard/insights', icon: BrainCircuit },
  { id: 'simulator', label: 'Savings simulator', href: '/dashboard/simulator', icon: Target },
  { id: 'reports', label: 'Reports & exports', href: '/dashboard/reports', icon: FileText },
]

export const DEFAULT_RECOMMENDATIONS: Recommendation[] = [
  {
    id: 'rec-1',
    title: 'Switch to LED lighting in common areas',
    category: 'Electricity',
    impact: 'High',
    savingsMonthly: '₹2,140/mo',
    difficulty: 'High',
  },
  {
    id: 'rec-2',
    title: 'Consolidate two low-use transport routes',
    category: 'Transport',
    impact: 'Medium',
    savingsMonthly: '₹1,680/mo',
    difficulty: 'Medium',
  },
  {
    id: 'rec-3',
    title: 'Add source separation stations',
    category: 'Waste',
    impact: 'Quick win',
    savingsMonthly: '₹820/mo',
    difficulty: 'Low effort',
  },
]
