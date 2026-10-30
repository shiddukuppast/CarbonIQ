'use client'

import React from 'react'
import { useRouter } from 'next/navigation'
import { Logo } from '@/components/ui/Logo'

export function LandingFooter() {
  const router = useRouter()

  return (
    <footer className="border-t border-[#E0E7DE] px-6 py-7">
      <div className="mx-auto flex max-w-[1240px] flex-col justify-between gap-4 text-xs text-[#4D6053] sm:flex-row">
        <Logo onClick={() => router.push('/')} />
        <span>CarbonIQ · A sustainability management platform for better everyday decisions.</span>
        <span>Demo data only · 2026</span>
      </div>
    </footer>
  )
}
