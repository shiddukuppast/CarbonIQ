'use client'

import React from 'react'
import Link from 'next/link'
import { useRouter } from 'next/navigation'
import { ArrowLeft, BusFront, ShieldAlert, Zap } from 'lucide-react'
import { Button } from '@/components/ui/button'
import { Card } from '@/components/ui/Card'
import { Pill } from '@/components/ui/Pill'
import { TransportationView } from '@/components/dashboard/TransportationView'
import { useAuth } from '@/context/auth-context'

export default function TransportationPage() {
  const router = useRouter()
  const { user, isHydrated } = useAuth()

  // Wait until session is hydrated to prevent flashes
  if (!isHydrated) {
    return (
      <div className="flex min-h-[400px] items-center justify-center p-8">
        <div className="text-sm text-[#748178] animate-pulse">Loading workspace modules…</div>
      </div>
    )
  }

  // Guard: If individual / student account, display access unavailable card
  if (user.accountType === 'individual') {
    return (
      <div className="mx-auto max-w-2xl px-4 py-16 sm:px-6">
        <Card className="p-8 text-center sm:p-10 border-[#E2EAE0] shadow-sm">
          <div className="mx-auto mb-4 grid h-14 w-14 place-items-center rounded-2xl bg-[#F6EFEA] text-[#B95D47]">
            <ShieldAlert size={28} strokeWidth={2} />
          </div>

          <Pill tone="amber">RESTRICTED MODULE</Pill>

          <h1 className="mt-4 text-2xl font-bold tracking-tight text-[#234A36] sm:text-3xl">
            Transportation Module Unavailable
          </h1>

          <p className="mt-3 text-sm leading-relaxed text-[#6E7E72]">
            Fleet tracking and Smart Bus Route Optimization are exclusive to{' '}
            <strong className="text-[#285943]">College</strong> and{' '}
            <strong className="text-[#285943]">Organization</strong> accounts. Your account is configured
            as an <strong className="text-[#285943]">Individual / Student</strong> workspace.
          </p>

          <div className="mt-6 rounded-xl border border-[#E7ECE5] bg-[#F9FBF8] p-4 text-left">
            <h2 className="text-xs font-semibold uppercase tracking-wider text-[#697A6D]">
              Included in your Individual Workspace:
            </h2>
            <ul className="mt-2 space-y-1.5 text-xs text-[#526256]">
              <li className="flex items-center gap-2">
                <span className="h-1.5 w-1.5 rounded-full bg-[#285943]" />
                Full Electricity consumption logging and tariff bill calculation
              </li>
              <li className="flex items-center gap-2">
                <span className="h-1.5 w-1.5 rounded-full bg-[#285943]" />
                Waste stream tracking with recycling diversion rates
              </li>
              <li className="flex items-center gap-2">
                <span className="h-1.5 w-1.5 rounded-full bg-[#285943]" />
                Dedicated AI Electricity and Waste Advisors
              </li>
            </ul>
          </div>

          <div className="mt-8 flex flex-wrap items-center justify-center gap-3">
            <Button
              type="button"
              onClick={() => router.push('/dashboard')}
              className="gap-2"
            >
              <ArrowLeft size={16} />
              Return to Overview
            </Button>
            <Link href="/dashboard/electricity">
              <Button type="button" variant="secondary" className="gap-2">
                <Zap size={16} />
                Open Electricity
              </Button>
            </Link>
          </div>
        </Card>
      </div>
    )
  }

  // College and Organization accounts have full access to Transportation & Route Optimization
  return <TransportationView />
}
