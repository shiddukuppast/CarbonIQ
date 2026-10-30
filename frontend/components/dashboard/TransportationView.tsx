'use client'

import React, { useMemo, useRef, useState } from 'react'
import {
  AlertCircle,
  ArrowRight,
  Bus,
  BusFront,
  CheckCircle2,
  ChevronRight,
  Cloud,
  Compass,
  Edit2,
  FileCheck,
  Fuel,
  GitMerge,
  MoreHorizontal,
  Plus,
  Route,
  Sparkles,
  Trash2,
  Truck,
  Users,
  Wallet,
} from 'lucide-react'
import { ModuleAiAdvisor } from '@/components/ai/ModuleAiAdvisor'
import { BusRouteModal } from '@/components/dashboard/BusRouteModal'
import { RouteComparisonModal } from '@/components/dashboard/RouteComparisonModal'
import { TransportationRecordModal } from '@/components/dashboard/TransportationRecordModal'
import { Button } from '@/components/ui/button'
import { Card } from '@/components/ui/Card'
import { Metric } from '@/components/ui/Metric'
import { MiniSpark } from '@/components/ui/MiniSpark'
import { PageTitle } from '@/components/ui/PageTitle'
import { Pill } from '@/components/ui/Pill'
import { ToastNotification } from '@/components/ui/ToastNotification'
import { useAuth } from '@/context/auth-context'
import {
  calculateTransportationEmissions,
  generateBusRouteOptimizations,
} from '@/lib/calculations'
import { apiClient } from '@/services/api-client'
import { aiAdvisorsService } from '@/services/ai-advisors.service'
import type {
  BusRoute,
  RouteOptimizationProposal,
  TransportationRecord,
} from '@/types/sustainability'

const INITIAL_TRANSPORT_RECORDS: TransportationRecord[] = [
  {
    id: 'tr-1',
    date: '2026-10-28',
    mode: 'Bus',
    distanceKm: 580,
    fuelType: 'Diesel',
    fuelConsumedLiters: 112,
    fuelEfficiencyKmPerL: 5.2,
    fuelExpenditureInr: 10584,
    vehicleId: 'BUS-04',
    passengerCount: 38,
    notes: 'Campus North Corridor - 2 shifts',
    calculationMethod: 'actual_fuel',
    calculatedEmissionsKg: calculateTransportationEmissions({
      distanceKm: 580,
      fuelType: 'Diesel',
      fuelConsumedLiters: 112,
    }).emissionsKg,
    createdAt: '2026-10-28T08:00:00.000Z',
  },
  {
    id: 'tr-2',
    date: '2026-10-24',
    mode: 'Bus',
    distanceKm: 540,
    fuelType: 'Diesel',
    fuelConsumedLiters: 104,
    fuelEfficiencyKmPerL: 5.2,
    fuelExpenditureInr: 9828,
    vehicleId: 'BUS-07',
    passengerCount: 34,
    notes: 'South Sector route',
    calculationMethod: 'actual_fuel',
    calculatedEmissionsKg: calculateTransportationEmissions({
      distanceKm: 540,
      fuelType: 'Diesel',
      fuelConsumedLiters: 104,
    }).emissionsKg,
    createdAt: '2026-10-24T08:00:00.000Z',
  },
  {
    id: 'tr-3',
    date: '2026-10-18',
    mode: 'Fleet Van',
    distanceKm: 180,
    fuelType: 'Diesel',
    fuelConsumedLiters: 22,
    fuelEfficiencyKmPerL: 8.2,
    fuelExpenditureInr: 2079,
    vehicleId: 'VAN-02',
    passengerCount: 8,
    notes: 'Faculty inter-campus transfer',
    calculationMethod: 'actual_fuel',
    calculatedEmissionsKg: calculateTransportationEmissions({
      distanceKm: 180,
      fuelType: 'Diesel',
      fuelConsumedLiters: 22,
    }).emissionsKg,
    createdAt: '2026-10-18T08:00:00.000Z',
  },
  {
    id: 'tr-4',
    date: '2026-10-12',
    mode: 'Bus',
    distanceKm: 420,
    fuelType: 'CNG',
    fuelConsumedLiters: 80,
    fuelEfficiencyKmPerL: 5.25,
    fuelExpenditureInr: 6560,
    vehicleId: 'BUS-09',
    passengerCount: 32,
    notes: 'Metro feeder connector',
    calculationMethod: 'actual_fuel',
    calculatedEmissionsKg: calculateTransportationEmissions({
      distanceKm: 420,
      fuelType: 'CNG',
      fuelConsumedLiters: 80,
    }).emissionsKg,
    createdAt: '2026-10-12T08:00:00.000Z',
  },
]

