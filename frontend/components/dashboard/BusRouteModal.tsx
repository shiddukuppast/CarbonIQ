'use client'

import React, { useEffect, useState } from 'react'
import { Bus, MapPin, X } from 'lucide-react'
import { Button } from '@/components/ui/button'
import type { BusRoute } from '@/types/sustainability'

export interface BusRouteModalProps {
  isOpen: boolean
  onClose: () => void
  onSave: (route: Omit<BusRoute, 'id'>, existingId?: string) => void
  initialRoute?: BusRoute | null
}

export function BusRouteModal({
  isOpen,
  onClose,
  onSave,
  initialRoute,
}: BusRouteModalProps) {
  const [routeName, setRouteName] = useState('Route 14 — North Campus')
  const [startLocation, setStartLocation] = useState('Hebbal Junction')
  const [destination, setDestination] = useState('Main Campus')
  const [intermediateStops, setIntermediateStops] = useState('Yelahanka, Jakkur, Kogilu Cross')
  const [distanceKm, setDistanceKm] = useState('28')
  const [durationMinutes, setDurationMinutes] = useState('50')
  const [tripsPerDay, setTripsPerDay] = useState('2')
  const [operatingDaysPerWeek, setOperatingDaysPerWeek] = useState('5')
  const [assignedStudents, setAssignedStudents] = useState('26')
  const [busId, setBusId] = useState('BUS-04')
  const [fuelType, setFuelType] = useState<'Diesel' | 'CNG' | 'Electric'>('Diesel')
  const [fuelEfficiencyKmPerL, setFuelEfficiencyKmPerL] = useState('5.2')
  const [seatingCapacity, setSeatingCapacity] = useState('40')
  const [currentBusesCount, setCurrentBusesCount] = useState('1')
  const [notes, setNotes] = useState('')
  const [error, setError] = useState<string | null>(null)

  useEffect(() => {
    if (initialRoute) {
      setRouteName(initialRoute.routeName)
      setStartLocation(initialRoute.startLocation)
      setDestination(initialRoute.destination)
      setIntermediateStops(initialRoute.intermediateStops.join(', '))
      setDistanceKm(String(initialRoute.distanceKm))
      setDurationMinutes(String(initialRoute.durationMinutes))
      setTripsPerDay(String(initialRoute.tripsPerDay))
      setOperatingDaysPerWeek(String(initialRoute.operatingDaysPerWeek))
      setAssignedStudents(String(initialRoute.assignedStudents))
      setBusId(initialRoute.busId)
      setFuelType(initialRoute.fuelType)
      setFuelEfficiencyKmPerL(String(initialRoute.fuelEfficiencyKmPerL))
      setSeatingCapacity(String(initialRoute.seatingCapacity))
      setCurrentBusesCount(String(initialRoute.currentBusesCount))
      setNotes(initialRoute.notes || '')
    } else {
      setRouteName('')
      setStartLocation('')
      setDestination('Main Campus')
      setIntermediateStops('')
      setDistanceKm('')
      setDurationMinutes('45')
      setTripsPerDay('2')
      setOperatingDaysPerWeek('5')
      setAssignedStudents('')
      setBusId('BUS-NEW')
      setFuelType('Diesel')
      setFuelEfficiencyKmPerL('5.0')
      setSeatingCapacity('40')
      setCurrentBusesCount('1')
      setNotes('')
    }
    setError(null)
  }, [initialRoute, isOpen])

  if (!isOpen) return null

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault()
    setError(null)

    if (!routeName.trim() || !startLocation.trim() || !destination.trim()) {
      setError('Please provide Route Name, Starting Location, and Destination.')
      return
    }

    const dist = parseFloat(distanceKm)
    if (isNaN(dist) || dist <= 0) {
      setError('Please provide a valid route distance in kilometres.')
      return
    }

    const students = parseInt(assignedStudents, 10) || 0
    const capacity = parseInt(seatingCapacity, 10) || 40

    if (students > capacity) {
      setError(`Warning: Assigned students (${students}) exceeds the bus seating capacity (${capacity}).`)
      return
    }

    const stops = intermediateStops
      .split(',')
      .map((s) => s.trim())
      .filter(Boolean)

    onSave(
      {
        routeName: routeName.trim(),
        startLocation: startLocation.trim(),
        destination: destination.trim(),
        intermediateStops: stops,
        distanceKm: dist,
        durationMinutes: parseInt(durationMinutes, 10) || 45,
        tripsPerDay: parseInt(tripsPerDay, 10) || 2,
        operatingDaysPerWeek: parseInt(operatingDaysPerWeek, 10) || 5,
        assignedStudents: students,
        busId: busId.trim() || 'BUS-01',
        fuelType,
        fuelEfficiencyKmPerL: parseFloat(fuelEfficiencyKmPerL) || 5.0,
        seatingCapacity: capacity,
        currentBusesCount: parseInt(currentBusesCount, 10) || 1,
        status: initialRoute?.status || 'active',
        notes: notes.trim() || undefined,
      },
      initialRoute?.id
    )

    onClose()
  }

  return (
    <div
      role="dialog"
      aria-modal="true"
      aria-labelledby="route-modal-title"
      className="fixed inset-0 z-50 flex items-center justify-center bg-[#234A36]/40 p-4 backdrop-blur-xs animate-in fade-in duration-200"
    >
      <div className="relative w-full max-w-2xl max-h-[90vh] overflow-y-auto rounded-2xl border border-[#E0E7DE] bg-white p-6 shadow-2xl sm:p-7">
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
            <Bus size={19} />
          </span>
          <div>
            <h2 id="route-modal-title" className="text-lg font-semibold text-[#28352D]">
              {initialRoute ? 'Edit Bus Route' : 'Configure New Bus Route'}
            </h2>
            <p className="text-xs text-[#8A978D]">
              Define stops, distance, vehicle specs, and student allocation
            </p>
          </div>
        </div>

        <form onSubmit={handleSubmit} className="mt-6 space-y-4">
          <div className="grid gap-4 sm:grid-cols-2">
            <label className="block text-xs font-medium text-[#4D6054]">
              Route Name / Code <span className="text-[#A35C49]">*</span>
              <input
                type="text"
                placeholder="e.g., Route 12 — West Sector"
                value={routeName}
                onChange={(e) => setRouteName(e.target.value)}
                className="mt-1 w-full rounded-xl border border-[#DCE4DA] bg-[#FBFDFB] px-3 py-2 text-xs text-[#28352D] outline-none focus:border-[#285943]"
                required
              />
            </label>

            <label className="block text-xs font-medium text-[#4D6054]">
              Destination / Campus <span className="text-[#A35C49]">*</span>
              <input
                type="text"
                placeholder="e.g., Main Campus Gate 2"
                value={destination}
                onChange={(e) => setDestination(e.target.value)}
                className="mt-1 w-full rounded-xl border border-[#DCE4DA] bg-[#FBFDFB] px-3 py-2 text-xs text-[#28352D] outline-none focus:border-[#285943]"
                required
              />
            </label>
          </div>

          <div className="grid gap-4 sm:grid-cols-2">
            <label className="block text-xs font-medium text-[#4D6054]">
              Starting Location / Depot <span className="text-[#A35C49]">*</span>
              <input
                type="text"
                placeholder="e.g., Central Bus Terminal"
                value={startLocation}
                onChange={(e) => setStartLocation(e.target.value)}
                className="mt-1 w-full rounded-xl border border-[#DCE4DA] bg-[#FBFDFB] px-3 py-2 text-xs text-[#28352D] outline-none focus:border-[#285943]"
                required
              />
            </label>

            <label className="block text-xs font-medium text-[#4D6054]">
              Intermediate Stops (comma-separated)
              <input
                type="text"
                placeholder="e.g., Sector 4, Civic Center, Metro Station"
                value={intermediateStops}
                onChange={(e) => setIntermediateStops(e.target.value)}
                className="mt-1 w-full rounded-xl border border-[#DCE4DA] bg-[#FBFDFB] px-3 py-2 text-xs text-[#28352D] outline-none focus:border-[#285943]"
              />
            </label>
          </div>

          <div className="grid gap-3 grid-cols-2 sm:grid-cols-4">
            <label className="block text-xs font-medium text-[#4D6054]">
              One-way Distance (km) <span className="text-[#A35C49]">*</span>
              <input
                type="number"
                step="any"
                min="1"
                placeholder="e.g., 28"
                value={distanceKm}
                onChange={(e) => setDistanceKm(e.target.value)}
                className="mt-1 w-full rounded-xl border border-[#DCE4DA] bg-[#FBFDFB] px-3 py-2 text-xs text-[#28352D] outline-none focus:border-[#285943]"
                required
              />
            </label>

            <label className="block text-xs font-medium text-[#4D6054]">
              Duration (minutes)
              <input
                type="number"
                min="5"
                placeholder="e.g., 45"
                value={durationMinutes}
                onChange={(e) => setDurationMinutes(e.target.value)}
                className="mt-1 w-full rounded-xl border border-[#DCE4DA] bg-[#FBFDFB] px-3 py-2 text-xs text-[#28352D] outline-none focus:border-[#285943]"
              />
            </label>

            <label className="block text-xs font-medium text-[#4D6054]">
              Trips per Day
              <input
                type="number"
                min="1"
                value={tripsPerDay}
                onChange={(e) => setTripsPerDay(e.target.value)}
                className="mt-1 w-full rounded-xl border border-[#DCE4DA] bg-[#FBFDFB] px-3 py-2 text-xs text-[#28352D] outline-none focus:border-[#285943]"
              />
            </label>

            <label className="block text-xs font-medium text-[#4D6054]">
              Days / Week
              <input
                type="number"
                min="1"
                max="7"
                value={operatingDaysPerWeek}
                onChange={(e) => setOperatingDaysPerWeek(e.target.value)}
                className="mt-1 w-full rounded-xl border border-[#DCE4DA] bg-[#FBFDFB] px-3 py-2 text-xs text-[#28352D] outline-none focus:border-[#285943]"
              />
            </label>
          </div>

          <div className="rounded-xl border border-[#E7EFE4] bg-[#F9FCF8] p-4 space-y-4">
            <p className="text-xs font-semibold text-[#304739]">
              Vehicle Specifications & Passenger Demand
            </p>

            <div className="grid gap-3 grid-cols-2 sm:grid-cols-4">
              <label className="block text-xs font-medium text-[#4D6054]">
                Bus / Fleet ID
                <input
                  type="text"
                  placeholder="e.g., BUS-08"
                  value={busId}
                  onChange={(e) => setBusId(e.target.value)}
                  className="mt-1 w-full rounded-xl border border-[#DCE4DA] bg-white px-3 py-2 text-xs text-[#28352D] outline-none focus:border-[#285943]"
                />
              </label>

              <label className="block text-xs font-medium text-[#4D6054]">
                Fuel Type
                <select
                  value={fuelType}
                  onChange={(e) => setFuelType(e.target.value as any)}
                  className="mt-1 w-full rounded-xl border border-[#DCE4DA] bg-white px-3 py-2 text-xs text-[#28352D] outline-none focus:border-[#285943] cursor-pointer"
                >
                  <option value="Diesel">Diesel</option>
                  <option value="CNG">CNG</option>
                  <option value="Electric">Electric</option>
                </select>
              </label>

              <label className="block text-xs font-medium text-[#4D6054]">
                Seating Capacity
                <input
                  type="number"
                  min="10"
                  placeholder="e.g., 40"
                  value={seatingCapacity}
                  onChange={(e) => setSeatingCapacity(e.target.value)}
                  className="mt-1 w-full rounded-xl border border-[#DCE4DA] bg-white px-3 py-2 text-xs text-[#28352D] outline-none focus:border-[#285943]"
                />
              </label>

              <label className="block text-xs font-medium text-[#4D6054]">
                Assigned Students <span className="text-[#A35C49]">*</span>
                <input
                  type="number"
                  min="1"
                  placeholder="e.g., 26"
                  value={assignedStudents}
                  onChange={(e) => setAssignedStudents(e.target.value)}
                  className="mt-1 w-full rounded-xl border border-[#DCE4DA] bg-white px-3 py-2 text-xs text-[#28352D] outline-none focus:border-[#285943]"
                  required
                />
              </label>
            </div>

            <div className="grid gap-3 sm:grid-cols-2">
              <label className="block text-xs font-medium text-[#4D6054]">
                Fuel Efficiency (km/L)
                <input
                  type="number"
                  step="0.1"
                  min="1"
                  placeholder="e.g., 5.2"
                  value={fuelEfficiencyKmPerL}
                  onChange={(e) => setFuelEfficiencyKmPerL(e.target.value)}
                  className="mt-1 w-full rounded-xl border border-[#DCE4DA] bg-white px-3 py-2 text-xs text-[#28352D] outline-none focus:border-[#285943]"
                />
              </label>

              <label className="block text-xs font-medium text-[#4D6054]">
                Operating Notes
                <input
                  type="text"
                  placeholder="e.g., Morning peak traffic on Outer Ring Road"
                  value={notes}
                  onChange={(e) => setNotes(e.target.value)}
                  className="mt-1 w-full rounded-xl border border-[#DCE4DA] bg-white px-3 py-2 text-xs text-[#28352D] outline-none focus:border-[#285943]"
                />
              </label>
            </div>
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
              {initialRoute ? 'Update Route' : 'Save Bus Route'}
            </Button>
          </div>
        </form>
      </div>
    </div>
  )
}
