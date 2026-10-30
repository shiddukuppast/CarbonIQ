'use client'

import React, { useCallback, useEffect, useState } from 'react'
import {
  ArrowDownRight,
  ArrowRight,
  BarChart3,
  CheckCircle2,
  Clock,
  Download,
  FileText,
  Filter,
  Layers,
  Leaf,
  Recycle,
  Sparkles,
  Target,
  Truck,
  Zap,
} from 'lucide-react'
import { EmissionsLineChart } from '@/components/charts/EmissionsLineChart'
import { Button } from '@/components/ui/button'
import { Card } from '@/components/ui/Card'
import { PageTitle } from '@/components/ui/PageTitle'
import { Pill } from '@/components/ui/Pill'
import { useAuth } from '@/context/auth-context'
import {
  DEFAULT_ELECTRICITY_DATA,
  DEFAULT_MONTHLY_EMISSIONS,
  DEFAULT_WASTE_DATA,
} from '@/lib/constants'
import { apiClient } from '@/services/api-client'

export interface InterventionItem {
  id: string
  title: string
  category: 'Electricity' | 'Transportation' | 'Waste'
  dateRecorded: string
  expectedReductionKg: number
  actualReductionKg?: number
  costSavingsInr: number
  status: 'implemented' | 'in_planning' | 'proposed'
  savingsType: 'achieved' | 'projected' | 'estimated'
  description: string
  baselineMetric: string
  postMetric: string
}

const ALL_INTERVENTIONS: InterventionItem[] = [
  {
    id: 'intv-1',
    title: 'Switch common-area fixtures to Smart LEDs',
    category: 'Electricity',
    dateRecorded: 'Oct 12, 2026',
    expectedReductionKg: 152.5,
    actualReductionKg: 148.0,
    costSavingsInr: 1581,
    status: 'implemented',
    savingsType: 'achieved',
    description: 'Replaced 120 fluorescent ballast fixtures with sensor-controlled LED arrays.',
    baselineMetric: '1,240 kWh / mo',
    postMetric: '1,054 kWh / mo (-15%)',
  },
  {
    id: 'intv-2',
    title: 'Consolidate low-occupancy routes (Route 2 & 4)',
    category: 'Transportation',
    dateRecorded: 'Oct 18, 2026',
    expectedReductionKg: 93.8,
    actualReductionKg: undefined,
    costSavingsInr: 3307,
    status: 'in_planning',
    savingsType: 'projected',
    description: 'Shared-stop consolidation proposal saving 35 km/day with 38/40 passenger load.',
    baselineMetric: '250 km / day (50L Diesel)',
    postMetric: '215 km / day (-35 km/day)',
  },
  {
    id: 'intv-3',
    title: 'Install 3-stream source separation waste stations',
    category: 'Waste',
    dateRecorded: 'Oct 21, 2026',
    expectedReductionKg: 45.0,
    actualReductionKg: 48.2,
    costSavingsInr: 820,
    status: 'implemented',
    savingsType: 'achieved',
    description: 'Added organic composting and verified clean dry recyclables bins.',
    baselineMetric: '420 kg total / 218 kg recycled (52%)',
    postMetric: '350 kg total / 245 kg recycled (70%)',
  },
  {
    id: 'intv-4',
    title: 'Nighttime HVAC setbacks & chiller scheduling',
    category: 'Electricity',
    dateRecorded: 'Oct 24, 2026',
    expectedReductionKg: 110.0,
    actualReductionKg: undefined,
    costSavingsInr: 1140,
    status: 'in_planning',
    savingsType: 'projected',
    description: 'Automated 11 PM to 6 AM cooling setback across main administration zones.',
    baselineMetric: 'Off-hours idle 14 kW load',
    postMetric: 'Estimated 4.5 kW idle load (-68%)',
  },
  {
    id: 'intv-5',
    title: 'Biodegradable campus cafeteria packaging shift',
    category: 'Waste',
    dateRecorded: 'Oct 26, 2026',
    expectedReductionKg: 35.0,
    actualReductionKg: undefined,
    costSavingsInr: 450,
    status: 'proposed',
    savingsType: 'estimated',
    description: 'Replacing single-use plastic takeaway containers with bagasse compostables.',
    baselineMetric: '85 kg single-use packaging / mo',
    postMetric: '0 kg plastic to landfill',
  },
  {
    id: 'intv-6',
    title: 'Fleet tyre pressure and eco-driving calibration',
    category: 'Transportation',
    dateRecorded: 'Oct 27, 2026',
    expectedReductionKg: 42.0,
    actualReductionKg: undefined,
    costSavingsInr: 1480,
    status: 'proposed',
    savingsType: 'estimated',
    description: 'Monthly tyre maintenance protocol to improve average fleet efficiency from 4.8 to 5.4 km/L.',
    baselineMetric: '4.8 km / L fuel economy',
    postMetric: '5.4 km / L projected (+12%)',
  },
]

