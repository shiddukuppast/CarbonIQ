'use client'

import React from 'react'
import { useRouter } from 'next/navigation'
import { ArrowRight, Leaf, Play, Sparkles } from 'lucide-react'
import { EmissionsLineChart } from '@/components/charts/EmissionsLineChart'
import { Button } from '@/components/ui/button'
import { MiniSpark } from '@/components/ui/MiniSpark'
import { Pill } from '@/components/ui/Pill'
import { DEFAULT_MONTHLY_EMISSIONS } from '@/lib/constants'

export function HeroSection() {
  const router = useRouter()

  const handleExploreDemo = () => {
    router.push('/dashboard')
  }

  return (
    <section className="mx-auto grid max-w-[1240px] items-center gap-12 px-6 pb-20 pt-14 lg:grid-cols-[1.02fr_.98fr] lg:px-8 lg:pb-28 lg:pt-20">
      <div>
        <Pill>THE SUSTAINABILITY OPERATING SYSTEM</Pill>
        <h1 className="mt-6 max-w-[610px] text-5xl font-semibold leading-[1.04] tracking-[-0.06em] text-[#234A36] sm:text-6xl lg:text-[74px]">
          Make every resource <span className="text-[#3B6B38]">count.</span>
        </h1>
        <p className="mt-6 max-w-[530px] text-lg leading-8 text-[#445A4B]">
          Understand your environmental impact, uncover hidden inefficiencies, and discover smarter
          ways to save energy, reduce costs, and build a sustainable future.
        </p>
        <div className="mt-8 flex flex-wrap gap-3">
          <Button onClick={handleExploreDemo} className="px-5 py-3">
            Explore the demo <ArrowRight size={16} />
          </Button>
          <Button variant="secondary" onClick={handleExploreDemo} className="px-5 py-3">
            <Play size={15} fill="currentColor" /> See how it works
          </Button>
        </div>
        <p className="mt-4 text-xs text-[#4D6253] font-medium">
          No account required · Frontend demonstration mode
        </p>
      </div>

      <div className="relative mx-auto w-full max-w-[560px]">
        <div className="absolute -inset-4 rounded-[32px] bg-[#E7F1E5] blur-2xl" />
        <div className="relative overflow-hidden rounded-[28px] border border-[#D9E5D7] bg-[#EAF3E7] p-4 shadow-[0_22px_60px_rgba(56,99,65,.13)]">
          <div className="rounded-[21px] border border-white/70 bg-white/80 p-5 backdrop-blur-sm">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-[10px] font-semibold uppercase tracking-[.16em] text-[#4D6253]">
                  Impact overview
                </p>
                <p className="mt-1 text-2xl font-semibold tracking-[-.04em] text-[#285943]">
                  Your footprint
                </p>
              </div>
              <span className="grid h-9 w-9 place-items-center rounded-xl bg-[#E7F1E5] text-[#285943]">
                <Leaf size={17} />
              </span>
            </div>

            <div className="mt-5 grid grid-cols-3 gap-2">
              <div className="rounded-xl bg-[#F5F8F3] p-3">
                <p className="text-[10px] font-medium text-[#4D6253]">Emissions</p>
                <p className="mt-2 text-lg font-semibold text-[#285943]">2.48t</p>
                <MiniSpark />
              </div>
              <div className="rounded-xl bg-[#F5F8F3] p-3">
                <p className="text-[10px] font-medium text-[#4D6253]">Savings</p>
                <p className="mt-2 text-lg font-semibold text-[#285943]">₹6.8k</p>
                <span className="text-[11px] font-medium text-[#2E6B47]">Estimated</span>
              </div>
              <div className="rounded-xl bg-[#F5F8F3] p-3">
                <p className="text-[10px] font-medium text-[#4D6253]">Goal</p>
                <p className="mt-2 text-lg font-semibold text-[#285943]">34%</p>
                <span className="text-[11px] font-medium text-[#2E6B47]">On track</span>
              </div>
            </div>

            <div className="mt-5 rounded-xl border border-[#E4ECE1] bg-white p-4">
              <div className="flex items-center justify-between">
                <p className="text-xs font-semibold text-[#3D5244]">Monthly emissions</p>
                <span className="text-[10px] font-medium text-[#4D6253]">kg CO₂e</span>
              </div>
              <EmissionsLineChart data={DEFAULT_MONTHLY_EMISSIONS} height={132} showAxes={false} />
            </div>

            <div className="mt-4 flex items-center gap-3 rounded-xl bg-[#285943] p-3.5 text-white">
              <span className="grid h-8 w-8 place-items-center rounded-lg bg-white/15">
                <Sparkles size={15} />
              </span>
              <div>
                <p className="text-xs font-medium">A little goes a long way</p>
                <p className="mt-0.5 text-[10px] text-[#D5E5D3]">3 actions could save ~₹2,140 monthly</p>
              </div>
              <ArrowRight size={15} className="ml-auto text-white/80" />
            </div>
          </div>
        </div>
      </div>
    </section>
  )
}
