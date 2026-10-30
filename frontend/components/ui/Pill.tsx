'use client'

import React from 'react'
import { cn } from '@/lib/utils'

export interface PillProps {
  children: React.ReactNode
  tone?: 'green' | 'amber' | 'sage'
  className?: string
}

export function Pill({ children, tone = 'green', className }: PillProps) {
  const toneClasses =
    tone === 'amber'
      ? 'bg-[#FBF1D8] text-[#7A5A1B] font-semibold'
      : tone === 'sage'
        ? 'bg-[#EDF2EA] text-[#344D3B] font-semibold'
        : 'bg-[#E7F1E5] text-[#285943] font-semibold'

  return (
    <span
      className={cn(
        'inline-flex items-center rounded-full px-2.5 py-1 text-[11px] tracking-wide',
        toneClasses,
        className
      )}
    >
      {children}
    </span>
  )
}
