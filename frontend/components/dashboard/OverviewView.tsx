'use client'

import React, { useCallback, useEffect, useState } from 'react'
import { useRouter } from 'next/navigation'
import {
  ArrowRight,
  BusFront,
  CircleHelp,
  Cloud,
  Layers,
  MoreHorizontal,
  Package,
  Recycle,
  Sparkles,
  Target,
  Truck,
  Wallet,
  Zap,
} from 'lucide-react'
import { EmissionsLineChart } from '@/components/charts/EmissionsLineChart'
import { ResourceBreakdownChart } from '@/components/charts/ResourceBreakdownChart'
import { Button } from '@/components/ui/button'
import { Card } from '@/components/ui/Card'
import { Metric } from '@/components/ui/Metric'
import { MiniSpark } from '@/components/ui/MiniSpark'
import { Pill } from '@/components/ui/Pill'
import { useAuth } from '@/context/auth-context'
import { apiClient } from '@/services/api-client'

interface DashboardSummaryData {
  workspace_id: string
  workspace_name: string
  total_emissions_kg: number
  electricity: {
    total_kwh: number
    emissions_kg: number
    cost_inr: number
    record_count: number
  }
  transportation: {
    total_liters: number
    emissions_kg: number
    cost_inr: number
    total_distance_km?: number
    record_count: number
  }
  waste: {
    total_weight_kg: number
    emissions_kg: number
    recovery_rate_pct: number
    record_count: number
  }
  monthly_emissions_trend: Array<{ month: string; value: number }>
  category_breakdown: Array<{ name: string; value: number; color: string; emissions_kg?: number }>
  active_interventions_count: number
}

interface RecentActivityItem {
  id: string
  category: 'Electricity' | 'Transportation' | 'Waste'
  activity: string
  quantity: string
  date: string
  status: string
}

