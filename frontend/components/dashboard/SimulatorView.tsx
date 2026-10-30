'use client'

import React, { useCallback, useEffect, useState } from 'react'
import { Card } from '@/components/ui/Card'
import { PageTitle } from '@/components/ui/PageTitle'
import { Pill } from '@/components/ui/Pill'
import { useAuth } from '@/context/auth-context'
import { calculateSavingsProjection } from '@/lib/calculations'
import { apiClient } from '@/services/api-client'
import { authService } from '@/services/auth.service'

interface BackendSimResult {
  module: string
  baseline: Record<string, any>
  proposed: Record<string, any>
  difference: Record<string, any>
  estimated_cost_savings_inr: number
  estimated_emissions_reduction_kg: number
  assumptions: string[]
  limitations: string
}

export function SimulatorView() {
  const { session, token } = useAuth()
  const activeToken = token || (typeof window !== 'undefined' ? authService.getToken() : null)
  const isAuth = Boolean((session.isAuthenticated || Boolean(activeToken)) && activeToken)

  const [elec, setElec] = useState(15)
  const [transport, setTransport] = useState(10)
  const [wasteR, setWasteR] = useState(20)

  const [backendSavings, setBackendSavings] = useState<{
    savingsMonthly: number
    emissionsImprovementPercent: number
    currentEmissions: number
    proposedEmissions: number
    projectedKwhReduction: number
    projectedWasteReduction: number
    baselineElectricityKwh: number
    hasElecData: boolean
    baselineTransportDistanceKm: number
    hasTransData: boolean
    baselineWasteKg: number
    hasWasteData: boolean
    baselineWasteEmissions: number
    projectedWasteEmissionsReduction: number
    assumptions: string[]
  } | null>(null)

  // Client-side fallback projection (for demo/unauthenticated mode)
  const clientFallback = calculateSavingsProjection({
    electricityReduction: elec,
    transportReduction: transport,
    wasteReduction: wasteR,
  })

  const runBackendSimulation = useCallback(async () => {
    const effectiveToken = activeToken || (typeof window !== 'undefined' ? authService.getToken() : null)
    if (!effectiveToken) return

    try {
      const [elecRes, transRes, wasteRes] = await Promise.allSettled([
        apiClient.post<BackendSimResult>(
          '/simulator/electricity',
          { percent_reduction: elec },
          { token: effectiveToken }
        ),
        apiClient.post<BackendSimResult>(
          '/simulator/transportation',
          { percent_distance_reduction: transport },
          { token: effectiveToken }
        ),
        apiClient.post<BackendSimResult>(
          '/simulator/waste',
          { percent_reduction: wasteR },
          { token: effectiveToken }
        ),
      ])

      const elecData = elecRes.status === 'fulfilled' ? elecRes.value : null
      const transData = transRes.status === 'fulfilled' ? transRes.value : null
      const wasteData = wasteRes.status === 'fulfilled' ? wasteRes.value : null

      if (!elecData && !transData && !wasteData) {
        setBackendSavings(null)
        return
      }

      const totalSavingsInr =
        (elecData?.estimated_cost_savings_inr || 0) +
        (transData?.estimated_cost_savings_inr || 0) +
        (wasteData?.estimated_cost_savings_inr || 0)

      const baselineElec = Number(elecData?.baseline?.emissions_kg || 0)
      const baselineTrans = Number(transData?.baseline?.emissions_kg || 0)
      const baselineWaste = Number(wasteData?.baseline?.emissions_kg || 0)
      const totalBaselineEmissions = baselineElec + baselineTrans + baselineWaste

      const diffElec = Number(elecData?.estimated_emissions_reduction_kg || 0)
      const diffTrans = Number(transData?.estimated_emissions_reduction_kg || 0)
      const diffWaste = Number(wasteData?.estimated_emissions_reduction_kg || 0)
      const totalReduction = diffElec + diffTrans + diffWaste

      const proposed = Math.max(0, totalBaselineEmissions - totalReduction)
      const improvementPct =
        totalBaselineEmissions > 0
          ? Math.round((totalReduction / totalBaselineEmissions) * 100)
          : clientFallback.emissionsImprovementPercent

      const elecBaselineKwh = Number(elecData?.baseline?.consumption_kwh || 0)
      const hasElecRecords = Boolean(
        elecData && (elecData.baseline?.has_records === true || elecBaselineKwh > 0)
      )

      const transBaselineKm = Number(transData?.baseline?.distance_km || 0)
      const hasTransRecords = Boolean(
        transData && (transData.baseline?.has_records === true || transBaselineKm > 0)
      )

      const wasteBaselineKg = Number(wasteData?.baseline?.quantity_kg || 0)
      const hasWasteRecords = Boolean(
        wasteData && (wasteData.baseline?.has_records === true || wasteBaselineKg > 0)
      )

      const kwhCut = Number(elecData?.difference?.kwh_reduction || 0)
      const wasteCut = Number(
        wasteData?.difference?.quantity_reduction_kg ??
        wasteData?.difference?.waste_kg_reduction ??
        0
      )

      const allAssumptions = [
        ...(elecData?.assumptions || []),
        ...(transData?.assumptions || []),
        ...(wasteData?.assumptions || []),
      ]

      setBackendSavings({
        savingsMonthly: Math.round(totalSavingsInr),
        emissionsImprovementPercent: improvementPct,
        currentEmissions: Math.round(totalBaselineEmissions),
        proposedEmissions: Math.round(proposed),
        projectedKwhReduction: kwhCut,
        projectedWasteReduction: wasteCut,
        baselineElectricityKwh: elecBaselineKwh,
        hasElecData: hasElecRecords,
        baselineTransportDistanceKm: transBaselineKm,
        hasTransData: hasTransRecords,
        baselineWasteKg: wasteBaselineKg,
        hasWasteData: hasWasteRecords,
        baselineWasteEmissions: baselineWaste,
        projectedWasteEmissionsReduction: diffWaste,
        assumptions: allAssumptions,
      })
    } catch {
      setBackendSavings(null)
    }
  }, [activeToken, elec, transport, wasteR, clientFallback.emissionsImprovementPercent])

  useEffect(() => {
    if (isAuth) {
      const timer = setTimeout(() => {
        runBackendSimulation()
      }, 150)
      return () => clearTimeout(timer)
    } else {
      setBackendSavings(null)
    }
  }, [isAuth, activeToken, elec, transport, wasteR, runBackendSimulation])

  const hasAnyBaselineRecords = Boolean(
    backendSavings &&
    (backendSavings.hasElecData ||
     backendSavings.hasTransData ||
     backendSavings.hasWasteData ||
     backendSavings.currentEmissions > 0)
  )

  const currentEmissionsDisplay = hasAnyBaselineRecords
    ? `${backendSavings!.currentEmissions.toLocaleString()} kg CO₂e`
    : isAuth
      ? '0 kg CO₂e (No baseline records logged)'
      : '2,480 kg CO₂e (Demo baseline)'

  const savingsMonthly = hasAnyBaselineRecords
    ? backendSavings!.savingsMonthly
    : isAuth
      ? 0
      : clientFallback.savingsMonthly

  const emissionsImprovementPercent = hasAnyBaselineRecords
    ? backendSavings!.emissionsImprovementPercent
    : isAuth
      ? 0
      : clientFallback.emissionsImprovementPercent

  const proposedEmissionsDisplay = hasAnyBaselineRecords
    ? `${backendSavings!.proposedEmissions.toLocaleString()} kg CO₂e`
    : isAuth
      ? '0 kg CO₂e'
      : `${clientFallback.proposedEmissions.toLocaleString()} kg CO₂e`

  // Dynamically compute projected kWh reduction using the baseline and current slider position
  const dynamicKwhReduction =
    backendSavings?.hasElecData && backendSavings.baselineElectricityKwh > 0
      ? Number(((backendSavings.baselineElectricityKwh * elec) / 100).toFixed(1))
      : backendSavings?.projectedKwhReduction ?? 0

  const projectedKwhReductionDisplay = hasAnyBaselineRecords
    ? backendSavings?.hasElecData && backendSavings.baselineElectricityKwh > 0
      ? `${dynamicKwhReduction.toLocaleString(undefined, { minimumFractionDigits: 0, maximumFractionDigits: 1 })} kWh`
      : 'No electricity records logged'
    : isAuth
      ? 'No electricity records logged'
      : `${clientFallback.projectedKwhReduction.toLocaleString()} kWh`

  // Dynamically compute projected waste reduction (mass avoided in kg) using the baseline and current slider position
  const dynamicWasteReduction =
    backendSavings?.hasWasteData && backendSavings.baselineWasteKg > 0
      ? Number(((backendSavings.baselineWasteKg * wasteR) / 100).toFixed(1))
      : backendSavings?.projectedWasteReduction ?? 0

  const projectedWasteReductionDisplay = hasAnyBaselineRecords
    ? backendSavings?.hasWasteData && backendSavings.baselineWasteKg > 0
      ? `${dynamicWasteReduction.toLocaleString(undefined, { minimumFractionDigits: 0, maximumFractionDigits: 1 })} kg`
      : 'No waste records logged'
    : isAuth
      ? 'No waste records logged'
      : `${clientFallback.projectedWasteReduction.toLocaleString()} kg`

  const sliders = [
    ['Electricity reduction', elec, setElec, 'Lower monthly kWh'],
    ['Transport distance reduction', transport, setTransport, 'Fewer route kilometres'],
    ['Waste reduction', wasteR, setWasteR, 'Less material generated'],
  ] as const

  const summaryRows = [
    ['Current estimated emissions', currentEmissionsDisplay],
    ['Proposed emissions', proposedEmissionsDisplay],
    ['Projected kWh reduction', projectedKwhReductionDisplay],
    ['Projected waste reduction', projectedWasteReductionDisplay],
  ]

  return (
    <div className="space-y-6">
      <PageTitle
        eyebrow="WHAT-IF PLANNING"
        title="Savings simulator"
        description="Test a scenario before you commit. These are projections, not measured outcomes."
        action={<Pill tone={isAuth ? 'green' : 'amber'}>{isAuth ? 'Grounded scenario' : 'Hypothetical scenario'}</Pill>}
      />

      <div className="grid gap-5 xl:grid-cols-[1fr_.8fr]">
        <Card className="p-5 sm:p-7 border border-[#E0E7DE] bg-white">
          <h2 className="text-base font-semibold text-[#244230]">Adjust your scenario</h2>
          <p className="mt-1 text-xs text-[#4E6254]">Move the sliders to model possible changes.</p>

          <div className="mt-8 space-y-7">
            {sliders.map(([label, val, setter, note]) => (
              <label key={label} className="block cursor-pointer">
                <div className="flex justify-between items-baseline text-sm font-medium">
                  <span className="text-[#2C4234] font-semibold">{label}</span>
                  <span className="text-base font-bold text-[#20513B] tabular-nums">{val}%</span>
                </div>
                <input
                  type="range"
                  min="0"
                  max="50"
                  value={val}
                  onChange={(e) => setter(Number(e.target.value))}
                  className="mt-3 w-full accent-[#285943]"
                  aria-label={label}
                />
                <div className="mt-2 flex justify-between text-xs font-medium text-[#4A5E50]">
                  <span>0%</span>
                  <span className="text-[#3D5244] font-normal">{note}</span>
                  <span>50%</span>
                </div>
              </label>
            ))}
          </div>
        </Card>

        <div className="space-y-4">
          <Card className="p-6 border border-[#D8E4D5] bg-white shadow-xs">
            <div className="flex items-center justify-between">
              <p className="text-xs font-semibold uppercase tracking-[.12em] text-[#4A6252]">
                Projected monthly opportunity
              </p>
              <span className="inline-flex items-center rounded-full bg-[#E7F1E5] px-2.5 py-0.5 text-[11px] font-semibold text-[#285943]">
                {backendSavings ? 'Backend Calculated' : 'Estimated'}
              </span>
            </div>

            <p className="mt-3 text-4xl font-bold tracking-[-.05em] text-[#285943] sm:text-[42px] leading-tight tabular-nums">
              ₹{savingsMonthly.toLocaleString('en-IN')}
            </p>

            <p className="mt-2 text-xs font-medium text-[#4D6354]">
              Estimated cost difference under this scenario
            </p>

            <div className="mt-5 space-y-2">
              <div className="h-2.5 w-full overflow-hidden rounded-full bg-[#E5ECE3]">
                <div
                  className="h-full rounded-full bg-[#285943] transition-all duration-300"
                  style={{
                    width: `${Math.min(100, Math.max(0, emissionsImprovementPercent * 2))}%`,
                  }}
                />
              </div>
              <div className="flex justify-between items-center text-xs">
                <span className="font-semibold text-[#285943]">
                  {emissionsImprovementPercent}% modeled emissions improvement
                </span>
                <span className="text-[#526857] font-medium">Target: 50%</span>
              </div>
            </div>
          </Card>

          <Card className="p-5 sm:p-6 border border-[#E0E7DE] bg-white">
            <h2 className="text-sm font-semibold tracking-[-0.01em] text-[#244230]">
              Scenario summary
            </h2>
            <div className="mt-4 space-y-3.5 text-xs">
              {summaryRows.map(([k, v]) => (
                <div
                  key={k}
                  className="flex items-center justify-between border-b border-[#E8EFE6] pb-3 last:border-0 last:pb-0"
                >
                  <span className="font-medium text-[#465B4D]">{k}</span>
                  <span className="font-semibold text-[#1F3D2C] tabular-nums text-right">{v}</span>
                </div>
              ))}
            </div>
            {backendSavings?.hasWasteData && backendSavings.projectedWasteEmissionsReduction > 0 && (
              <div className="mt-3.5 pt-3 border-t border-[#E8EFE6] flex items-center justify-between text-xs text-[#4E6254]">
                <span className="font-medium">Waste emissions avoided</span>
                <span className="font-semibold text-[#20513B] tabular-nums">
                  {backendSavings.projectedWasteEmissionsReduction.toLocaleString()} kg CO₂e
                </span>
              </div>
            )}
          </Card>
        </div>
      </div>

      <div className="rounded-xl border border-[#DDD5A8] bg-[#FAF6E4] px-4 py-3 text-xs leading-5 text-[#4A4322]">
        <span className="font-semibold text-[#2D2810]">Important:</span> this simulator applies
        verified backend algorithms to model hypothetical interventions. A projected improvement is
        an actionable target and not proof of an already achieved reduction.
      </div>
    </div>
  )
}
