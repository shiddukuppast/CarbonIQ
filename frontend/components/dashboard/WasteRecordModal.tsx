'use client'

import React, { useEffect, useState } from 'react'
import { Calculator, Recycle, X } from 'lucide-react'
import { Button } from '@/components/ui/button'
import { calculateWasteEmissions, EMISSION_FACTORS } from '@/lib/calculations'
import type { WasteCategory, WasteRecord, WasteTreatmentMethod } from '@/types/sustainability'

export interface WasteRecordModalProps {
  isOpen: boolean
  onClose: () => void
  onSave: (record: Omit<WasteRecord, 'id' | 'createdAt'>, existingId?: string) => void
  initialRecord?: WasteRecord | null
}

export function WasteRecordModal({
  isOpen,
  onClose,
  onSave,
  initialRecord,
}: WasteRecordModalProps) {
  const [date, setDate] = useState('2026-10-28')
  const [category, setCategory] = useState<WasteCategory>('Recyclable')
  const [quantityKg, setQuantityKg] = useState<string>('84')
  const [treatmentMethod, setTreatmentMethod] = useState<WasteTreatmentMethod>('Recycling')
  const [buildingOrDepartment, setBuildingOrDepartment] = useState('')
  const [collectionProvider, setCollectionProvider] = useState('')
  const [disposalCostInr, setDisposalCostInr] = useState<string>('')
  const [notes, setNotes] = useState('')
  const [error, setError] = useState<string | null>(null)

  useEffect(() => {
    if (initialRecord) {
      setDate(initialRecord.date)
      setCategory(initialRecord.category)
      setQuantityKg(String(initialRecord.quantityKg))
      setTreatmentMethod(initialRecord.treatmentMethod || 'Recycling')
      setBuildingOrDepartment(initialRecord.buildingOrDepartment || '')
      setCollectionProvider(initialRecord.collectionProvider || '')
      setDisposalCostInr(
        initialRecord.disposalCostInr ? String(initialRecord.disposalCostInr) : ''
      )
      setNotes(initialRecord.notes || '')
    } else {
      setDate('2026-10-28')
      setCategory('Recyclable')
      setQuantityKg('')
      setTreatmentMethod('Recycling')
      setBuildingOrDepartment('')
      setCollectionProvider('')
      setDisposalCostInr('')
      setNotes('')
    }
    setError(null)
  }, [initialRecord, isOpen])

  if (!isOpen) return null

  const parsedQty = parseFloat(quantityKg) || 0
  const liveEmissions = calculateWasteEmissions(parsedQty, treatmentMethod)
  const isNetAvoided = liveEmissions < 0

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault()
    setError(null)

    if (!date.trim()) {
      setError('Please select a valid record date.')
      return
    }

    if (isNaN(parsedQty) || parsedQty <= 0) {
      setError('Please enter a valid waste quantity greater than 0 kg.')
      return
    }

    const cost = disposalCostInr.trim() ? parseFloat(disposalCostInr) : undefined

    onSave(
      {
        date: date.trim(),
        category,
        quantityKg: parsedQty,
        treatmentMethod,
        buildingOrDepartment: buildingOrDepartment.trim() || undefined,
        collectionProvider: collectionProvider.trim() || undefined,
        disposalCostInr: cost && !isNaN(cost) ? cost : undefined,
        notes: notes.trim() || undefined,
        calculatedEmissionsKg: liveEmissions,
        emissionFactorUsed: EMISSION_FACTORS.waste[treatmentMethod],
        status: 'Verified',
      },
      initialRecord?.id
    )

    onClose()
  }

  return (
    <div
      role="dialog"
      aria-modal="true"
      aria-labelledby="waste-modal-title"
      className="fixed inset-0 z-50 flex items-center justify-center bg-[#234A36]/40 p-4 backdrop-blur-xs animate-in fade-in duration-200"
    >
      <div className="relative w-full max-w-lg max-h-[90vh] overflow-y-auto rounded-2xl border border-[#E0E7DE] bg-white p-6 shadow-2xl sm:p-7">
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
            <Recycle size={19} />
          </span>
          <div>
            <h2 id="waste-modal-title" className="text-lg font-semibold text-[#28352D]">
              {initialRecord ? 'Edit Waste Record' : 'Add Waste Entry'}
            </h2>
            <p className="text-xs text-[#8A978D]">Record material stream, weight, and recovery route</p>
          </div>
        </div>

        <form onSubmit={handleSubmit} className="mt-6 space-y-4">
          <div className="grid gap-4 sm:grid-cols-2">
            <label className="block text-xs font-medium text-[#4D6054]">
              Date / Period <span className="text-[#A35C49]">*</span>
              <input
                type="date"
                value={date}
                onChange={(e) => setDate(e.target.value)}
                className="mt-1 w-full rounded-xl border border-[#DCE4DA] bg-[#FBFDFB] px-3 py-2 text-xs text-[#28352D] outline-none focus:border-[#285943]"
                required
              />
            </label>

            <label className="block text-xs font-medium text-[#4D6054]">
              Quantity (kg) <span className="text-[#A35C49]">*</span>
              <input
                type="number"
                step="any"
                min="0.5"
                placeholder="e.g., 84"
                value={quantityKg}
                onChange={(e) => setQuantityKg(e.target.value)}
                className="mt-1 w-full rounded-xl border border-[#DCE4DA] bg-[#FBFDFB] px-3 py-2 text-xs text-[#28352D] outline-none focus:border-[#285943]"
                required
              />
            </label>
          </div>

          <div className="grid gap-4 sm:grid-cols-2">
            <label className="block text-xs font-medium text-[#4D6054]">
              Waste Category <span className="text-[#A35C49]">*</span>
              <select
                value={category}
                onChange={(e) => {
                  const cat = e.target.value as WasteCategory
                  setCategory(cat)
                  if (cat === 'Biodegradable') setTreatmentMethod('Composting')
                  else if (cat === 'Recyclable') setTreatmentMethod('Recycling')
                  else if (cat === 'General') setTreatmentMethod('Landfill')
                  else if (cat === 'E-waste') setTreatmentMethod('Recycling')
                }}
                className="mt-1 w-full rounded-xl border border-[#DCE4DA] bg-[#FBFDFB] px-3 py-2 text-xs text-[#28352D] outline-none focus:border-[#285943] cursor-pointer"
              >
                <option value="Biodegradable">Biodegradable / Organic</option>
                <option value="Recyclable">Recyclable (Paper, Plastic, Metal)</option>
                <option value="General">General / Non-recyclable</option>
                <option value="E-waste">E-waste</option>
              </select>
            </label>

            <label className="block text-xs font-medium text-[#4D6054]">
              Treatment / Disposal Method
              <select
                value={treatmentMethod}
                onChange={(e) => setTreatmentMethod(e.target.value as WasteTreatmentMethod)}
                className="mt-1 w-full rounded-xl border border-[#DCE4DA] bg-[#FBFDFB] px-3 py-2 text-xs text-[#28352D] outline-none focus:border-[#285943] cursor-pointer"
              >
                <option value="Composting">Composting</option>
                <option value="Recycling">Recycling</option>
                <option value="Landfill">Landfill</option>
                <option value="Incineration">Incineration</option>
                <option value="Other / Unknown">Other / Unknown</option>
              </select>
            </label>
          </div>

          <div className="grid gap-4 sm:grid-cols-2">
            <label className="block text-xs font-medium text-[#4D6054]">
              Building / Department{' '}
              <span className="text-xs text-[#8A978D] font-normal">(optional)</span>
              <input
                type="text"
                placeholder="e.g., Dining Hall & Canteen"
                value={buildingOrDepartment}
                onChange={(e) => setBuildingOrDepartment(e.target.value)}
                className="mt-1 w-full rounded-xl border border-[#DCE4DA] bg-[#FBFDFB] px-3 py-2 text-xs text-[#28352D] outline-none focus:border-[#285943]"
              />
            </label>

            <label className="block text-xs font-medium text-[#4D6054]">
              Collection Provider{' '}
              <span className="text-xs text-[#8A978D] font-normal">(optional)</span>
              <input
                type="text"
                placeholder="e.g., GreenRecycle Pvt Ltd"
                value={collectionProvider}
                onChange={(e) => setCollectionProvider(e.target.value)}
                className="mt-1 w-full rounded-xl border border-[#DCE4DA] bg-[#FBFDFB] px-3 py-2 text-xs text-[#28352D] outline-none focus:border-[#285943]"
              />
            </label>
          </div>

          <div className="grid gap-4 sm:grid-cols-2">
            <label className="block text-xs font-medium text-[#4D6054]">
              Disposal Cost (₹){' '}
              <span className="text-xs text-[#8A978D] font-normal">(optional)</span>
              <input
                type="number"
                step="any"
                min="0"
                placeholder="e.g., 650"
                value={disposalCostInr}
                onChange={(e) => setDisposalCostInr(e.target.value)}
                className="mt-1 w-full rounded-xl border border-[#DCE4DA] bg-[#FBFDFB] px-3 py-2 text-xs text-[#28352D] outline-none focus:border-[#285943]"
              />
            </label>

            <label className="block text-xs font-medium text-[#4D6054]">
              Notes{' '}
              <span className="text-xs text-[#8A978D] font-normal">(optional)</span>
              <input
                type="text"
                placeholder="e.g., Segregated bins from library"
                value={notes}
                onChange={(e) => setNotes(e.target.value)}
                className="mt-1 w-full rounded-xl border border-[#DCE4DA] bg-[#FBFDFB] px-3 py-2 text-xs text-[#28352D] outline-none focus:border-[#285943]"
              />
            </label>
          </div>

          {/* Live Emissions Calculation Box */}
          <div className="rounded-xl border border-[#DCE8DA] bg-[#F6FBF4] p-3 text-xs text-[#355240]">
            <div className="flex items-center justify-between">
              <span className="flex items-center gap-1.5 font-semibold text-[#285943]">
                <Calculator size={14} /> Calculated Emissions:
              </span>
              <span
                className={`text-sm font-bold ${
                  isNetAvoided ? 'text-[#367954]' : 'text-[#285943]'
                }`}
              >
                {liveEmissions > 0 ? `+${liveEmissions}` : liveEmissions} kg CO₂e
              </span>
            </div>
            <p className="mt-1 text-[11px] text-[#718577]">
              Treatment method factor: {EMISSION_FACTORS.waste[treatmentMethod]} kg CO₂e/kg{' '}
              {isNetAvoided ? '(Net avoided emissions credit via recycling)' : '(Anaerobic / processing factor)'}.
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