export function OverviewView() {
  const router = useRouter()
  const { session, user, token } = useAuth()
  const isAuth = Boolean(session.isAuthenticated && token)

  const [summary, setSummary] = useState<DashboardSummaryData | null>(null)
  const [activities, setActivities] = useState<RecentActivityItem[]>([])
  const [isLoading, setIsLoading] = useState(false)
  const [trendForecast, setTrendForecast] = useState<{
    points: any[]
    status: string
    modelMetrics?: any
    message?: string
  } | null>(null)

  const fetchSummary = useCallback(async () => {
    if (!isAuth || !token) return
    setIsLoading(true)
    try {
      const data = await apiClient.get<DashboardSummaryData>('/dashboard/summary', { token })
      setSummary(data)

      // Fetch recent records and ML emissions trend forecast concurrently
      const [elecRes, transRes, wasteRes, trendRes] = await Promise.allSettled([
        apiClient.get<any[]>('/electricity', { token }),
        apiClient.get<any[]>('/transportation', { token }),
        apiClient.get<any[]>('/waste', { token }),
        apiClient.get<any>('/emissions/trend?horizon=3', { token }),
      ])

      if (trendRes.status === 'fulfilled' && trendRes.value) {
        const val = trendRes.value
        if (val.status === 'ready' && Array.isArray(val.combined_series) && val.combined_series.length > 0) {
          setTrendForecast({
            points: val.combined_series,
            status: val.status,
            modelMetrics: val.model_metrics || val.model_info?.evaluation_metrics,
            message: val.message,
          })
        } else if (Array.isArray(val.historical_series) && val.historical_series.length > 0) {
          setTrendForecast({
            points: val.historical_series,
            status: val.status,
            modelMetrics: val.model_metrics || val.model_info?.evaluation_metrics,
            message: val.message,
          })
        }
      }

      const acts: RecentActivityItem[] = []

      if (elecRes.status === 'fulfilled' && Array.isArray(elecRes.value)) {
        elecRes.value.slice(-2).reverse().forEach((r: any) => {
          acts.push({
            id: r.id,
            category: 'Electricity',
            activity: `${r.building_or_department || 'Facility'} meter log`,
            quantity: `${Number(r.consumption_kwh).toLocaleString()} kWh`,
            date: r.reporting_month || 'Recent',
            status: 'Verified',
          })
        })
      }

      if (transRes.status === 'fulfilled' && Array.isArray(transRes.value)) {
        transRes.value.slice(-2).reverse().forEach((r: any) => {
          acts.push({
            id: r.id,
            category: 'Transportation',
            activity: r.route_name ? `Route ${r.route_name}` : `${r.mode || 'Fleet'} trip`,
            quantity: `${Number(r.distance_km).toLocaleString()} km`,
            date: r.date || 'Recent',
            status: 'Verified',
          })
        })
      }

      if (wasteRes.status === 'fulfilled' && Array.isArray(wasteRes.value)) {
        wasteRes.value.slice(-2).reverse().forEach((r: any) => {
          acts.push({
            id: r.id,
            category: 'Waste',
            activity: `${r.category || 'General'} disposal (${r.treatment_method || 'Disposal'})`,
            quantity: `${Number(r.quantity_kg).toLocaleString()} kg`,
            date: r.date || 'Recent',
            status: 'Verified',
          })
        })
      }

      setActivities(acts)
    } catch (err: any) {
      console.error('Failed to load dashboard summary:', err)
    } finally {
      setIsLoading(false)
    }
  }, [isAuth])

  useEffect(() => {
    if (isAuth) {
      fetchSummary()
    } else {
      setSummary(null)
      setActivities([])
    }
  }, [isAuth, fetchSummary])

  const totalEmissions = summary ? summary.total_emissions_kg : 0
  const electricityKwh = summary ? summary.electricity.total_kwh : 0
  const transportCost = summary ? summary.transportation.cost_inr : 0
  const wasteGenerated = summary ? summary.waste.total_weight_kg : 0
  const wasteRecoveryRate = summary ? summary.waste.recovery_rate_pct : 0
  const activeInterventions = summary ? summary.active_interventions_count : 0

  const totalRecordCount = summary
    ? summary.electricity.record_count +
      summary.transportation.record_count +
      summary.waste.record_count
    : 0

  const trendData = summary?.monthly_emissions_trend || []
  const chartData = trendForecast?.points && trendForecast.points.length > 0
    ? trendForecast.points
    : trendData
  const breakdownData = summary?.category_breakdown || []

  // Modeled savings: ~15% potential based on actual measured emissions
  const potentialMonthlySavingsInr = totalEmissions > 0 ? Math.round(totalEmissions * 0.15 * 8.5) : 0
  const goalProgressPercent = totalRecordCount > 0 ? (activeInterventions > 0 ? Math.min(100, activeInterventions * 25) : 10) : 0

  return (
    <div className="space-y-6">
      {/* Banner */}
      <div className="rounded-2xl bg-[#285943] px-5 py-5 text-white sm:px-7 sm:py-6 shadow-xs">
        <div className="flex flex-col justify-between gap-5 sm:flex-row sm:items-center">
          <div>
            <p className="text-xs font-medium text-[#B9D0B3]">
              {isAuth ? `${user.workspaceName.toUpperCase()} · ${user.accountType.toUpperCase()} WORKSPACE` : 'OCTOBER 2026 · DEMO WORKSPACE'}
            </p>
            <h1 className="mt-2 text-2xl font-semibold tracking-[-.04em] sm:text-3xl">
              Your impact, at a glance.
            </h1>
            <p className="mt-2 max-w-[510px] text-sm leading-6 text-white/65">
              Authoritative emissions calculations based strictly on your workspace&apos;s verified activity records.
            </p>
          </div>
          <div className="flex shrink-0 items-center gap-3 rounded-xl bg-white/10 p-3">
            <span className="grid h-9 w-9 place-items-center rounded-lg bg-[#9DBB99]/20 text-[#C7DFC0]">
              <Target size={18} />
            </span>
            <div>
              <p className="text-[10px] text-white/55">Active interventions</p>
              <p className="mt-1 text-xl font-semibold">
                {activeInterventions} <span className="text-xs font-normal text-white/55">in progress</span>
              </p>
            </div>
          </div>
        </div>
      </div>

      {isAuth && totalRecordCount === 0 && (
        <Card className="border border-[#DCE4DA] bg-[#F7FAF5] p-5">
          <div className="flex flex-col sm:flex-row items-start sm:items-center justify-between gap-4">
            <div className="flex items-center gap-3">
              <span className="grid h-10 w-10 shrink-0 place-items-center rounded-xl bg-[#285943] text-white">
                <Sparkles size={18} />
              </span>
              <div>
                <h2 className="text-sm font-semibold text-[#285943]">Welcome to your new workspace!</h2>
                <p className="text-xs text-[#5D6F62]">
                  No consumption logs recorded yet. Add your first electricity, travel, or waste entries to see live calculations.
                </p>
              </div>
            </div>
            <div className="flex gap-2">
              <Button className="px-3 py-1.5 text-xs" onClick={() => router.push('/dashboard/electricity')}>
                Add electricity
              </Button>
              <Button className="px-3 py-1.5 text-xs" variant="secondary" onClick={() => router.push('/dashboard/waste')}>
                Add waste
              </Button>
            </div>
          </div>
        </Card>
      )}

      {/* Metrics Row */}
      <div className="grid gap-4 sm:grid-cols-2 xl:grid-cols-3">
        <Metric
          icon={Cloud}
          label="Estimated carbon emissions"
          value={totalRecordCount > 0 ? Math.round(totalEmissions).toLocaleString() : '0'}
          unit="kg CO₂e"
          trend={<MiniSpark up={totalEmissions > 0} />}
          note={totalRecordCount > 0 ? `Calculated from ${totalRecordCount} workspace records` : 'No records logged yet'}
          tone="green"
        />
        <Metric
          icon={Zap}
          label="Electricity consumption"
          value={totalRecordCount > 0 ? Math.round(electricityKwh).toLocaleString() : '0'}
          unit="kWh"
          trend={<MiniSpark up={electricityKwh > 0} />}
          note={`${summary?.electricity.record_count || 0} electricity periods recorded`}
          tone="olive"
        />
        <Metric
          icon={Truck}
          label="Transport & fuel cost"
          value={transportCost > 0 ? `₹${Math.round(transportCost).toLocaleString('en-IN')}` : '₹0'}
          trend={<MiniSpark />}
          note={`${summary?.transportation.record_count || 0} fleet trips recorded`}
          tone="sage"
        />
        <Metric
          icon={Package}
          label="Total waste generated"
          value={wasteGenerated > 0 ? Math.round(wasteGenerated).toLocaleString() : '0'}
          unit="kg"
          trend={<MiniSpark />}
          note={`${wasteRecoveryRate}% recovery rate`}
          tone="amber"
        />
        <Metric
          icon={Wallet}
          label="Potential monthly savings"
          value={potentialMonthlySavingsInr > 0 ? `₹${potentialMonthlySavingsInr.toLocaleString('en-IN')}` : '₹0'}
          trend={<Pill>Modeled</Pill>}
          note={totalEmissions > 0 ? 'Modeled 15% reduction target' : 'Add records to model savings'}
          tone="green"
        />
        <Metric
          icon={Target}
          label="Reduction goal progress"
          value={goalProgressPercent.toString()}
          unit="%"
          trend={<span className="text-[11px] font-medium text-[#4B8A63]">{goalProgressPercent > 0 ? 'Active' : 'Unset'}</span>}
          note={activeInterventions > 0 ? `${activeInterventions} measures in progress` : 'Set milestone in Reports'}
          tone="sage"
        />
      </div>

      {/* Charts Grid */}
      <div className="grid gap-5 xl:grid-cols-[1.38fr_.82fr]">
        <Card className="p-5">
          <div className="flex items-start justify-between">
            <div>
              <div className="flex items-center gap-2">
                <h2 className="font-semibold text-[#405448]">Emissions trend</h2>
                {trendForecast?.status === 'ready' && (
                  <span className="inline-flex items-center gap-1 rounded-full bg-[#F3E8FF] px-2 py-0.5 text-[10px] font-semibold text-[#7E22CE]">
                    <Sparkles size={10} className="text-[#9333EA]" />
                    ML Forecast (3-mo)
                  </span>
                )}
              </div>
              <p className="mt-1 text-xs text-[#8A978D]">
                {trendForecast?.status === 'ready'
                  ? 'Historical records (solid green) & XGBoost forecast (dashed purple) · kg CO₂e'
                  : 'Estimated monthly footprint · kg CO₂e'}
              </p>
            </div>
            <button
              type="button"
              aria-label="More chart options"
              className="rounded-lg p-1.5 text-[#8A978D] hover:bg-[#F1F5EF]"
            >
              <MoreHorizontal size={18} />
            </button>
          </div>
          <div className="mt-5">
            {chartData.length > 0 ? (
              <div>
                <EmissionsLineChart data={chartData} height={230} showAxes={true} />
                {trendForecast?.status === 'ready' && trendForecast.modelMetrics && (
                  <div className="mt-3 flex flex-wrap items-center justify-between gap-2 border-t border-[#EDF1EB] pt-2.5 text-[11px] text-[#55695C]">
                    <div className="flex items-center gap-3">
                      <span className="flex items-center gap-1.5">
                        <span className="h-2 w-2 rounded-full bg-[#285943]" />
                        Measured
                      </span>
                      <span className="flex items-center gap-1.5">
                        <span className="h-2 w-2 rounded-full bg-[#C084FC]" />
                        ML Forecast (XGBoost)
                      </span>
                    </div>
                    <div className="flex items-center gap-2 font-mono text-[10px] text-[#7E22CE]">
                      <span>R²: {Number(trendForecast.modelMetrics.R2).toFixed(3)}</span>
                      <span>•</span>
                      <span>MAE: {Number(trendForecast.modelMetrics.MAE_kgCO2e).toFixed(1)} kg CO₂e</span>
                    </div>
                  </div>
                )}
                {trendForecast?.status === 'insufficient_data' && (
                  <p className="mt-2 text-[11px] text-[#7A8E80]">
                    Note: At least 2 monthly reporting periods required for ML trend forecasting.
                  </p>
                )}
              </div>
            ) : (
              <div className="flex h-[230px] flex-col items-center justify-center rounded-xl border border-dashed border-[#E0E7DE] bg-[#FBFDFB] text-center p-4">
                <Cloud className="h-8 w-8 text-[#A0B4A2]" />
                <p className="mt-2 text-xs font-semibold text-[#285943]">No emissions trajectory recorded yet</p>
                <p className="mt-1 text-[11px] text-[#7A8E80] max-w-xs">
                  Monthly trend graph will appear once consumption records are added across reporting periods.
                </p>
              </div>
            )}
          </div>
        </Card>

        <Card className="p-5">
          <div className="flex items-start justify-between">
            <div>
              <h2 className="font-semibold text-[#405448]">Resource breakdown</h2>
              <p className="mt-1 text-xs text-[#8A978D]">Emission share across categories</p>
            </div>
            <button
              type="button"
              aria-label="More breakdown options"
              className="rounded-lg p-1.5 text-[#8A978D] hover:bg-[#F1F5EF]"
            >
              <MoreHorizontal size={18} />
            </button>
          </div>
          <div className="mt-4 flex flex-col items-center">
            {breakdownData.length > 0 ? (
              <ResourceBreakdownChart data={breakdownData} />
            ) : (
              <div className="flex h-[230px] w-full flex-col items-center justify-center rounded-xl border border-dashed border-[#E0E7DE] bg-[#FBFDFB] text-center p-4">
                <Layers className="h-8 w-8 text-[#A0B4A2]" />
                <p className="mt-2 text-xs font-semibold text-[#285943]">No category breakdown available</p>
                <p className="mt-1 text-[11px] text-[#7A8E80] max-w-xs">
                  Proportional shares across Electricity, Transportation, and Waste will be calculated when records exist.
                </p>
              </div>
            )}
          </div>
        </Card>
      </div>

      {/* Recent Activity & Next Steps */}
      <div className="grid gap-5 xl:grid-cols-2">
        <Card className="p-5">
          <div className="flex items-center justify-between border-b border-[#EDF1EB] pb-3">
            <h2 className="font-semibold text-[#3E5246]">Recent activity</h2>
            <Pill tone="sage">Verified logs</Pill>
          </div>
          <div className="mt-3 divide-y divide-[#F1F5EF]">
            {activities.length > 0 ? (
              activities.map((act) => (
                <div key={act.id} className="flex items-center justify-between py-3 text-xs">
                  <div className="flex items-center gap-3">
                    <span className="grid h-8 w-8 place-items-center rounded-lg bg-[#E7F1E5] text-[#285943]">
                      {act.category === 'Electricity' ? (
                        <Zap size={14} />
                      ) : act.category === 'Transportation' ? (
                        <Truck size={14} />
                      ) : (
                        <Package size={14} />
                      )}
                    </span>
                    <div>
                      <p className="font-medium text-[#2F4436]">{act.activity}</p>
                      <p className="text-[11px] text-[#8A978D]">{act.date}</p>
                    </div>
                  </div>
                  <div className="text-right">
                    <p className="font-semibold text-[#285943]">{act.quantity}</p>
                    <p className="text-[10px] text-[#8A978D]">{act.status}</p>
                  </div>
                </div>
              ))
            ) : (
              <div className="py-8 text-center text-[#748178]">
                <p className="text-xs font-medium text-[#405448]">No activity records logged yet</p>
                <p className="mt-1 text-[11px] text-[#7A8E80]">
                  Recent activity entries will appear as you record electricity, transport, or waste data.
                </p>
              </div>
            )}
          </div>
        </Card>

        <Card className="p-5">
          <div className="flex items-center justify-between border-b border-[#EDF1EB] pb-3">
            <h2 className="font-semibold text-[#3E5246]">Top reduction opportunities</h2>
            <button
              type="button"
              onClick={() => router.push('/dashboard/simulator')}
              className="flex items-center gap-1 text-xs font-medium text-[#285943] hover:underline"
            >
              <span>Explore simulator</span>
              <ArrowRight size={13} />
            </button>
          </div>
          <div className="mt-3 divide-y divide-[#F1F5EF]">
            {totalRecordCount > 0 ? (
              <>
                <div className="flex items-center justify-between py-3 text-xs">
                  <div className="space-y-0.5">
                    <div className="flex items-center gap-2">
                      <span className="font-semibold text-[#2F4436]">Facility HVAC & Lighting Schedule</span>
                      <Pill tone="amber">High Impact</Pill>
                    </div>
                    <p className="text-[11px] text-[#78897D]">Electricity · 15% reduction target</p>
                  </div>
                  <div className="text-right font-semibold text-[#285943]">
                    {potentialMonthlySavingsInr > 0 ? `₹${potentialMonthlySavingsInr.toLocaleString('en-IN')}/mo` : 'Modeled'}
                  </div>
                </div>

                <div className="flex items-center justify-between py-3 text-xs">
                  <div className="space-y-0.5">
                    <div className="flex items-center gap-2">
                      <span className="font-semibold text-[#2F4436]">Fleet Route Consolidation</span>
                      <Pill tone="green">Medium Impact</Pill>
                    </div>
                    <p className="text-[11px] text-[#78897D]">Transportation · Avoided fuel mileage</p>
                  </div>
                  <div className="text-right font-semibold text-[#285943]">
                    Explore in Fleet
                  </div>
                </div>

                <div className="flex items-center justify-between py-3 text-xs">
                  <div className="space-y-0.5">
                    <div className="flex items-center gap-2">
                      <span className="font-semibold text-[#2F4436]">Organic Waste Segregation & Composting</span>
                      <Pill tone="green">Quick Win</Pill>
                    </div>
                    <p className="text-[11px] text-[#78897D]">Waste · Methane abatement</p>
                  </div>
                  <div className="text-right font-semibold text-[#285943]">
                    Diversion credit
                  </div>
                </div>
              </>
            ) : (
              <div className="py-8 text-center text-[#748178]">
                <p className="text-xs font-medium text-[#405448]">No baseline records available</p>
                <p className="mt-1 text-[11px] text-[#7A8E80]">
                  Log your baseline data to generate prioritized abatement interventions.
                </p>
              </div>
            )}
          </div>
        </Card>
      </div>
    </div>
  )
}