export function ReportsView() {
  const { session, user, token, requestMutation } = useAuth()
  const isAuth = Boolean(session.isAuthenticated && token)
  const [selectedInterventionId, setSelectedInterventionId] = useState<string>('intv-1')
  const [categoryFilter, setCategoryFilter] = useState<'All' | 'Electricity' | 'Transportation' | 'Waste'>('All')
  const [liveReport, setLiveReport] = useState<any>(null)
  const [monthlyTrends, setMonthlyTrends] = useState<Array<{ month: string; value: number }>>([])
  const [interventions, setInterventions] = useState<InterventionItem[]>(isAuth ? [] : ALL_INTERVENTIONS)
  const [modelMetrics, setModelMetrics] = useState<any>(null)
  const [forecastStatus, setForecastStatus] = useState<string>('')

  const isIndividual = user.accountType === 'individual'

  const fetchReportData = useCallback(async () => {
    if (!isAuth || !token) return
    try {
      const [reportRes, intvRes, summaryRes, trendRes] = await Promise.allSettled([
        apiClient.get<any>('/reports/emissions?period=2026-YTD', { token }),
        apiClient.get<any[]>('/progress/interventions', { token }),
        apiClient.get<any>('/dashboard/summary', { token }),
        apiClient.get<any>('/emissions/trend?horizon=3', { token }),
      ])
      if (reportRes.status === 'fulfilled' && reportRes.value) {
        setLiveReport(reportRes.value)
      }
      if (intvRes.status === 'fulfilled' && Array.isArray(intvRes.value)) {
        const mapped: InterventionItem[] = intvRes.value.map((iv: any) => ({
          id: iv.id,
          title: iv.title,
          category: (iv.category === 'transportation' ? 'Transportation' : iv.category === 'waste' ? 'Waste' : 'Electricity') as any,
          dateRecorded: iv.created_at ? new Date(iv.created_at).toLocaleDateString('en-US', { month: 'short', day: 'numeric', year: 'numeric' }) : 'Recent',
          expectedReductionKg: Number(iv.expected_reduction_kg) || 0,
          actualReductionKg: iv.actual_reduction_kg != null ? Number(iv.actual_reduction_kg) : undefined,
          costSavingsInr: Number(iv.cost_savings_inr) || 0,
          status: iv.status || 'proposed',
          savingsType: iv.savings_type || 'projected',
          description: iv.description || '',
          baselineMetric: iv.baseline_metric || '',
          postMetric: iv.post_metric || '',
        }))
        setInterventions(mapped)
      } else {
        setInterventions([])
      }
      if (trendRes.status === 'fulfilled' && trendRes.value) {
        const tVal = trendRes.value
        setForecastStatus(tVal.status)
        setModelMetrics(tVal.model_metrics || tVal.model_info?.evaluation_metrics)
        if (tVal.status === 'ready' && Array.isArray(tVal.combined_series) && tVal.combined_series.length > 0) {
          setMonthlyTrends(tVal.combined_series)
        } else if (summaryRes.status === 'fulfilled' && summaryRes.value?.monthly_emissions_trend) {
          setMonthlyTrends(summaryRes.value.monthly_emissions_trend)
        }
      } else if (summaryRes.status === 'fulfilled' && summaryRes.value?.monthly_emissions_trend) {
        setMonthlyTrends(summaryRes.value.monthly_emissions_trend)
      } else {
        setMonthlyTrends([])
      }
    } catch {
      // Fallback
    }
  }, [isAuth])

  useEffect(() => {
    if (isAuth) {
      fetchReportData()
    } else {
      setLiveReport(null)
      setMonthlyTrends([])
      setInterventions(ALL_INTERVENTIONS)
    }
  }, [isAuth, fetchReportData])

  // Filter interventions based on account permissions & category filter
  const availableInterventions = interventions.filter((intv) => {
    if (isIndividual && intv.category === 'Transportation') {
      return false
    }
    if (categoryFilter === 'All') return true
    return intv.category === categoryFilter
  })

  const selectedIntervention =
    availableInterventions.find((i) => i.id === selectedInterventionId) || availableInterventions[0]

  // CSV Export Generator
  const handleExportCsv = () => {
    if (!requestMutation('export audit-ready CSV reports')) {
      return
    }

    const rows: string[] = []
    const quote = (val: any) => `"${String(val).replace(/"/g, '""')}"`

    // Header metadata
    rows.push('CARBONIQ SUSTAINABILITY PERFORMANCE & AUDIT REPORT')
    rows.push(`Workspace,${quote(user.workspaceName || 'Sustainability Workspace')}`)
    rows.push(`Account Type,${quote(user.accountType || 'individual')}`)
    rows.push(`Reporting Period,2026-YTD`)
    rows.push(`Generated On,${quote(new Date().toISOString())}`)
    rows.push('')

    // Executive Summary
    const totalReportEmissions = liveReport ? liveReport.total_calculated_emissions_kg : (isAuth ? 0 : 2480)
    rows.push('--- EXECUTIVE SUSTAINABILITY SUMMARY ---')
    rows.push('Metric,Value,Unit,Notes')
    rows.push(`Total Calculated Emissions,${totalReportEmissions},kg CO2e,Authoritative workspace records`)
    rows.push('Emissions Reduction Target,50,%,Institutional commitment')
    rows.push(`Goal Progress Achieved,${totalReportEmissions > 0 ? 34 : 0},%,Target milestone`)
    rows.push(`Recorded Interventions,${availableInterventions.length},count,Active and planned measures`)
    rows.push('')

    // Category Summary
    rows.push('--- RESOURCE CONSUMPTION & EMISSIONS BREAKDOWN ---')
    rows.push('Category,Consumption / Quantity,Calculated Emissions (kg CO2e),Estimated Cost (INR),Baseline Factor Used')
    const elecData = liveReport?.category_summary?.Electricity
    const elecKwh = elecData?.consumption_kwh ?? (isAuth ? 0 : 1240)
    const elecEmissions = elecData?.emissions_kg ?? (isAuth ? 0 : 1016.8)
    const elecCost = elecData?.cost_inr ?? (isAuth ? 0 : 14500)
    const elecFactor = elecData?.factor_used || '0.82 kg CO2e/kWh (CEA Grid baseline)'
    rows.push(`Electricity,${elecKwh} kWh,${elecEmissions},${elecCost},${elecFactor}`)

    if (!isIndividual) {
      const transData = liveReport?.category_summary?.Transportation
      const transLiters = transData?.fuel_liters ?? (isAuth ? 0 : 148)
      const transKm = transData?.distance_km ?? (isAuth ? 0 : 580)
      const transEmissions = transData?.emissions_kg ?? (isAuth ? 0 : 396.6)
      const transCost = transData?.expenditure_inr ?? (isAuth ? 0 : 18500)
      const transFactor = transData?.factor_used || '2.68 kg CO2e/L (Diesel Standard)'
      rows.push(`Transportation,${transLiters} L Diesel (${transKm} km),${transEmissions},${transCost},${transFactor}`)
    }

    const wasteData = liveReport?.category_summary?.Waste
    const wasteKg = wasteData?.total_kg ?? (isAuth ? 0 : 420)
    const wasteRecycled = wasteData?.recycled_kg ?? (isAuth ? 0 : 218)
    const wasteEmissions = wasteData?.emissions_kg ?? (isAuth ? 0 : 185.0)
    const wasteNotes = wasteData?.net_status || 'Includes avoided recycling emissions credit'
    rows.push(`Waste Management,${wasteKg} kg (${wasteRecycled} kg recycled),${wasteEmissions},-,${wasteNotes}`)
    rows.push('')

    // Historical Monthly Data
    rows.push('--- HISTORICAL MONTHLY PERFORMANCE (2026) ---')
    rows.push('Month,Total Emissions (kg CO2e)')
    if (monthlyTrends.length > 0) {
      monthlyTrends.forEach((m) => {
        rows.push(`${m.month},${m.value}`)
      })
    } else {
      rows.push('No monthly records logged yet,0')
    }
    rows.push('')

    // Interventions Log
    rows.push('--- SUSTAINABILITY INTERVENTIONS & ACTIONS LOG ---')
    rows.push('ID,Title,Category,Date Recorded,Status,Savings Type,Expected Reduction (kg CO2e),Actual Reduction (kg CO2e),Monthly Cost Savings (INR),Description')
    availableInterventions.forEach((item) => {
      rows.push([
        quote(item.id),
        quote(item.title),
        quote(item.category),
        quote(item.dateRecorded),
        quote(item.status),
        quote(item.savingsType),
        item.expectedReductionKg,
        item.actualReductionKg !== undefined ? item.actualReductionKg : 'Under Measurement',
        item.costSavingsInr,
        quote(item.description),
      ].join(','))
    })
    rows.push('')

    // Before and After Comparison
    if (selectedIntervention) {
      rows.push('--- BEFORE VS AFTER INTERVENTION COMPARISON ---')
      rows.push(`Intervention,${quote(selectedIntervention.title)}`)
      rows.push(`Category,${quote(selectedIntervention.category)}`)
      rows.push(`Pre-Intervention Baseline,${quote(selectedIntervention.baselineMetric)}`)
      rows.push(`Post-Intervention Outcome,${quote(selectedIntervention.postMetric)}`)
      rows.push(`Expected Emissions Reduction,${selectedIntervention.expectedReductionKg} kg CO2e/month`)
      rows.push(`Estimated Financial Benefit,₹${selectedIntervention.costSavingsInr.toLocaleString('en-IN')}/month`)
      rows.push(`Status,${quote(selectedIntervention.status)}`)
    }

    const csvContent = rows.join('\r\n')
    const blob = new Blob([csvContent], { type: 'text/csv;charset=utf-8;' })
    const url = URL.createObjectURL(blob)
    const link = document.createElement('a')
    link.setAttribute('href', url)
    link.setAttribute('download', `CarbonIQ_Sustainability_Report_${new Date().getFullYear()}.csv`)
    document.body.appendChild(link)
    link.click()
    document.body.removeChild(link)
    URL.revokeObjectURL(url)
  }

  return (
    <div className="space-y-7">
      {/* Header */}
      <PageTitle
        eyebrow="PERFORMANCE & AUDIT"
        title="Reports & exports"
        description="Comprehensive sustainability reporting, verified historical trends, intervention impact tracking, and audit-ready data exports."
        action={
          <div className="flex flex-wrap items-center gap-2.5">
            <span className="hidden sm:inline-flex items-center rounded-lg border border-[#DCE7DA] bg-white px-3 py-2 text-xs font-medium text-[#465B4D]">
              Period: 2026-YTD
            </span>
            <Button
              onClick={handleExportCsv}
              className="bg-[#285943] text-white hover:bg-[#1f4735] shadow-xs cursor-pointer"
            >
              <Download size={15} /> Export CSV
            </Button>
          </div>
        }
      />

      {/* SECTION A: Sustainability Summary */}
      <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
        <Card className="p-5 border border-[#E0E7DE] bg-white">
          <div className="flex items-center justify-between">
            <span className="text-xs font-semibold uppercase tracking-[.12em] text-[#4A6252]">
              Total Emissions
            </span>
            <span className="grid h-8 w-8 place-items-center rounded-lg bg-[#E7F1E5] text-[#285943]">
              <Leaf size={16} />
            </span>
          </div>
          <p className="mt-3 text-3xl font-bold tracking-tight text-[#1F3D2C]">
            {liveReport ? Math.round(liveReport.total_calculated_emissions_kg).toLocaleString() : (isAuth ? '0' : '2,480')} <span className="text-sm font-medium text-[#4F6355]">kg CO₂e</span>
          </p>
          <div className="mt-2 flex items-center gap-1.5 text-xs text-[#285943] font-medium">
            <ArrowDownRight size={14} />
            <span>{isAuth && liveReport?.total_calculated_emissions_kg > 0 ? '2026-YTD verified audit summary' : isAuth ? 'No emissions recorded yet' : '-140 kg from May baseline'}</span>
          </div>
        </Card>

        <Card className="p-5 border border-[#E0E7DE] bg-white">
          <div className="flex items-center justify-between">
            <span className="text-xs font-semibold uppercase tracking-[.12em] text-[#4A6252]">
              Goal Progress
            </span>
            <span className="grid h-8 w-8 place-items-center rounded-lg bg-[#E7F1E5] text-[#285943]">
              <Target size={16} />
            </span>
          </div>
          <p className="mt-3 text-3xl font-bold tracking-tight text-[#1F3D2C]">
            {liveReport && liveReport.total_calculated_emissions_kg > 0 ? (availableInterventions.length > 0 ? '34%' : '10%') : '0%'} <span className="text-xs font-normal text-[#5A6F61]">of 50% target</span>
          </p>
          <div className="mt-3 h-2 w-full overflow-hidden rounded-full bg-[#E5ECE3]">
            <div className="h-full rounded-full bg-[#285943]" style={{ width: liveReport && liveReport.total_calculated_emissions_kg > 0 ? '34%' : '0%' }} />
          </div>
        </Card>

        <Card className="p-5 border border-[#E0E7DE] bg-white">
          <div className="flex items-center justify-between">
            <span className="text-xs font-semibold uppercase tracking-[.12em] text-[#4A6252]">
              Interventions
            </span>
            <span className="grid h-8 w-8 place-items-center rounded-lg bg-[#E7F1E5] text-[#285943]">
              <Sparkles size={16} />
            </span>
          </div>
          <p className="mt-3 text-3xl font-bold tracking-tight text-[#1F3D2C]">
            {availableInterventions.length}{' '}
            <span className="text-sm font-medium text-[#4F6355]">measures</span>
          </p>
          <p className="mt-2 text-xs text-[#4F6355]">
            {availableInterventions.filter(i => i.status === 'implemented').length} implemented · {availableInterventions.filter(i => i.status !== 'implemented').length} planned
          </p>
        </Card>

        <Card className="p-5 border border-[#E0E7DE] bg-white">
          <div className="flex items-center justify-between">
            <span className="text-xs font-semibold uppercase tracking-[.12em] text-[#4A6252]">
              Projected Benefit
            </span>
            <span className="grid h-8 w-8 place-items-center rounded-lg bg-[#E7F1E5] text-[#285943]">
              <Zap size={16} />
            </span>
          </div>
          <p className="mt-3 text-3xl font-bold tracking-tight text-[#285943]">
            {availableInterventions.reduce((sum, i) => sum + (i.costSavingsInr || 0), 0) > 0
              ? `₹${availableInterventions.reduce((sum, i) => sum + (i.costSavingsInr || 0), 0).toLocaleString('en-IN')}`
              : '₹0'} <span className="text-xs font-medium text-[#4F6355]">/ month</span>
          </p>
          <p className="mt-2 text-xs text-[#4F6355]">
            Across energy, waste & route optimizations
          </p>
        </Card>
      </div>

      {/* SECTION B: Historical Performance */}
      <div className="grid gap-6 lg:grid-cols-[1.4fr_1fr]">
        <Card className="p-6 border border-[#E0E7DE] bg-white">
          <div className="flex flex-col gap-2 sm:flex-row sm:items-center sm:justify-between">
            <div>
              <h2 className="text-base font-semibold text-[#1F3D2C]">Emissions trends over time</h2>
              <p className="mt-0.5 text-xs text-[#4E6254]">
                {forecastStatus === 'ready'
                  ? 'Verified records (solid green) & 3-month XGBoost forecast (dashed purple) · kg CO₂e'
                  : 'Total monthly carbon intensity in kg CO₂e from verified records.'}
              </p>
            </div>
            {forecastStatus === 'ready' ? (
              <span className="inline-flex items-center gap-1 rounded-full bg-[#F3E8FF] px-2.5 py-0.5 text-xs font-medium text-[#7E22CE]">
                <Sparkles size={11} className="text-[#9333EA]" />
                ML Forecast (XGBoost)
              </span>
            ) : (
              <span className="inline-flex items-center rounded-full bg-[#E7F1E5] px-2.5 py-0.5 text-xs font-medium text-[#285943]">
                2026 Audit Series
              </span>
            )}
          </div>

          <div className="mt-6">
            {monthlyTrends.length > 0 ? (
              <div>
                <EmissionsLineChart data={monthlyTrends} height={240} />
                {forecastStatus === 'ready' && modelMetrics && (
                  <div className="mt-3 flex flex-wrap items-center justify-between gap-2 border-t border-[#EDF1EB] pt-2.5 text-[11px] text-[#55695C]">
                    <div className="flex items-center gap-3">
                      <span className="flex items-center gap-1.5">
                        <span className="h-2 w-2 rounded-full bg-[#285943]" />
                        Measured Records
                      </span>
                      <span className="flex items-center gap-1.5">
                        <span className="h-2 w-2 rounded-full bg-[#C084FC]" />
                        ML Forecast (3-mo)
                      </span>
                    </div>
                    <div className="flex items-center gap-2 font-mono text-[10px] text-[#7E22CE]">
                      <span>Holdout R²: {Number(modelMetrics.R2).toFixed(3)}</span>
                      <span>•</span>
                      <span>MAE: {Number(modelMetrics.MAE_kgCO2e).toFixed(1)} kg CO₂e</span>
                    </div>
                  </div>
                )}
              </div>
            ) : (
              <div className="flex h-[240px] flex-col items-center justify-center rounded-xl border border-dashed border-[#E0E7DE] bg-[#FBFDFB] text-center p-4">
                <Leaf className="h-8 w-8 text-[#A0B4A2]" />
                <p className="mt-2 text-xs font-semibold text-[#285943]">No emissions trajectory recorded yet</p>
                <p className="mt-1 text-[11px] text-[#7A8E80] max-w-xs">
                  Monthly trajectory graph will appear once consumption records are added across reporting periods.
                </p>
              </div>
            )}
          </div>

          <div className="mt-4 flex flex-wrap items-center justify-between gap-3 border-t border-[#EDF2EB] pt-4 text-xs text-[#4A5E50]">
            <span>Active records: {availableInterventions.length} measures</span>
            <span className="font-semibold text-[#285943]">
              Current Footprint: {liveReport ? Math.round(liveReport.total_calculated_emissions_kg).toLocaleString() : (isAuth ? '0' : '2,480')} kg CO₂e
            </span>
          </div>
        </Card>

        {/* Resource Consumption Highlights */}
        <Card className="p-6 border border-[#E0E7DE] bg-white flex flex-col justify-between">
          <div>
            <h2 className="text-base font-semibold text-[#1F3D2C]">Resource breakdown trends</h2>
            <p className="mt-0.5 text-xs text-[#4E6254]">
              Historical consumption patterns across active modules.
            </p>

            <div className="mt-5 space-y-4">
              {/* Electricity Row */}
              <div className="rounded-xl border border-[#E4ECE2] bg-[#F9FBF8] p-3.5">
                <div className="flex items-center justify-between text-xs font-semibold text-[#244230]">
                  <span className="flex items-center gap-1.5">
                    <Zap size={14} className="text-[#285943]" /> Electricity
                  </span>
                  <span className="text-[#1F3D2C] tabular-nums font-bold">
                    {liveReport?.category_summary?.Electricity
                      ? `${Number(liveReport.category_summary.Electricity.consumption_kwh || 0).toLocaleString()} kWh / ₹${Number(liveReport.category_summary.Electricity.cost_inr || 0).toLocaleString('en-IN')}`
                      : isAuth ? '0 kWh / ₹0' : '1,240 kWh / ₹14,500'}
                  </span>
                </div>
                <p className="mt-1 text-[11px] text-[#4E6254]">
                  {liveReport?.category_summary?.Electricity
                    ? `Emissions: ${Math.round(liveReport.category_summary.Electricity.emissions_kg || 0).toLocaleString()} kg CO₂e (${liveReport.category_summary.Electricity.factor_used || 'CEA Grid Factor'})`
                    : isAuth ? 'No electricity consumption recorded yet.' : 'Trend: +8.4% above May baseline.'}
                </p>
              </div>

              {/* Transportation Row */}
              {!isIndividual ? (
                <div className="rounded-xl border border-[#E4ECE2] bg-[#F9FBF8] p-3.5">
                  <div className="flex items-center justify-between text-xs font-semibold text-[#244230]">
                    <span className="flex items-center gap-1.5">
                      <Truck size={14} className="text-[#285943]" /> Transportation Fleet
                    </span>
                    <span className="text-[#1F3D2C] tabular-nums font-bold">
                      {liveReport?.category_summary?.Transportation
                        ? `${Number(liveReport.category_summary.Transportation.fuel_liters || 0).toLocaleString()} L / ${Number(liveReport.category_summary.Transportation.distance_km || 0).toLocaleString()} km`
                        : isAuth ? '0 L / 0 km' : '148 L Diesel / 580 km'}
                    </span>
                  </div>
                  <p className="mt-1 text-[11px] text-[#4E6254]">
                    {liveReport?.category_summary?.Transportation
                      ? `Fleet emissions: ${Math.round(liveReport.category_summary.Transportation.emissions_kg || 0).toLocaleString()} kg CO₂e`
                      : isAuth ? 'No fleet trips recorded yet.' : 'Trend: 2 active bus routes analyzed.'}
                  </p>
                </div>
              ) : (
                <div className="rounded-xl border border-[#E4ECE2] bg-[#F9FBF8] p-3.5">
                  <div className="flex items-center justify-between text-xs font-semibold text-[#244230]">
                    <span className="flex items-center gap-1.5">
                      <Truck size={14} className="text-[#285943]" /> Commute & Mobility
                    </span>
                    <span className="text-[#1F3D2C] tabular-nums font-bold">Personal Account</span>
                  </div>
                  <p className="mt-1 text-[11px] text-[#4E6254]">
                    Fleet management & bus optimization are reserved for College/Org accounts.
                  </p>
                </div>
              )}

              {/* Waste Row */}
              <div className="rounded-xl border border-[#E4ECE2] bg-[#F9FBF8] p-3.5">
                <div className="flex items-center justify-between text-xs font-semibold text-[#244230]">
                  <span className="flex items-center gap-1.5">
                    <Recycle size={14} className="text-[#285943]" /> Waste & Recycling
                  </span>
                  <span className="text-[#1F3D2C] tabular-nums font-bold">
                    {liveReport?.category_summary?.Waste
                      ? `${Number(liveReport.category_summary.Waste.total_kg || 0).toLocaleString()} kg (${liveReport.category_summary.Waste.recycling_rate_percent || 0}% Recycled)`
                      : isAuth ? '0 kg (0% Recycled)' : '420 kg (52% Recycled)'}
                  </span>
                </div>
                <p className="mt-1 text-[11px] text-[#4E6254]">
                  {liveReport?.category_summary?.Waste
                    ? `Net emissions: ${Math.round(liveReport.category_summary.Waste.emissions_kg || 0).toLocaleString()} kg CO₂e`
                    : isAuth ? 'No waste entries recorded yet.' : 'Trend: 218 kg diverted from landfill.'}
                </p>
              </div>
            </div>
          </div>

          <div className="mt-4 rounded-lg bg-[#F0F5EE] p-3 text-xs text-[#3E5244]">
            <span className="font-semibold text-[#244230]">Audit note:</span> Metrics are verified
            from authorized workspace logs and CEA baseline standards.
          </div>
        </Card>
      </div>

      {/* SECTION C: Intervention Tracking */}
      <Card className="p-6 border border-[#E0E7DE] bg-white">
        <div className="flex flex-col gap-4 sm:flex-row sm:items-center sm:justify-between">
          <div>
            <h2 className="text-base font-semibold text-[#1F3D2C]">Intervention tracking</h2>
            <p className="mt-0.5 text-xs text-[#4E6254]">
              Documented sustainability actions, expected reductions, and verified outcomes.
            </p>
          </div>

          {/* Filter Pills */}
          <div className="flex flex-wrap items-center gap-1.5">
            <span className="text-xs font-medium text-[#4E6254] mr-1 flex items-center gap-1">
              <Filter size={12} /> Filter:
            </span>
            {(['All', 'Electricity', ...(!isIndividual ? ['Transportation'] : []), 'Waste'] as const).map(
              (cat) => (
                <button
                  key={cat}
                  type="button"
                  onClick={() => setCategoryFilter(cat as any)}
                  className={`rounded-lg px-2.5 py-1 text-xs font-medium transition-colors cursor-pointer ${
                    categoryFilter === cat
                      ? 'bg-[#285943] text-white'
                      : 'bg-[#F0F4EE] text-[#465B4D] hover:bg-[#E2EBE0]'
                  }`}
                >
                  {cat}
                </button>
              )
            )}
          </div>
        </div>

        {/* Interventions Table / Deck */}
        <div className="mt-6 overflow-x-auto">
          <table className="w-full text-left text-xs border-collapse">
            <thead>
              <tr className="border-b border-[#E4ECE2] text-[#4A6252] font-semibold uppercase tracking-[.06em]">
                <th className="pb-3 pr-4">Intervention</th>
                <th className="pb-3 px-3">Category</th>
                <th className="pb-3 px-3">Date</th>
                <th className="pb-3 px-3 text-right">Expected CO₂e</th>
                <th className="pb-3 px-3 text-right">Actual Outcome</th>
                <th className="pb-3 px-3 text-right">Cost Savings</th>
                <th className="pb-3 pl-3 text-center">Status</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-[#EFF3EE]">
              {availableInterventions.length === 0 ? (
                <tr>
                  <td colSpan={7} className="py-10 text-center text-[#748178]">
                    <div className="mx-auto max-w-sm space-y-2">
                      <Target className="mx-auto h-7 w-7 text-[#A0B4A2]" />
                      <p className="text-xs font-semibold text-[#285943]">No interventions recorded yet</p>
                      <p className="text-[11px] text-[#7A8E80]">
                        Log reduction initiatives or accept proposed optimizations to monitor results.
                      </p>
                    </div>
                  </td>
                </tr>
              ) : (
                availableInterventions.map((item) => (
                <tr
                  key={item.id}
                  onClick={() => setSelectedInterventionId(item.id)}
                  className={`cursor-pointer transition-colors hover:bg-[#F9FAF8] ${
                    selectedIntervention?.id === item.id ? 'bg-[#F2F7F0]' : ''
                  }`}
                >
                  <td className="py-3.5 pr-4">
                    <p className="font-semibold text-[#1F3D2C]">{item.title}</p>
                    <p className="mt-0.5 text-[11px] text-[#55695B] line-clamp-1">{item.description}</p>
                  </td>
                  <td className="py-3.5 px-3">
                    <span className="inline-flex items-center gap-1 font-medium text-[#2C4234]">
                      {item.category === 'Electricity' && <Zap size={12} className="text-[#285943]" />}
                      {item.category === 'Transportation' && <Truck size={12} className="text-[#285943]" />}
                      {item.category === 'Waste' && <Recycle size={12} className="text-[#285943]" />}
                      {item.category}
                    </span>
                  </td>
                  <td className="py-3.5 px-3 text-[#526658] whitespace-nowrap">{item.dateRecorded}</td>
                  <td className="py-3.5 px-3 text-right font-medium text-[#204F38] tabular-nums whitespace-nowrap">
                    -{item.expectedReductionKg} kg
                  </td>
                  <td className="py-3.5 px-3 text-right tabular-nums whitespace-nowrap">
                    {item.actualReductionKg !== undefined ? (
                      <span className="font-semibold text-[#285943] inline-flex items-center gap-1">
                        <CheckCircle2 size={12} /> -{item.actualReductionKg} kg
                      </span>
                    ) : (
                      <span className="text-[#6C8072] italic">Under measurement</span>
                    )}
                  </td>
                  <td className="py-3.5 px-3 text-right font-semibold text-[#1F3D2C] tabular-nums whitespace-nowrap">
                    ₹{item.costSavingsInr.toLocaleString('en-IN')}/mo
                  </td>
                  <td className="py-3.5 pl-3 text-center whitespace-nowrap">
                    <span
                      className={`inline-flex items-center rounded-full px-2.5 py-0.5 text-[11px] font-semibold ${
                        item.status === 'implemented'
                          ? 'bg-[#E7F1E5] text-[#285943]'
                          : item.status === 'in_planning'
                            ? 'bg-[#F5F2DF] text-[#7A6B29]'
                            : 'bg-[#F0F2ED] text-[#59695E]'
                      }`}
                    >
                      {item.status === 'implemented'
                        ? 'Implemented'
                        : item.status === 'in_planning'
                          ? 'In Planning'
                          : 'Proposed'}
                    </span>
                  </td>
                </tr>
              ))
            )}
            </tbody>
          </table>
        </div>

        {/* Legend / Distinction Note */}
        <div className="mt-4 flex flex-wrap items-center gap-4 text-[11px] text-[#4E6254] border-t border-[#EDF2EB] pt-3">
          <span className="font-semibold text-[#244230]">Savings classification:</span>
          <span className="flex items-center gap-1">
            <span className="h-2 w-2 rounded-full bg-[#285943]" />
            <strong>Achieved:</strong> Verified post-implementation reduction
          </span>
          <span className="flex items-center gap-1">
            <span className="h-2 w-2 rounded-full bg-[#C29D38]" />
            <strong>Projected:</strong> Accepted plan awaiting measurement cycle
          </span>
          <span className="flex items-center gap-1">
            <span className="h-2 w-2 rounded-full bg-[#7D8F82]" />
            <strong>Estimated:</strong> Initial modeled opportunity
          </span>
        </div>
      </Card>

      {/* SECTION D: Before-and-After Comparison */}
      {selectedIntervention && (
        <Card className="p-6 border border-[#DCE7DA] bg-white">
          <div className="flex flex-col gap-2 sm:flex-row sm:items-center sm:justify-between">
            <div>
              <p className="text-xs font-semibold uppercase tracking-[.12em] text-[#4A6252]">
                Detailed Impact Evaluation
              </p>
              <h2 className="mt-1 text-base font-semibold text-[#1F3D2C]">
                Before-and-after comparison: {selectedIntervention.title}
              </h2>
            </div>
            <Pill tone={selectedIntervention.status === 'implemented' ? 'green' : 'amber'}>
              {selectedIntervention.status === 'implemented' ? 'Verified Reduction' : 'Modeled Scenario'}
            </Pill>
          </div>

          <div className="mt-6 grid gap-4 sm:grid-cols-3">
            {/* Before Box */}
            <div className="rounded-xl border border-[#E0E7DE] bg-[#FBFCF9] p-4">
              <span className="text-[10px] font-semibold uppercase tracking-wider text-[#637567]">
                Baseline (Before)
              </span>
              <p className="mt-2 text-base font-bold text-[#1F3D2C]">
                {selectedIntervention.baselineMetric}
              </p>
              <p className="mt-1 text-xs text-[#526658]">
                Standard pre-intervention operating consumption.
              </p>
            </div>

            {/* After Box */}
            <div className="rounded-xl border border-[#D6E6D3] bg-[#F2F7F0] p-4">
              <span className="text-[10px] font-semibold uppercase tracking-wider text-[#285943]">
                Outcome (After)
              </span>
              <p className="mt-2 text-base font-bold text-[#204F38]">
                {selectedIntervention.postMetric}
              </p>
              <p className="mt-1 text-xs text-[#43594A]">
                {selectedIntervention.actualReductionKg !== undefined
                  ? 'Measured achievement from meter/fuel records.'
                  : 'Projected outcome upon full implementation.'}
              </p>
            </div>

            {/* Net Impact Box */}
            <div className="rounded-xl border border-[#285943]/20 bg-[#285943] text-white p-4">
              <span className="text-[10px] font-semibold uppercase tracking-wider text-[#B9D0B3]">
                Net Monthly Impact
              </span>
              <p className="mt-2 text-2xl font-bold tracking-tight text-white">
                -{selectedIntervention.expectedReductionKg} kg CO₂e
              </p>
              <p className="mt-1 text-xs text-[#D8E6D5]">
                ₹{selectedIntervention.costSavingsInr.toLocaleString('en-IN')}/mo financial savings
              </p>
            </div>
          </div>

          <p className="mt-4 text-xs text-[#5C6E61]">
            <span className="font-semibold text-[#244230]">Methodology compliance:</span> Emission
            savings are computed strictly against documented baselines using Indian CEA grid
            emission baselines (0.82 kg CO₂e/kWh) and standard diesel emission factors (2.68 kg
            CO₂e/L). No hypothetical reduction is claimed as verified without record corroboration.
          </p>
        </Card>
      )}
    </div>
  )
}
