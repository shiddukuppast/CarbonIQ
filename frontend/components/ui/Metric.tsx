'use client'

import React from 'react'
import { Card } from './Card'
import type { Tone } from '@/types/dashboard'

export interface MetricProps {
  icon: React.ElementType
  label: string
  value: string
  unit?: string
  trend?: React.ReactNode
  tone?: Tone
  note?: string
}

export function Metric({
  icon: Icon,
  label,
  value,
  unit,
  trend,
  tone = 'green',
  note,
}: MetricProps) {
  const bg = {
    green: 'bg-[#E7F1E5] text-[#285943]',
    olive: 'bg-[#F2F1DF] text-[#767840]',
    sage: 'bg-[#EDF2EA] text-[#60745F]',
    amber: 'bg-[#FBF1D8] text-[#8A6C2E]',
  }[tone]

  return (
    <Card className="p-4 sm:p-5">
      <div className="flex items-start justify-between">
        <span className={`grid h-9 w-9 place-items-center rounded-xl ${bg}`}>
          <Icon size={17} />
        </span>
        {trend}
      </div>
      <p className="mt-5 text-xs text-[#7D8A80]">{label}</p>
      <p className="mt-1 text-2xl font-semibold tracking-[-.05em] text-[#2F4436]">
        {value}
        {unit && <span className="ml-1 text-xs font-normal tracking-normal text-[#8A978D]">{unit}</span>}
      </p>
      {note && <p className="mt-2 text-[11px] text-[#8D9A90]">{note}</p>}
    </Card>
  )
}
