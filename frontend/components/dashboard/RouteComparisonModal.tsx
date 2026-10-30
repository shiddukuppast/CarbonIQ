'use client'

import React from 'react'
import {
  AlertTriangle,
  ArrowRight,
  Bus,
  CheckCircle2,
  FileCheck,
  ShieldAlert,
  Sparkles,
  X,
} from 'lucide-react'
import { Button } from '@/components/ui/button'
import { Pill } from '@/components/ui/Pill'
import type { RouteOptimizationProposal } from '@/types/sustainability'

export interface RouteComparisonModalProps {
  proposal: RouteOptimizationProposal | null
  isOpen: boolean
  onClose: () => void
  onAccept: (proposalId: string) => void
  onReject: (proposalId: string) => void
}

export function RouteComparisonModal({
  proposal,
  isOpen,
  onClose,
  onAccept,
  onReject,
}: RouteComparisonModalProps) {
  if (!isOpen || !proposal) return null

  const isAccepted = proposal.status === 'accepted'

  return (
    <div
      role="dialog"
      aria-modal="true"
      aria-labelledby="comparison-modal-title"
      className="fixed inset-0 z-50 flex items-center justify-center bg-[#234A36]/40 p-4 backdrop-blur-xs animate-in fade-in duration-200"
    >
      <div className="relative w-full max-w-3xl max-h-[92vh] overflow-y-auto rounded-2xl border border-[#E0E7DE] bg-white p-6 shadow-2xl sm:p-8">
        <button
          type="button"
          onClick={onClose}
          aria-label="Close dialog"
          className="absolute right-4 top-4 rounded-lg p-1.5 text-[#7A887D] hover:bg-[#F3F7F1] hover:text-[#285943] cursor-pointer"
        >
          <X size={18} />
        </button>

        <div className="flex items-center gap-3">
          <span className="grid h-10 w-10 place-items-center rounded-xl bg-[#285943] text-white">
            <Sparkles size={18} />
          </span>
          <div>
            <div className="flex items-center gap-2">
              <h2 id="comparison-modal-title" className="text-xl font-semibold text-[#28352D]">
                {proposal.title}
              </h2>
              <Pill tone={proposal.feasibility === 'High' ? 'green' : 'amber'}>
                {proposal.feasibility} Feasibility
              </Pill>
            </div>
            <p className="mt-0.5 text-xs text-[#8A978D]">
              AI-Assisted Corridor Consolidation & Passenger Balancing
            </p>
          </div>
        </div>

        {/* Reason summary */}
        <div className="mt-5 rounded-xl border border-[#DCE7DA] bg-[#F7FAF5] p-4 text-xs leading-5 text-[#354B3E]">
          <p className="font-semibold text-[#285943]">Why this recommendation was generated:</p>
          <p className="mt-1">{proposal.reason}</p>
        </div>

        {/* Side-by-Side Comparison Table */}
        <div className="mt-6 overflow-hidden rounded-xl border border-[#E0E7DE]">
          <div className="grid grid-cols-2 divide-x divide-[#E0E7DE] bg-[#F2F6F0] p-3 text-xs font-semibold text-[#304739]">
            <div className="flex items-center gap-2">
              <span className="h-2 w-2 rounded-full bg-[#A35C49]" />
              <span>Current Route Configuration</span>
            </div>
            <div className="flex items-center gap-2 pl-3">
              <span className="h-2 w-2 rounded-full bg-[#285943]" />
              <span>Proposed Consolidated Route</span>
            </div>
          </div>

          <div className="divide-y divide-[#EEF2ED] text-xs">
            {/* Number of Buses */}
            <div className="grid grid-cols-2 divide-x divide-[#E0E7DE] p-3">
              <div>
                <p className="text-[10px] text-[#8A978D]">Buses Deployed</p>
                <p className="mt-1 font-semibold text-[#445649]">
                  {proposal.currentConfig.busesCount} independent buses
                </p>
                <p className="text-[11px] text-[#78897C]">
                  {proposal.currentConfig.routeNames.join(' + ')}
                </p>
              </div>
              <div className="pl-3 bg-[#FAFCF8]">
                <p className="text-[10px] text-[#8A978D]">Buses Deployed</p>
                <p className="mt-1 font-semibold text-[#285943]">
                  {proposal.proposedConfig.busesCount} optimized bus
                </p>
                <p className="text-[11px] text-[#4A8561]">
                  1 high-capacity 40-seat coach
                </p>
              </div>
            </div>

            {/* Students Served */}
            <div className="grid grid-cols-2 divide-x divide-[#E0E7DE] p-3">
              <div>
                <p className="text-[10px] text-[#8A978D]">Students Accommodated</p>
                <p className="mt-1 font-semibold text-[#445649]">
                  {proposal.currentConfig.studentsServed} students across 2 routes
                </p>
              </div>
              <div className="pl-3 bg-[#FAFCF8]">
                <p className="text-[10px] text-[#8A978D]">Students Accommodated</p>
                <p className="mt-1 font-semibold text-[#285943]">
                  {proposal.proposedConfig.studentsServed} students (100% accommodated)
                </p>
              </div>
            </div>

            {/* Total Distance */}
            <div className="grid grid-cols-2 divide-x divide-[#E0E7DE] p-3">
              <div>
                <p className="text-[10px] text-[#8A978D]">Daily Distance</p>
                <p className="mt-1 font-semibold text-[#445649]">
                  {proposal.currentConfig.totalDistanceKm} km / day
                </p>
              </div>
              <div className="pl-3 bg-[#FAFCF8]">
                <p className="text-[10px] text-[#8A978D]">Daily Distance</p>
                <p className="mt-1 font-semibold text-[#285943]">
                  {proposal.proposedConfig.totalDistanceKm} km / day
                </p>
                <span className="inline-block mt-0.5 rounded bg-[#E3EFE0] px-1.5 py-0.5 text-[10px] font-semibold text-[#285943]">
                  -{proposal.estimatedDistanceReductionKm} km/run reduction
                </span>
              </div>
            </div>

            {/* Fuel Consumption */}
            <div className="grid grid-cols-2 divide-x divide-[#E0E7DE] p-3">
              <div>
                <p className="text-[10px] text-[#8A978D]">Daily Fuel Use</p>
                <p className="mt-1 font-semibold text-[#445649]">
                  {proposal.currentConfig.dailyFuelConsumptionLiters} L / day
                </p>
              </div>
              <div className="pl-3 bg-[#FAFCF8]">
                <p className="text-[10px] text-[#8A978D]">Daily Fuel Use</p>
                <p className="mt-1 font-semibold text-[#285943]">
                  {proposal.proposedConfig.dailyFuelConsumptionLiters} L / day
                </p>
              </div>
            </div>

            {/* Monthly Cost & Emissions */}
            <div className="grid grid-cols-2 divide-x divide-[#E0E7DE] p-3">
              <div>
                <p className="text-[10px] text-[#8A978D]">Monthly Fuel Cost & Emissions</p>
                <p className="mt-1 font-semibold text-[#445649]">
                  ₹{proposal.currentConfig.monthlyFuelCostInr.toLocaleString('en-IN')} / mo
                </p>
                <p className="text-[11px] text-[#718275]">
                  {proposal.currentConfig.monthlyEmissionsKg.toLocaleString()} kg CO₂e / mo
                </p>
              </div>
              <div className="pl-3 bg-[#FAFCF8]">
                <p className="text-[10px] text-[#8A978D]">Estimated Savings</p>
                <p className="mt-1 font-semibold text-[#285943]">
                  ₹{proposal.estimatedMonthlySavingsInr.toLocaleString('en-IN')} / mo saved
                </p>
                <p className="text-[11px] text-[#285943] font-medium">
                  -{proposal.estimatedEmissionsReductionKg.toLocaleString()} kg CO₂e avoided
                </p>
              </div>
            </div>
          </div>
        </div>

        {/* Required Validations Box */}
        <div className="mt-5 rounded-xl border border-[#E9E5D4] bg-[#FDFBF3] p-4 text-xs text-[#7A6B3D]">
          <div className="flex items-center gap-2 font-semibold">
            <AlertTriangle size={15} />
            <span>Pre-Implementation Validation Checklist:</span>
          </div>
          <ul className="mt-2 list-disc pl-5 space-y-1 text-[11px] leading-relaxed">
            {proposal.requiredValidation.map((val, idx) => (
              <li key={idx}>{val}</li>
            ))}
          </ul>
          <p className="mt-3 text-[10px] text-[#8E8055] italic">
            Note: "Accept for Planning" records this route proposal as an active planned intervention.
            Actual route timings must be verified with transport staff before changing schedules.
          </p>
        </div>

        {/* Action Buttons */}
        <div className="mt-6 flex flex-wrap items-center justify-between gap-3 border-t border-[#EEF2EC] pt-4">
          <Button type="button" variant="ghost" onClick={onClose}>
            Close
          </Button>

          <div className="flex items-center gap-2.5">
            <Button
              type="button"
              variant="secondary"
              onClick={() => {
                onReject(proposal.id)
                onClose()
              }}
              className="text-[#994734] hover:bg-[#FDF2F0]"
            >
              Reject Recommendation
            </Button>

            <Button
              type="button"
              onClick={() => {
                onAccept(proposal.id)
                onClose()
              }}
              disabled={isAccepted}
              className={isAccepted ? 'bg-[#5F7567] text-white' : ''}
            >
              {isAccepted ? (
                <>
                  <CheckCircle2 size={15} /> Accepted for Planning
                </>
              ) : (
                <>
                  <FileCheck size={15} /> Accept for Planning
                </>
              )}
            </Button>
          </div>
        </div>
      </div>
    </div>
  )
}
