'use client'

import React, { useEffect, useState } from 'react'
import { BusFront, Calculator, X } from 'lucide-react'
import { Button } from '@/components/ui/button'
import { calculateTransportationEmissions } from '@/lib/calculations'
import type { FuelType, TransportationMode, TransportationRecord } from '@/types/sustainability'

export interface TransportationRecordModalProps {
  isOpen: boolean
  onClose: () => void
  onSave: (record: Omit<TransportationRecord, 'id' | 'createdAt'>, existingId?: string) => void
  initialRecord?: TransportationRecord | null
}

export function TransportationRecordModal({
  isOpen,
  onClose,
  onSave,
  initialRecord,
}: TransportationRecordModalProps) {
  const [date, setDate] = useState('2026-10-28')
  const [mode, setMode] = useState<TransportationMode>('Bus')
  const [distanceKm, setDistanceKm] = useState<string>('320')
  const [fuelType, setFuelType] = useState<FuelType>('Diesel')
  const [fuelConsumedLiters, setFuelConsumedLiters] = useState<string>('')
  const [fuelEfficiencyKmPerL, setFuelEfficiencyKmPerL] = useState<string>('5.5')
  const [fuelExpenditureInr, setFuelExpenditureInr] = useState<string>('')
  const [vehicleId, setVehicleId] = useState('')
  const [passengerCount, setPassengerCount] = useState<string>('')
  const [vehicleCapacity, setVehicleCapacity] = useState<string>('')
  const [routeName, setRouteName] = useState('')
  const [destination, setDestination] = useState('')
  const [notes, setNotes] = useState('')
  const [error, setError] = useState<string | null>(null)

  useEffect(() => {
    if (initialRecord) {
      setDate(initialRecord.date)
      setMode(initialRecord.mode)
      setDistanceKm(String(initialRecord.distanceKm))
      setFuelType(initialRecord.fuelType || 'Diesel')
      setFuelConsumedLiters(
        initialRecord.fuelConsumedLiters ? String(initialRecord.fuelConsumedLiters) : ''
      )
      setFuelEfficiencyKmPerL(
        initialRecord.fuelEfficiencyKmPerL ? String(initialRecord.fuelEfficiencyKmPerL) : ''
      )
      setFuelExpenditureInr(
        initialRecord.fuelExpenditureInr ? String(initialRecord.fuelExpenditureInr) : ''
      )
      setVehicleId(initialRecord.vehicleId || '')
      setPassengerCount(initialRecord.passengerCount ? String(initialRecord.passengerCount) : '')
      setVehicleCapacity(initialRecord.vehicleCapacity ? String(initialRecord.vehicleCapacity) : '')
      setRouteName(initialRecord.routeName || '')
      setDestination(initialRecord.destination || '')
      setNotes(initialRecord.notes || '')
    } else {
      setDate('2026-10-28')
      setMode('Bus')
      setDistanceKm('')
      setFuelType('Diesel')
      setFuelConsumedLiters('')
      setFuelEfficiencyKmPerL('5.5')
      setFuelExpenditureInr('')
      setVehicleId('')
      setPassengerCount('')
      setVehicleCapacity('')
      setRouteName('')
      setDestination('')
      setNotes('')
    }
    setError(null)
  }, [initialRecord, isOpen])

  if (!isOpen) return null

  const parsedDist = parseFloat(distanceKm) || 0
  const parsedFuel = fuelConsumedLiters.trim() ? parseFloat(fuelConsumedLiters) : undefined
  const parsedEff = fuelEfficiencyKmPerL.trim() ? parseFloat(fuelEfficiencyKmPerL) : undefined

  const calcResult = calculateTransportationEmissions({
    distanceKm: parsedDist,
    fuelType,
    fuelConsumedLiters: parsedFuel,
    fuelEfficiencyKmPerL: parsedEff,
  })

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault()
    setError(null)

    if (!date.trim()) {
      setError('Please select a valid record date.')
      return
    }

    if (isNaN(parsedDist) || parsedDist <= 0) {
      setError('Please enter a valid distance greater than 0 km.')
      return
    }

    const cost = fuelExpenditureInr.trim() ? parseFloat(fuelExpenditureInr) : undefined
    const passengers = passengerCount.trim() ? parseInt(passengerCount, 10) : undefined
    const capacity = vehicleCapacity.trim() ? parseInt(vehicleCapacity, 10) : undefined

    onSave(
      {
        date: date.trim(),
        mode,
        distanceKm: parsedDist,
        fuelType,
        fuelConsumedLiters: parsedFuel,
        fuelEfficiencyKmPerL: parsedEff,
        fuelExpenditureInr: cost && !isNaN(cost) ? cost : undefined,
        vehicleId: vehicleId.trim() || undefined,
        passengerCount: passengers && !isNaN(passengers) ? passengers : undefined,
        vehicleCapacity: capacity && !isNaN(capacity) ? capacity : undefined,
        routeName: routeName.trim() || undefined,
        destination: destination.trim() || undefined,
        notes: notes.trim() || undefined,
        calculationMethod: calcResult.method,
        calculatedEmissionsKg: calcResult.emissionsKg,
      },
      initialRecord?.id
    )

    onClose()
  }

  return (
    <div
      role="dialog"
      aria-modal="true"
      aria-labelledby="transport-modal-title"
      className="fixed inset-0 z-50 flex items-center justify-center bg-[#234A36]/40 p-4 backdrop-blur-xs animate-in fade-in duration-200"
    >
      <div className="relative w-full max-w-xl max-h-[90vh] overflow-y-auto rounded-2xl border border-[#E0E7DE] bg-white p-6 shadow-2xl sm:p-7">
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
            <BusFront size={19} />
          </span>
          <div>
            <h2 id="transport-modal-title" className="text-lg font-semibold text-[#28352D]">
              {initialRecord ? 'Edit Travel Record' : 'Add Transportation Record'}
            </h2>
            <p className="text-xs text-[#8A978D]">
              Record vehicle distance, fleet runs, and fuel entries
            </p>
          </div>
        </div>

        <form onSubmit={handleSubmit} className="mt-6 space-y-4">
          <div className="grid gap-4 sm:grid-cols-3">
            <label className="block text-xs font-medium text-[#4D6054]">
              Date / Month <span className="text-[#A35C49]">*</span>
              <input
                type="date"
                value={date}
                onChange={(e) => setDate(e.target.value)}
                className="mt-1 w-full rounded-xl border border-[#DCE4DA] bg-[#FBFDFB] px-3 py-2 text-xs text-[#28352D] outline-none focus:border-[#285943]"
                required
              />
            </label>

            <label className="block text-xs font-medium text-[#4D6054]">
              Transport Mode <span className="text-[#A35C49]">*</span>
              <select
                value={mode}
                onChange={(e) => setMode(e.target.value as TransportationMode)}
                className="mt-1 w-full rounded-xl border border-[#DCE4DA] bg-[#FBFDFB] px-3 py-2 text-xs text-[#28352D] outline-none focus:border-[#285943] cursor-pointer"
              >
                <option value="Bus">Campus / Transit Bus</option>
                <option value="Fleet Van">Fleet Van</option>
                <option value="Car">Car / Cab</option>
                <option value="Two-Wheeler">Two-Wheeler</option>
                <option value="Public Transit">Public Transit</option>
              </select>
            </label>

            <label className="block text-xs font-medium text-[#4D6054]">
              Distance (km) <span className="text-[#A35C49]">*</span>
              <input
                type="number"
                step="any"
                min="0.1"
                placeholder="e.g., 320"
                value={distanceKm}
                onChange={(e) => setDistanceKm(e.target.value)}
                className="mt-1 w-full rounded-xl border border-[#DCE4DA] bg-[#FBFDFB] px-3 py-2 text-xs text-[#28352D] outline-none focus:border-[#285943]"
                required
              />
            </label>
          </div>

          <div className="rounded-xl border border-[#E7EFE4] bg-[#F9FCF8] p-4 space-y-4">
            <p className="text-xs font-semibold text-[#304739]">
              Fuel & Consumption Details <span className="text-[11px] font-normal text-[#7A8C80]">(enter actual litres OR efficiency)</span>
            </p>

            <div className="grid gap-4 sm:grid-cols-3">
              <label className="block text-xs font-medium text-[#4D6054]">
                Fuel Type
                <select
                  value={fuelType}
                  onChange={(e) => setFuelType(e.target.value as FuelType)}
                  className="mt-1 w-full rounded-xl border border-[#DCE4DA] bg-white px-3 py-2 text-xs text-[#28352D] outline-none focus:border-[#285943] cursor-pointer"
                >
                  <option value="Diesel">Diesel</option>
                  <option value="Petrol">Petrol</option>
                  <option value="CNG">CNG</option>
                  <option value="Electric">Electric</option>
                </select>
              </label>

              <label className="block text-xs font-medium text-[#4D6054]">
                Actual Fuel Consumed (L)
                <input
                  type="number"
                  step="any"
                  placeholder="e.g., 58"
                  value={fuelConsumedLiters}
                  onChange={(e) => setFuelConsumedLiters(e.target.value)}
                  className="mt-1 w-full rounded-xl border border-[#DCE4DA] bg-white px-3 py-2 text-xs text-[#28352D] outline-none focus:border-[#285943]"
                />
              </label>

              <label className="block text-xs font-medium text-[#4D6054]">
                Fuel Efficiency (km/L)
                <input
                  type="number"
                  step="any"
                  placeholder="e.g., 5.5"
                  value={fuelEfficiencyKmPerL}
                  onChange={(e) => setFuelEfficiencyKmPerL(e.target.value)}
                  className="mt-1 w-full rounded-xl border border-[#DCE4DA] bg-white px-3 py-2 text-xs text-[#28352D] outline-none focus:border-[#285943]"
                />
              </label>
            </div>
          </div>

          <div className="grid gap-4 sm:grid-cols-3">
            <label className="block text-xs font-medium text-[#4D6054]">
              Fuel Expenditure (₹)
              <input
                type="number"
                step="any"
                placeholder="e.g., 5500"
                value={fuelExpenditureInr}
                onChange={(e) => setFuelExpenditureInr(e.target.value)}
                className="mt-1 w-full rounded-xl border border-[#DCE4DA] bg-[#FBFDFB] px-3 py-2 text-xs text-[#28352D] outline-none focus:border-[#285943]"
              />
            </label>

            <label className="block text-xs font-medium text-[#4D6054]">
              Vehicle / Route ID
              <input
                type="text"
                placeholder="e.g., Bus #14 or KA-04-1234"
                value={vehicleId}
                onChange={(e) => setVehicleId(e.target.value)}
                className="mt-1 w-full rounded-xl border border-[#DCE4DA] bg-[#FBFDFB] px-3 py-2 text-xs text-[#28352D] outline-none focus:border-[#285943]"
              />
            </label>

            <label className="block text-xs font-medium text-[#4D6054]">
              Passengers on board
              <input
                type="number"
                placeholder="e.g., 28"
                value={passengerCount}
                onChange={(e) => setPassengerCount(e.target.value)}
                className="mt-1 w-full rounded-xl border border-[#DCE4DA] bg-[#FBFDFB] px-3 py-2 text-xs text-[#28352D] outline-none focus:border-[#285943]"
              />
            </label>
          </div>

          <label className="block text-xs font-medium text-[#4D6054]">
            Notes
            <input
              type="text"
              placeholder="e.g., Morning campus shift and return leg"
              value={notes}
              onChange={(e) => setNotes(e.target.value)}
              className="mt-1 w-full rounded-xl border border-[#DCE4DA] bg-[#FBFDFB] px-3 py-2 text-xs text-[#28352D] outline-none focus:border-[#285943]"
            />
          </label>

          {/* Live Emissions Calculation Box */}
          <div className="rounded-xl border border-[#DCE8DA] bg-[#F6FBF4] p-3.5 text-xs text-[#355240]">
            <div className="flex items-center justify-between">
              <span className="flex items-center gap-1.5 font-semibold text-[#285943]">
                <Calculator size={14} /> Calculated Emissions:
              </span>
              <span className="text-sm font-bold text-[#285943]">
                {calcResult.emissionsKg.toLocaleString()} kg CO₂e
              </span>
            </div>
            <p className="mt-1 text-[11px] leading-relaxed text-[#6E8274]">
              {calcResult.explanation}
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