const INITIAL_BUS_ROUTES: BusRoute[] = [
  {
    id: 'route-a',
    routeName: 'Route 101 — North Hub',
    startLocation: 'Hebbal Flyover',
    destination: 'Main Campus Gate 1',
    intermediateStops: ['Sahakar Nagar', 'Jakkur Aerodrome', 'Yelahanka Bypass'],
    distanceKm: 30,
    durationMinutes: 45,
    tripsPerDay: 2,
    operatingDaysPerWeek: 5,
    assignedStudents: 22,
    busId: 'BUS-01',
    fuelType: 'Diesel',
    fuelEfficiencyKmPerL: 5.0,
    seatingCapacity: 40,
    currentBusesCount: 1,
    status: 'active',
    notes: 'Low morning occupancy (22/40)',
  },
  {
    id: 'route-b',
    routeName: 'Route 102 — Jakkur Corridor',
    startLocation: 'Kogilu Cross',
    destination: 'Main Campus Gate 1',
    intermediateStops: ['Jakkur Aerodrome', 'Kogilu Village', 'Judicial Layout'],
    distanceKm: 28,
    durationMinutes: 42,
    tripsPerDay: 2,
    operatingDaysPerWeek: 5,
    assignedStudents: 16,
    busId: 'BUS-02',
    fuelType: 'Diesel',
    fuelEfficiencyKmPerL: 5.2,
    seatingCapacity: 40,
    currentBusesCount: 1,
    status: 'active',
    notes: 'Overlaps with Route 101 at Jakkur',
  },
  {
    id: 'route-c',
    routeName: 'Route 201 — South Ring',
    startLocation: 'Banashankari Depot',
    destination: 'Main Campus Gate 2',
    intermediateStops: ['Silk Board', 'HSR Layout', 'Bellandur'],
    distanceKm: 42,
    durationMinutes: 65,
    tripsPerDay: 2,
    operatingDaysPerWeek: 5,
    assignedStudents: 36,
    busId: 'BUS-03',
    fuelType: 'Diesel',
    fuelEfficiencyKmPerL: 4.8,
    seatingCapacity: 40,
    currentBusesCount: 1,
    status: 'active',
    notes: 'Near full capacity (36/40)',
  },
]

