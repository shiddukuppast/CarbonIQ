import type React from 'react'

export type DashboardView =
  | 'overview'
  | 'electricity'
  | 'transportation'
  | 'waste'
  | 'insights'
  | 'simulator'
  | 'progress'
  | 'reports'
  | 'settings'

export interface NavItem {
  id: DashboardView
  label: string
  href: string
  icon: React.ElementType
}

export type Tone = 'green' | 'olive' | 'sage' | 'amber'

export interface MetricCardProps {
  icon: React.ElementType
  label: string
  value: string
  unit?: string
  trend?: React.ReactNode
  tone?: Tone
  note?: string
}

export interface ActivityRecord {
  id: string
  date: string
  category: 'Electricity' | 'Transportation' | 'Waste' | string
  activity: string
  quantity: string
  status: 'Verified' | 'Reviewed' | 'Pending'
}
