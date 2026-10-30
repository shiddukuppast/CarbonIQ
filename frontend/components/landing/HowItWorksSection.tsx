'use client'

import React from 'react'
import { Pill } from '@/components/ui/Pill'

const steps = [
  { num: '01', title: 'Track', desc: 'Bring electricity, travel, and waste data into one place.' },
  { num: '02', title: 'Understand', desc: 'See your footprint, cost drivers, and trends at a glance.' },
  { num: '03', title: 'Improve', desc: 'Explore practical actions with transparent assumptions.' },
  { num: '04', title: 'Measure', desc: 'Follow progress and report outcomes with confidence.' },
]

export function HowItWorksSection() {
  return (
    <section id="how" className="bg-[#E7F1E5] py-20 lg:py-24">
      <div className="mx-auto max-w-[1240px] px-6 lg:px-8">
        <div className="flex flex-col justify-between gap-4 sm:flex-row sm:items-end">
          <div>
            <Pill>HOW IT WORKS</Pill>
            <h2 className="mt-4 text-4xl font-semibold tracking-[-.05em] text-[#234A36]">
              From data to direction.
            </h2>
          </div>
          <p className="max-w-[300px] text-sm leading-6 text-[#3B5442]">
            A repeatable loop for better decisions, not another dashboard to babysit.
          </p>
        </div>

        <div className="mt-12 grid gap-8 md:grid-cols-4">
          {steps.map(({ num, title, desc }) => (
            <div key={num} className="relative border-t border-[#B8CFB4] pt-5">
              <span className="text-xs font-bold tracking-[.14em] text-[#285943]">{num}</span>
              <h3 className="mt-5 text-lg font-semibold text-[#1F3D2C]">{title}</h3>
              <p className="mt-2 text-sm leading-6 text-[#3E5244]">{desc}</p>
            </div>
          ))}
        </div>
      </div>
    </section>
  )
}