export function TransportationView() {
  const { session, user, token, requestMutation } = useAuth()
  const isAuth = Boolean(session.isAuthenticated && token)
  const optimizationSectionRef = useRef<HTMLDivElement>(null)

  const [records, setRecords] = useState<TransportationRecord[]>(isAuth ? [] : INITIAL_TRANSPORT_RECORDS)
  const [routes, setRoutes] = useState<BusRoute[]>(isAuth ? [] : INITIAL_BUS_ROUTES)
  const [proposals, setProposals] = useState<RouteOptimizationProposal[]>(
    isAuth ? [] : generateBusRouteOptimizations(INITIAL_BUS_ROUTES)
  )

  const [isRecordModalOpen, setIsRecordModalOpen] = useState(false)
  const [editingRecord, setEditingRecord] = useState<TransportationRecord | null>(null)

  const [isRouteModalOpen, setIsRouteModalOpen] = useState(false)
  const [editingRoute, setEditingRoute] = useState<BusRoute | null>(null)

  const [selectedProposal, setSelectedProposal] = useState<RouteOptimizationProposal | null>(null)
  const [isComparisonModalOpen, setIsComparisonModalOpen] = useState(false)

  const [activeMenuId, setActiveMenuId] = useState<string | null>(null)
  const [toastMessage, setToastMessage] = useState<string | null>(null)

  const fetchTransportationData = React.useCallback(async () => {
    if (!isAuth || !token) return
    try {
      const [recordsRes, routesRes] = await Promise.allSettled([
        apiClient.get<any[]>('/transportation', { token }),
        apiClient.get<any[]>('/transportation/routes', { token }),
      ])

      if (recordsRes.status === 'fulfilled' && Array.isArray(recordsRes.value)) {
        setRecords(
          recordsRes.value.map((raw: any) => ({
            id: raw.id,
            date: raw.date || raw.reporting_period || '2026-10-28',
            mode: raw.mode || 'Bus',
            distanceKm: Number(raw.distance_km) || 0,
            fuelType: raw.fuel_type || 'Diesel',
            fuelConsumedLiters: raw.fuel_consumed_liters != null ? Number(raw.fuel_consumed_liters) : undefined,
            fuelEfficiencyKmPerL: raw.fuel_efficiency_km_per_l != null ? Number(raw.fuel_efficiency_km_per_l) : undefined,
            fuelExpenditureInr: raw.fuel_expenditure_inr != null ? Number(raw.fuel_expenditure_inr) : undefined,
            vehicleId: raw.vehicle_id,
            passengerCount: raw.passenger_count != null ? Number(raw.passenger_count) : undefined,
            vehicleCapacity: raw.vehicle_capacity != null ? Number(raw.vehicle_capacity) : undefined,
            routeName: raw.route_name,
            pickupLocations: raw.pickup_locations,
            destination: raw.destination,
            notes: raw.notes,
            calculationMethod: raw.calculation_method || 'actual_fuel',
            calculatedEmissionsKg: Number(raw.calculated_emissions_kg) || 0,
            factorSource: raw.factor_source,
            factorVersion: raw.factor_version,
            calculationBoundary: raw.calculation_boundary,
            createdAt: raw.created_at || new Date().toISOString(),
          }))
        )
      }

      if (routesRes.status === 'fulfilled' && Array.isArray(routesRes.value)) {
        const loadedRoutes: BusRoute[] = routesRes.value.map((raw: any) => ({
          id: raw.id,
          routeName: raw.route_name,
          startLocation: raw.start_location,
          destination: raw.destination,
          intermediateStops: raw.intermediate_stops || [],
          distanceKm: Number(raw.distance_km) || 0,
          durationMinutes: Number(raw.duration_minutes) || 0,
          tripsPerDay: Number(raw.trips_per_day) || 1,
          operatingDaysPerWeek: Number(raw.operating_days_per_week) || 5,
          assignedStudents: Number(raw.assigned_students) || 0,
          busId: raw.bus_id || 'BUS-01',
          fuelType: raw.fuel_type || 'Diesel',
          fuelEfficiencyKmPerL: Number(raw.fuel_efficiency_km_per_l) || 5.0,
          seatingCapacity: Number(raw.seating_capacity) || 40,
          currentBusesCount: Number(raw.current_buses_count) || 1,
          status: raw.status || 'active',
          notes: raw.notes,
        }))
        setRoutes(loadedRoutes)
        if (loadedRoutes.length > 0) {
          setProposals(generateBusRouteOptimizations(loadedRoutes))
        }
      }
    } catch (err: any) {
      console.error('Failed to fetch transportation data:', err)
    }
  }, [isAuth])

  React.useEffect(() => {
    if (isAuth) {
      fetchTransportationData()
    } else {
      setRecords(INITIAL_TRANSPORT_RECORDS)
      setRoutes(INITIAL_BUS_ROUTES)
      setProposals(generateBusRouteOptimizations(INITIAL_BUS_ROUTES))
    }
  }, [isAuth, fetchTransportationData])

  // Aggregated metrics from records
  const totalDistanceKm = useMemo(
    () => records.reduce((acc, r) => acc + r.distanceKm, 0),
    [records]
  )

  const totalFuelLiters = useMemo(
    () => records.reduce((acc, r) => acc + (r.fuelConsumedLiters || 0), 0),
    [records]
  )

  const totalExpenditureInr = useMemo(
    () => records.reduce((acc, r) => acc + (r.fuelExpenditureInr || 0), 0),
    [records]
  )

  const totalEmissionsKg = useMemo(
    () => records.reduce((acc, r) => acc + r.calculatedEmissionsKg, 0),
    [records]
  )

  // Potential monthly savings from active proposals
  const potentialOptimizationSavingsInr = useMemo(
    () => proposals.reduce((acc, p) => acc + p.estimatedMonthlySavingsInr, 0),
    [proposals]
  )

  const scrollToOptimizer = () => {
    optimizationSectionRef.current?.scrollIntoView({ behavior: 'smooth' })
  }

  // Record actions
  const handleOpenAddRecord = () => {
    if (!requestMutation('add transportation records')) return
    setEditingRecord(null)
    setIsRecordModalOpen(true)
  }

  const handleOpenEditRecord = (rec: TransportationRecord) => {
    if (!requestMutation('edit transportation records')) return
    setEditingRecord(rec)
    setIsRecordModalOpen(true)
    setActiveMenuId(null)
  }

  const handleDeleteRecord = async (id: string) => {
    if (!requestMutation('delete transportation records')) return
    if (isAuth) {
      try {
        await apiClient.delete(`/transportation/${id}`)
        setToastMessage('Travel record removed from database.')
        await fetchTransportationData()
      } catch (err: any) {
        setToastMessage(err.message || 'Failed to remove transportation record.')
      }
    } else {
      setRecords((prev) => prev.filter((r) => r.id !== id))
      setToastMessage('Travel record removed from workspace.')
    }
    setActiveMenuId(null)
  }

  const handleSaveRecord = async (
    data: Omit<TransportationRecord, 'id' | 'createdAt'>,
    existingId?: string
  ) => {
    if (isAuth) {
      try {
        const payload = {
          date: data.date,
          mode: data.mode,
          distance_km: data.distanceKm,
          fuel_type: data.fuelType || 'Diesel',
          fuel_consumed_liters: data.fuelConsumedLiters,
          fuel_efficiency_km_per_l: data.fuelEfficiencyKmPerL,
          fuel_expenditure_inr: data.fuelExpenditureInr,
          vehicle_id: data.vehicleId,
          passenger_count: data.passengerCount,
          vehicle_capacity: data.vehicleCapacity,
          route_name: data.routeName,
          destination: data.destination,
          notes: data.notes,
        }
        if (existingId) {
          await apiClient.put(`/transportation/${existingId}`, payload)
          setToastMessage('Transportation record updated in database.')
        } else {
          await apiClient.post('/transportation', payload)
          setToastMessage('Transportation record saved to database.')
        }
        await fetchTransportationData()
      } catch (err: any) {
        setToastMessage(err.message || 'Failed to save transportation record.')
      }
    } else {
      if (existingId) {
        setRecords((prev) =>
          prev.map((r) => (r.id === existingId ? { ...r, ...data } : r))
        )
        setToastMessage('Travel record updated successfully.')
      } else {
        const newRec: TransportationRecord = {
          ...data,
          id: `tr-${Date.now()}`,
          createdAt: new Date().toISOString(),
        }
        setRecords((prev) => [newRec, ...prev])
        setToastMessage('Transportation entry saved to workspace.')
      }
    }
  }

  // Bus route actions
  const handleOpenAddRoute = () => {
    if (!requestMutation('manage bus routes')) return
    setEditingRoute(null)
    setIsRouteModalOpen(true)
  }

  const handleOpenEditRoute = (rt: BusRoute) => {
    if (!requestMutation('edit bus routes')) return
    setEditingRoute(rt)
    setIsRouteModalOpen(true)
  }

  const handleDeleteRoute = async (id: string) => {
    if (!requestMutation('delete bus routes')) return
    if (isAuth) {
      try {
        await apiClient.delete(`/transportation/routes/${id}`)
        setToastMessage('Bus route deleted from database.')
        await fetchTransportationData()
      } catch (err: any) {
        setToastMessage(err.message || 'Failed to delete bus route.')
      }
    } else {
      const updated = routes.filter((r) => r.id !== id)
      setRoutes(updated)
      setProposals(generateBusRouteOptimizations(updated))
      setToastMessage('Bus route deleted.')
    }
  }

  const handleSaveRoute = async (data: Omit<BusRoute, 'id'>, existingId?: string) => {
    if (isAuth) {
      try {
        const payload = {
          route_name: data.routeName,
          start_location: data.startLocation,
          destination: data.destination,
          intermediate_stops: data.intermediateStops,
          distance_km: data.distanceKm,
          duration_minutes: data.durationMinutes,
          trips_per_day: data.tripsPerDay,
          operating_days_per_week: data.operatingDaysPerWeek,
          assigned_students: data.assignedStudents,
          bus_id: data.busId,
          fuel_type: data.fuelType,
          fuel_efficiency_km_per_l: data.fuelEfficiencyKmPerL,
          seating_capacity: data.seatingCapacity,
          current_buses_count: data.currentBusesCount,
          status: data.status,
          notes: data.notes,
        }
        if (existingId) {
          await apiClient.put(`/transportation/routes/${existingId}`, payload)
          setToastMessage('Bus route updated in database.')
        } else {
          await apiClient.post('/transportation/routes', payload)
          setToastMessage('New bus route configured and saved to database.')
        }
        await fetchTransportationData()
      } catch (err: any) {
        setToastMessage(err.message || 'Failed to save bus route.')
      }
    } else {
      let updatedRoutes: BusRoute[]
      if (existingId) {
        updatedRoutes = routes.map((r) => (r.id === existingId ? { ...r, ...data } : r))
        setToastMessage('Bus route updated successfully.')
      } else {
        const newRt: BusRoute = {
          ...data,
          id: `route-${Date.now()}`,
        }
        updatedRoutes = [...routes, newRt]
        setToastMessage('New bus route configured and added.')
      }
      setRoutes(updatedRoutes)
      setProposals(generateBusRouteOptimizations(updatedRoutes))
    }
  }

  const handleRunOptimizer = async () => {
    if (isAuth) {
      try {
        const res = await apiClient.post<any>('/transportation/optimize')
        if (res && Array.isArray(res.proposals) && res.proposals.length > 0) {
          const mapped: RouteOptimizationProposal[] = res.proposals.map((p: any) => ({
            id: p.id,
            title: p.title,
            summary: p.summary,
            reason: p.reason,
            capacityCheckPassed: p.capacity_check_passed,
            currentConfig: {
              routeIds: p.current_config?.route_ids || [],
              routeNames: p.current_config?.route_names || [],
              busesCount: p.current_config?.buses_count || 1,
              studentsServed: p.current_config?.students_served || 0,
              totalDistanceKm: p.current_config?.total_distance_km || 0,
              dailyFuelConsumptionLiters: p.current_config?.daily_fuel_consumption_liters || 0,
              monthlyFuelCostInr: p.current_config?.monthly_fuel_cost_inr || 0,
              monthlyEmissionsKg: p.current_config?.monthly_emissions_kg || 0,
            },
            proposedConfig: {
              routeIds: p.proposed_config?.route_ids || [],
              routeNames: p.proposed_config?.route_names || [],
              busesCount: p.proposed_config?.buses_count || 1,
              studentsServed: p.proposed_config?.students_served || 0,
              totalDistanceKm: p.proposed_config?.total_distance_km || 0,
              dailyFuelConsumptionLiters: p.proposed_config?.daily_fuel_consumption_liters || 0,
              monthlyFuelCostInr: p.proposed_config?.monthly_fuel_cost_inr || 0,
              monthlyEmissionsKg: p.proposed_config?.monthly_emissions_kg || 0,
            },
            estimatedDistanceReductionKm: p.estimated_distance_reduction_km || 0,
            estimatedFuelSavingsLiters: p.estimated_fuel_savings_liters || 0,
            estimatedMonthlySavingsInr: p.estimated_monthly_savings_inr || 0,
            estimatedEmissionsReductionKg: p.estimated_emissions_reduction_kg || 0,
            feasibility: p.feasibility || 'High',
            requiredValidation: p.required_validation || [],
            status: p.status || 'pending',
          }))
          setProposals(mapped)
          setToastMessage(
            `Optimization completed: ${mapped.length} consolidation candidate identified from backend.`
          )
          return
        }
      } catch (err: any) {
        console.warn('Backend route optimizer returned error, using verified client optimizer:', err)
      }
    }

    const updated = generateBusRouteOptimizations(routes)
    setProposals(updated)
    if (updated.length > 0) {
      setToastMessage(
        `Optimization completed: ${updated.length} consolidation candidate identified.`
      )
    } else {
      setToastMessage(
        'Optimization completed: All current routes operate within optimal capacity thresholds.'
      )
    }
  }

  const handleAcceptProposal = async (proposalId: string) => {
    const proposal = proposals.find((p) => p.id === proposalId)
    if (isAuth && proposal) {
      try {
        await apiClient.post('/transportation/optimize/accept', {
          id: proposal.id,
          title: proposal.title,
          summary: proposal.summary,
          reason: proposal.reason,
          capacity_check_passed: proposal.capacityCheckPassed,
          current_config: {
            route_ids: proposal.currentConfig.routeIds,
            route_names: proposal.currentConfig.routeNames,
            buses_count: proposal.currentConfig.busesCount,
            students_served: proposal.currentConfig.studentsServed,
            total_distance_km: proposal.currentConfig.totalDistanceKm,
            daily_fuel_consumption_liters: proposal.currentConfig.dailyFuelConsumptionLiters,
            monthly_fuel_cost_inr: proposal.currentConfig.monthlyFuelCostInr,
            monthly_emissions_kg: proposal.currentConfig.monthlyEmissionsKg,
          },
          proposed_config: {
            route_ids: proposal.proposedConfig.routeIds,
            route_names: proposal.proposedConfig.routeNames,
            buses_count: proposal.proposedConfig.busesCount,
            students_served: proposal.proposedConfig.studentsServed,
            total_distance_km: proposal.proposedConfig.totalDistanceKm,
            daily_fuel_consumption_liters: proposal.proposedConfig.dailyFuelConsumptionLiters,
            monthly_fuel_cost_inr: proposal.proposedConfig.monthlyFuelCostInr,
            monthly_emissions_kg: proposal.proposedConfig.monthlyEmissionsKg,
          },
          estimated_distance_reduction_km: proposal.estimatedDistanceReductionKm,
          estimated_fuel_savings_liters: proposal.estimatedFuelSavingsLiters,
          estimated_monthly_savings_inr: proposal.estimatedMonthlySavingsInr,
          estimated_emissions_reduction_kg: proposal.estimatedEmissionsReductionKg,
          feasibility: proposal.feasibility,
          required_validation: proposal.requiredValidation,
          status: 'accepted',
        })
      } catch (err) {
        console.warn('Failed to record intervention on backend:', err)
      }
    }

    setProposals((prev) =>
      prev.map((p) =>
        p.id === proposalId ? { ...p, status: 'accepted' as const } : p
      )
    )
    setToastMessage('Route consolidation proposal recorded as Planned Intervention.')
  }

  const handleRejectProposal = (proposalId: string) => {
    setProposals((prev) =>
      prev.map((p) =>
        p.id === proposalId ? { ...p, status: 'rejected' as const } : p
      )
    )
    setToastMessage('Recommendation dismissed.')
  }

  return (
    <div className="space-y-6">
      <ToastNotification message={toastMessage} onClose={() => setToastMessage(null)} />

      <PageTitle
        eyebrow="MOBILITY & LOGISTICS MODULE"
        title="Transportation & Fuel Optimization"
        description="Monitor fleet distance, track verifiable fuel usage, and optimize transit bus routes using capacity-aware algorithms."
        action={
          <div className="flex flex-wrap gap-2.5">
            <Button variant="secondary" onClick={scrollToOptimizer}>
              <GitMerge size={15} /> Optimize Bus Routes
            </Button>
            <Button onClick={handleOpenAddRecord}>
              <Plus size={15} /> Add Record
            </Button>
          </div>
        }
      />

      {/* Top 4 Metrics Cards */}
      <div className="grid gap-4 sm:grid-cols-2 xl:grid-cols-4">
        <Metric
          icon={BusFront}
          label="Total distance logged"
          value={totalDistanceKm.toLocaleString()}
          unit="km"
          trend={<MiniSpark />}
          note={`Across ${records.length} travel entries`}
          tone="green"
        />
        <Metric
          icon={Fuel}
          label="Total fuel consumed"
          value={totalFuelLiters.toLocaleString()}
          unit="L"
          trend={<Pill tone="sage">Verified entries</Pill>}
          note="Actual liters recorded"
          tone="sage"
        />
        <Metric
          icon={Cloud}
          label="Transport emissions"
          value={Math.round(totalEmissionsKg).toLocaleString()}
          unit="kg CO₂e"
          trend={<span className="text-[11px] font-medium text-[#4B8A63]">Strict fuel method</span>}
          note="No double-counting"
          tone="olive"
        />
        <Metric
          icon={Wallet}
          label="Potential route savings"
          value={`₹${potentialOptimizationSavingsInr.toLocaleString('en-IN')}`}
          unit="/mo"
          trend={<Pill>AI Modeled</Pill>}
          note={`${proposals.length} active corridor proposal(s)`}
          tone="amber"
        />
      </div>

      {/* Travel Entries Table */}
      <Card className="p-5 sm:p-6">
        <div className="flex items-center justify-between">
          <div>
            <h2 className="font-semibold text-[#304739]">Travel & Fleet Log</h2>
            <p className="mt-0.5 text-xs text-[#8A978D]">
              Verified records with separated actual vs efficiency-based emissions
            </p>
          </div>
          <Button variant="secondary" onClick={handleOpenAddRecord} className="text-xs">
            <Plus size={14} /> New travel log
          </Button>
        </div>

        <div className="mt-5 overflow-x-auto">
          <table className="w-full min-w-[700px] text-left text-xs">
            <thead className="border-b border-[#E8EEE6] text-[10px] uppercase tracking-[.12em] text-[#98A49A]">
              <tr>
                <th className="pb-3 font-medium">Date</th>
                <th className="pb-3 font-medium">Vehicle / Mode</th>
                <th className="pb-3 font-medium">Distance</th>
                <th className="pb-3 font-medium">Fuel Consumed</th>
                <th className="pb-3 font-medium">Expenditure</th>
                <th className="pb-3 font-medium">Emissions</th>
                <th className="pb-3 font-medium">Calculation Method</th>
                <th className="pb-3 font-medium text-right">Actions</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-[#EFF3EE] text-[#55675A]">
              {records.length === 0 ? (
                <tr>
                  <td colSpan={8} className="py-12 text-center text-[#748178]">
                    <div className="mx-auto max-w-sm space-y-2">
                      <Truck className="mx-auto h-8 w-8 text-[#A0B4A2]" />
                      <p className="text-sm font-semibold text-[#285943]">No transportation logs found</p>
                      <p className="text-xs text-[#7A8E80]">
                        Click &ldquo;New travel log&rdquo; above to record vehicle trips, fuel usage, and transit distances.
                      </p>
                    </div>
                  </td>
                </tr>
              ) : (
                records.map((rec) => (
                <tr key={rec.id} className="hover:bg-[#FAFDF9]">
                  <td className="py-3 font-medium text-[#2F4436]">{rec.date}</td>
                  <td className="py-3">
                    <span className="font-medium text-[#304739]">{rec.vehicleId || rec.mode}</span>
                    <span className="text-[#87998D] block text-[10px]">{rec.notes || rec.mode}</span>
                  </td>
                  <td className="py-3 font-semibold text-[#285943]">
                    {rec.distanceKm.toLocaleString()} km
                  </td>
                  <td className="py-3">
                    {rec.fuelConsumedLiters ? `${rec.fuelConsumedLiters} L (${rec.fuelType})` : '—'}
                  </td>
                  <td className="py-3">
                    {rec.fuelExpenditureInr ? `₹${rec.fuelExpenditureInr.toLocaleString('en-IN')}` : '—'}
                  </td>
                  <td className="py-3 font-medium text-[#3A5243]">
                    {rec.calculatedEmissionsKg.toLocaleString()} kg CO₂e
                  </td>
                  <td className="py-3">
                    <Pill tone={rec.calculationMethod === 'actual_fuel' ? 'green' : 'sage'}>
                      {rec.calculationMethod === 'actual_fuel' ? 'Actual Fuel' : 'Distance/Eff.'}
                    </Pill>
                  </td>
                  <td className="py-3 text-right">
                    <div className="relative inline-block text-left">
                      <button
                        type="button"
                        onClick={() =>
                          setActiveMenuId(activeMenuId === rec.id ? null : rec.id)
                        }
                        aria-label="Record options"
                        className="rounded-lg p-1 text-[#8A978D] hover:bg-[#EEF3EC] hover:text-[#285943] cursor-pointer"
                      >
                        <MoreHorizontal size={15} />
                      </button>

                      {activeMenuId === rec.id && (
                        <>
                          <div
                            className="fixed inset-0 z-20"
                            onClick={() => setActiveMenuId(null)}
                            aria-hidden="true"
                          />
                          <div className="absolute right-0 top-7 z-30 w-36 rounded-xl border border-[#E0E7DE] bg-white p-1.5 shadow-lg animate-in fade-in duration-100">
                            <button
                              type="button"
                              onClick={() => handleOpenEditRecord(rec)}
                              className="flex w-full items-center gap-2 rounded-lg px-2.5 py-1.5 text-left text-xs text-[#526357] hover:bg-[#F3F7F1] cursor-pointer"
                            >
                              <Edit2 size={13} /> Edit
                            </button>
                            <button
                              type="button"
                              onClick={() => handleDeleteRecord(rec.id)}
                              className="flex w-full items-center gap-2 rounded-lg px-2.5 py-1.5 text-left text-xs font-medium text-[#A35C49] hover:bg-[#FDF2F0] cursor-pointer"
                            >
                              <Trash2 size={13} /> Delete
                            </button>
                          </div>
                        </>
                      )}
                    </div>
                  </td>
                </tr>
              ))
              )}
            </tbody>
          </table>
        </div>
      </Card>

      {/* DEDICATED BUS ROUTE MANAGEMENT & OPTIMIZATION SECTION */}
      <div ref={optimizationSectionRef} className="space-y-6 pt-4">
        <div className="flex flex-col gap-2 sm:flex-row sm:items-center sm:justify-between border-b border-[#E0E7DE] pb-4">
          <div>
            <div className="flex items-center gap-2.5">
              <span className="grid h-8 w-8 place-items-center rounded-lg bg-[#285943] text-white">
                <Route size={16} />
              </span>
              <h2 className="text-xl font-semibold tracking-[-0.03em] text-[#28352D]">
                Smart Bus Route Optimization
              </h2>
            </div>
            <p className="mt-1 text-xs text-[#7A8C80]">
              Analyze bus routes, student demand, and vehicle capacity to identify opportunities for more efficient transportation.
            </p>
          </div>

          <div className="flex items-center gap-2.5">
            <Button variant="secondary" onClick={handleOpenAddRoute} className="text-xs">
              <Plus size={14} /> Add Route
            </Button>
            <Button onClick={handleRunOptimizer} className="text-xs bg-[#285943]">
              <Sparkles size={14} /> Analyze & Optimize Routes
            </Button>
          </div>
        </div>

        {/* Configured Bus Routes Table */}
        <Card className="p-5 sm:p-6">
          <div className="flex items-center justify-between">
            <h3 className="font-semibold text-[#304739]">Active Bus Routes & Passenger Load</h3>
            <span className="text-xs text-[#7D8E81]">{routes.length} configured routes</span>
          </div>

          <div className="mt-4 overflow-x-auto">
            <table className="w-full min-w-[760px] text-left text-xs">
              <thead className="border-b border-[#E8EEE6] text-[10px] uppercase tracking-[.12em] text-[#98A49A]">
                <tr>
                  <th className="pb-3 font-medium">Route ID / Name</th>
                  <th className="pb-3 font-medium">Origin ➔ Destination</th>
                  <th className="pb-3 font-medium">Intermediate Stops</th>
                  <th className="pb-3 font-medium">Distance</th>
                  <th className="pb-3 font-medium">Student Demand</th>
                  <th className="pb-3 font-medium">Bus Specs</th>
                  <th className="pb-3 font-medium">Occupancy</th>
                  <th className="pb-3 font-medium text-right">Actions</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-[#EFF3EE] text-[#55675A]">
                {routes.length === 0 ? (
                  <tr>
                    <td colSpan={8} className="py-12 text-center text-[#748178]">
                      <div className="mx-auto max-w-sm space-y-2">
                        <Bus className="mx-auto h-8 w-8 text-[#A0B4A2]" />
                        <p className="text-sm font-semibold text-[#285943]">
                          {user?.accountType === 'individual'
                            ? 'Restricted to College & Organization accounts'
                            : 'No bus routes configured'}
                        </p>
                        <p className="text-xs text-[#7A8E80]">
                          {user?.accountType === 'individual'
                            ? 'Bus fleet management and multi-stop route optimization are designed for institutional fleet operations.'
                            : 'Click \u201CAdd Route\u201D above to register transit lines, student demand, and vehicle efficiencies.'}
                        </p>
                      </div>
                    </td>
                  </tr>
                ) : (
                  routes.map((rt) => {
                  const occupancyPct = Math.round((rt.assignedStudents / rt.seatingCapacity) * 100)
                  return (
                    <tr key={rt.id} className="hover:bg-[#FAFDF9]">
                      <td className="py-3 font-medium text-[#285943]">
                        <div className="flex items-center gap-1.5">
                          <Bus size={13} />
                          <span>{rt.routeName}</span>
                        </div>
                      </td>
                      <td className="py-3">
                        <span className="font-medium text-[#304739]">{rt.startLocation}</span>
                        <span className="text-[#889B8E] block text-[10px]">➔ {rt.destination}</span>
                      </td>
                      <td className="py-3 max-w-[200px] truncate" title={rt.intermediateStops.join(', ')}>
                        {rt.intermediateStops.length > 0 ? rt.intermediateStops.join(', ') : 'Direct run'}
                      </td>
                      <td className="py-3 font-medium">{rt.distanceKm} km ({rt.durationMinutes} min)</td>
                      <td className="py-3">
                        <span className="font-semibold text-[#2F4436]">{rt.assignedStudents}</span>
                        <span className="text-[#889B8E]"> / {rt.seatingCapacity} seats</span>
                      </td>
                      <td className="py-3">
                        <span>{rt.busId} ({rt.fuelType})</span>
                        <span className="text-[10px] text-[#889B8E] block">{rt.fuelEfficiencyKmPerL} km/L</span>
                      </td>
                      <td className="py-3">
                        <Pill tone={occupancyPct > 80 ? 'green' : occupancyPct < 60 ? 'amber' : 'sage'}>
                          {occupancyPct}%
                        </Pill>
                      </td>
                      <td className="py-3 text-right">
                        <div className="flex items-center justify-end gap-1.5">
                          <button
                            type="button"
                            onClick={() => handleOpenEditRoute(rt)}
                            className="p-1 text-[#788B7D] hover:text-[#285943] cursor-pointer"
                            title="Edit Route"
                          >
                            <Edit2 size={13} />
                          </button>
                          <button
                            type="button"
                            onClick={() => handleDeleteRoute(rt.id)}
                            className="p-1 text-[#A35C49] hover:text-[#7A3626] cursor-pointer"
                            title="Delete Route"
                          >
                            <Trash2 size={13} />
                          </button>
                        </div>
                      </td>
                    </tr>
                  )
                })
                )}
              </tbody>
            </table>
          </div>
        </Card>

        {/* Optimization Recommendations Results UI */}
        <div className="space-y-4">
          <div className="flex items-center justify-between">
            <div>
              <h3 className="font-semibold text-[#28352D]">Optimization Opportunities</h3>
              <p className="text-xs text-[#8A978D]">
                Grounded in passenger load limits, stop overlap, and realistic distance models
              </p>
            </div>
            <span className="text-xs font-semibold text-[#285943]">
              {proposals.length} active recommendation(s)
            </span>
          </div>

          {proposals.length === 0 ? (
            <Card className="p-8 text-center bg-[#FAFCF8]">
              <span className="mx-auto grid h-10 w-10 place-items-center rounded-xl bg-[#E7F1E5] text-[#285943]">
                <CheckCircle2 size={18} />
              </span>
              <p className="mt-3 text-sm font-semibold text-[#3D5245]">
                No route conflicts or consolidation candidates detected
              </p>
              <p className="mt-1 text-xs text-[#7F9083]">
                All active routes operate with balanced occupancy. Add more overlapping routes to explore multi-bus consolidation.
              </p>
            </Card>
          ) : (
            <div className="grid gap-4 sm:grid-cols-2">
              {proposals.map((prop) => {
                const isAccepted = prop.status === 'accepted'
                const isRejected = prop.status === 'rejected'
                return (
                  <Card
                    key={prop.id}
                    className={`p-5 transition-all ${
                      isAccepted
                        ? 'border-[#98BA93] bg-[#F7FBF6]'
                        : isRejected
                          ? 'opacity-60 border-[#E8EDE5]'
                          : 'hover:shadow-md'
                    }`}
                  >
                    <div className="flex items-start justify-between gap-3">
                      <div>
                        <div className="flex items-center gap-2">
                          <h4 className="font-semibold text-sm text-[#28352D]">{prop.title}</h4>
                          <Pill tone={isAccepted ? 'green' : prop.feasibility === 'High' ? 'green' : 'amber'}>
                            {isAccepted ? 'Accepted for Planning' : `${prop.feasibility} Feasibility`}
                          </Pill>
                        </div>
                        <p className="mt-1.5 text-xs text-[#6B7C70] leading-relaxed">
                          {prop.summary}
                        </p>
                      </div>
                    </div>

                    {/* Quick Metric Comparison Box */}
                    <div className="mt-4 grid grid-cols-3 gap-2 rounded-xl bg-[#F0F5ED] p-3 text-center text-xs">
                      <div>
                        <p className="text-[10px] text-[#78897D]">Distance Delta</p>
                        <p className="mt-0.5 font-bold text-[#285943]">
                          -{prop.estimatedDistanceReductionKm} km/day
                        </p>
                      </div>
                      <div>
                        <p className="text-[10px] text-[#78897D]">Fuel Savings</p>
                        <p className="mt-0.5 font-bold text-[#285943]">
                          ~{prop.estimatedFuelSavingsLiters} L/mo
                        </p>
                      </div>
                      <div>
                        <p className="text-[10px] text-[#78897D]">Estimated Cost</p>
                        <p className="mt-0.5 font-bold text-[#285943]">
                          ₹{prop.estimatedMonthlySavingsInr.toLocaleString('en-IN')}/mo
                        </p>
                      </div>
                    </div>

                    <div className="mt-4 flex flex-wrap items-center justify-between gap-2 border-t border-[#EEF3EC] pt-3">
                      <button
                        type="button"
                        onClick={() => {
                          setSelectedProposal(prop)
                          setIsComparisonModalOpen(true)
                        }}
                        className="flex items-center gap-1 text-xs font-semibold text-[#285943] hover:underline cursor-pointer"
                      >
                        <span>Compare Routes</span>
                        <ChevronRight size={14} />
                      </button>

                      <div className="flex items-center gap-2">
                        {!isAccepted && (
                          <button
                            type="button"
                            onClick={() => handleRejectProposal(prop.id)}
                            className="rounded-lg px-2.5 py-1 text-xs text-[#994734] hover:bg-[#FDF2F0] cursor-pointer"
                          >
                            Reject
                          </button>
                        )}
                        <Button
                          variant={isAccepted ? 'secondary' : 'primary'}
                          onClick={() => handleAcceptProposal(prop.id)}
                          className="text-xs px-3 py-1.5"
                          disabled={isAccepted}
                        >
                          {isAccepted ? 'Planned' : 'Accept for Planning'}
                        </Button>
                      </div>
                    </div>
                  </Card>
                )
              })}
            </div>
          )}
        </div>
      </div>

      {/* AI Transport Advisor Section */}
      <ModuleAiAdvisor
        category="transportation"
        title="AI Transport Advisor"
        subtitle="Ask questions about travel patterns, fuel usage, student transportation, and route optimization."
        suggestedQuestions={[
          'Which route consumes the most fuel?',
          'Which buses have low occupancy?',
          'Can any of my routes be combined?',
          'How can I reduce transportation emissions?',
          'Compare the current routes with the proposed optimized routes.',
          'Which routes carry the most students per kilometre?',
        ]}
        onQuery={(q) => aiAdvisorsService.queryTransportationAdvisor(q, records, routes, proposals)}
        emptyStateDescription="Ask questions about passenger density, route mileage, fuel economics, and consolidation criteria. The assistant evaluates active bus routes and logged fleet travel."
      />

      {/* Transportation Record Modal */}
      <TransportationRecordModal
        isOpen={isRecordModalOpen}
        onClose={() => setIsRecordModalOpen(false)}
        onSave={handleSaveRecord}
        initialRecord={editingRecord}
      />

      {/* Bus Route Modal */}
      <BusRouteModal
        isOpen={isRouteModalOpen}
        onClose={() => setIsRouteModalOpen(false)}
        onSave={handleSaveRoute}
        initialRoute={editingRoute}
      />

      {/* Route Comparison Modal */}
      <RouteComparisonModal
        proposal={selectedProposal}
        isOpen={isComparisonModalOpen}
        onClose={() => setIsComparisonModalOpen(false)}
        onAccept={handleAcceptProposal}
        onReject={handleRejectProposal}
      />
    </div>
  )
}
