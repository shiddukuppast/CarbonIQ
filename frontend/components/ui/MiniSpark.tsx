'use client'

import React from 'react'
import { TrendingDown, TrendingUp } from 'lucide-react'

export interface MiniSparkProps {
  up?: boolean
  percentage?: string
}

export function MiniSpark({ up = false, percentage }: MiniSparkProps) {
  const displayPercentage = percentage || (up ? '8.4%' : '12.6%')
  return (
    <span
      className={`inline-flex items-center gap-1 text-[11px] font-medium ${up ? 'text-[#A35C49]' : 'text-[#4B8A63]'}`}
    >
      {up ? <TrendingUp size={13} /> : <TrendingDown size={13} />} {displayPercentage}
    </span>
  )
}
