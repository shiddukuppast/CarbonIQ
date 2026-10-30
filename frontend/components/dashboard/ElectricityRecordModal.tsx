'use client'

import React, { useEffect, useState } from 'react'
import { Calculator, X, Zap } from 'lucide-react'
import { Button } from '@/components/ui/button'
import { Pill } from '@/components/ui/Pill'
import { calculateElectricityEmissions, EMISSION_FACTORS } from '@/lib/calculations'
import type { ElectricityRecord } from '@/types/sustainability'

export interface ElectricityRecordModalProps {
  isOpen: boolean
  onClose: () => void
  onSave: (record: Omit<ElectricityRecord, 'id' | 'createdAt'>, existingId?: string) => void
  initialRecord?: ElectricityRecord | null
}

export function ElectricityRecordModal({
  isOpen,
  onClose,
  onSave,
  initialRecord,
}: ElectricityRecordModalProps) {
  const [reportingMonth, setReportingMonth] = useState('2026-10')
  const [consumptionKwh, setConsumptionKwh] = useState<string>('1240')
  const [source, setSource] = useState<string>('Grid')
  const [billAmountInr, setBillAmountInr] = useState<string>('10500')
  const [buildingOrDepartment, setBuildingOrDepartment] = useState('')
  const [notes, setNotes] = useState('')
  const [error, setError] = useState<string | null>(null)

  useEffect(() => {
    if (initialRecord) {
      setReportingMonth(initialRecord.reportingMonth)
      setConsumptionKwh(String(initialRecord.consumptionKwh))
      setSource(initialRecord.source || 'Grid')
      setBillAmountInr(initialRecord.billAmountInr ? String(initialRecord.billAmountInr) : '')
      setBuildingOrDepartment(initialRecord.buildingOrDepartment || '')
      setNotes(initialRecord.notes || '')
    } else {
      setReportingMonth('2026-10')
      setConsumptionKwh('')
      setSource('Grid')
      setBillAmountInr('')
      setBuildingOrDepartment('')
      setNotes('')
    }
    setError(null)
  }, [initialRecord, isOpen])

  if (!isOpen) return null

  const parsedKwh = parseFloat(consumptionKwh) || 0
  const liveEmissionsKg = calculateElectricityEmissions(parsedKwh)

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault()
    setError(null)

    if (!reportingMonth.trim()) {
      setError('Please select a valid reporting month.')
      return
    }

    if (isNaN(parsedKwh) || parsedKwh <= 0) {
      setError('Please enter a valid electricity consumption value greater than 0 kWh.')
      return
    }

    const bill = billAmountInr.trim() ? parseFloat(billAmountInr) : undefined

    onSave(
      {
        reportingMonth: reportingMonth.trim(),
        consumptionKwh: parsedKwh,
        source,
        billAmountInr: bill && !isNaN(bill) ? bill : undefined,
        buildingOrDepartment: buildingOrDepartment.trim() || undefined,
        notes: notes.trim() || undefined,
        calculatedEmissionsKg: source === 'Solar Rooftop' ? 0 : liveEmissionsKg,
        emissionFactorUsed: source === 'Solar Rooftop' ? 0.0 : EMISSION_FACTORS.electricityGrid,
        factorType: source === 'Solar Rooftop' ? 'solar_rooftop_zero' : 'illustrative_grid_factor',
      },
      initialRecord?.id
    )

    onClose()
  }

  return (
    <div
      role="dialog"
      aria-modal="true"
      aria-labelledby="electricity-modal-title"
      className="fixed inset-0 z-50 flex items-center justify-center bg-[#234A36]/40 p-4 backdrop-blur-xs animate-in fade-in duration-200"
    >
      <div className="relative w-full max-w-lg rounded-2xl border border-[#E0E7DE] bg-white p-6 shadow-2xl sm:p-7">
        <button
          type="button"
          onClick={onClose}
          aria-label="Close dialog"
          className="absolute right-4 top-4 rounded-lg p-1.5 text-[#7A887D] hover:bg-[#F3F7F1] hover:text-[#285943] cursor-pointer"
        >
          <X size={18} />
        </button>

        <div className="flex items-center gap-3">
          <span className="grid h-10 w-10 place-items-center rounded-xl bg-[#E7F1E5] text-[#285943]">
            <Zap size={19} />
          </span>
          <div>
            <h2 id="electricity-modal-title" className="text-lg font-semibold text-[#28352D]">
              {initialRecord ? 'Edit Electricity Record' : 'Add Electricity Record'}
            </h2>
            <p className="text-xs text-[#8A978D]">Record monthly kilowatt-hour consumption</p>
          </div>
        </div>

        <form onSubmit={handleSubmit} className="mt-6 space-y-4">
          <div className="grid gap-4 sm:grid-cols-2">
            <label className="block text-xs font-medium text-[#4D6054]">
              Reporting month <span className="text-[#A35C49]">*</span>
              <input
                type="month"
                value={reportingMonth}
                onChange={(e) => setReportingMonth(e.target.value)}
                className="mt-1 w-full rounded-xl border border-[#DCE4DA] bg-[#FBFDFB] px-3 py-2 text-xs text-[#28352D] outline-none focus:border-[#285943]"
                required
              />
            </label>

            <label className="block text-xs font-medium text-[#4D6054]">
              Electricity source
              <select
                value={source}
                onChange={(e) => setSource(e.target.value)}
                className="mt-1 w-full rounded-xl border border-[#DCE4DA] bg-[#FBFDFB] px-3 py-2 text-xs text-[#28352D] outline-none focus:border-[#285943]"
              >
                <option value="Grid">Grid Electricity (CEA Baseline)</option>
                <option value="Solar Rooftop">Solar Rooftop (Zero direct emissions)</option>
              </select>
            </label>
          </div>

          <div className="grid gap-4 sm:grid-cols-2">
            <label className="block text-xs font-medium text-[#4D6054]">
              Consumption (kWh) <span className="text-[#A35C49]">*</span>
              <input
                type="number"
                step="any"
                min="1"
                placeholder="e.g., 1240"
                value={consumptionKwh}
                onChange={(e) => setConsumptionKwh(e.target.value)}
                className="mt-1 w-full rounded-xl border border-[#DCE4DA] bg-[#FBFDFB] px-3 py-2 text-xs text-[#28352D] outline-none focus:border-[#285943]"
                required
              />
            </label>

            <label className="block text-xs font-medium text-[#4D6054]">
              Bill amount (₹) <span className="text-xs text-[#8A978D] font-normal">(optional)</span>
              <input
                type="number"
                step="any"
                min="0"
                placeholder="e.g., 10500"
                value={billAmountInr}
                onChange={(e) => setBillAmountInr(e.target.value)}
                className="mt-1 w-full rounded-xl border border-[#DCE4DA] bg-[#FBFDFB] px-3 py-2 text-xs text-[#28352D] outline-none focus:border-[#285943]"
              />
            </label>
          </div>

          <label className="block text-xs font-medium text-[#4D6054]">
            Building / Department{' '}
            <span className="text-xs text-[#8A978D] font-normal">(optional)</span>
            <input
              type="text"
              placeholder="e.g., Science Block B"
              value={buildingOrDepartment}
              onChange={(e) => setBuildingOrDepartment(e.target.value)}
              className="mt-1 w-full rounded-xl border border-[#DCE4DA] bg-[#FBFDFB] px-3 py-2 text-xs text-[#28352D] outline-none focus:border-[#285943]"
            />
          </label>

          <label className="block text-xs font-medium text-[#4D6054]">
            Notes & Meter Details{' '}
            <span className="text-xs text-[#8A978D] font-normal">(optional)</span>
            <input
              type="text"
              placeholder="e.g., Main sub-station meter reading"
              value={notes}
              onChange={(e) => setNotes(e.target.value)}
              className="mt-1 w-full rounded-xl border border-[#DCE4DA] bg-[#FBFDFB] px-3 py-2 text-xs text-[#28352D] outline-none focus:border-[#285943]"
            />
          </label>

          {/* Live Emissions Calculation Box */}
          <div className="rounded-xl border border-[#DCE8DA] bg-[#F6FBF4] p-3 text-xs text-[#355240]">
            <div className="flex items-center justify-between">
              <span className="flex items-center gap-1.5 font-semibold text-[#285943]">
                <Calculator size={14} /> Live Calculated Emissions:
              </span>
              <span className="text-sm font-bold text-[#285943]">
                {liveEmissionsKg.toLocaleString()} kg CO₂e
              </span>
            </div>
            <p className="mt-1 text-[11px] text-[#718577]">
              Formula: {parsedKwh} kWh × {EMISSION_FACTORS.electricityGrid} kg CO₂e/kWh
              (Illustrative Indian Grid Factor).
            </p>
          </div>

          {error && (
            <p className="rounded-lg bg-[#FDF2F0] p-2.5 text-xs text-[#A35C49] animate-in fade-in">
              {error}
            </p>
          )}

          <div className="mt-6 flex justify-end gap-3 pt-3 border-t border-[#EEF2EC]">
            <Button type="button" variant="ghost" onClick={onClose}>
              Cancel
            </Button>
            <Button type="submit">
              {initialRecord ? 'Update Record' : 'Save Record'}
            </Button>
          </div>
        </form>
      </div>
    </div>
  )
}
