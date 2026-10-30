'use client'

import React from 'react'
import { Leaf } from 'lucide-react'

export interface LogoProps {
  light?: boolean
  onClick?: () => void
}

export function Logo({ light = false, onClick }: LogoProps) {
  const content = (
    <>
      <span className="grid h-9 w-9 place-items-center rounded-xl bg-[#E7F1E5]">
        <Leaf size={20} strokeWidth={2.2} className="text-[#285943]" />
      </span>
      <span className="text-[19px] font-semibold tracking-[-0.04em]">
        Carbon<span className="font-normal">IQ</span>
      </span>
    </>
  )

  return onClick ? (
    <button
      type="button"
      onClick={onClick}
      aria-label="CarbonIQ home"
      className={`flex items-center gap-2.5 ${light ? 'text-white' : 'text-[#285943]'}`}
    >
      {content}
    </button>
  ) : (
    <div className={`flex items-center gap-2.5 ${light ? 'text-white' : 'text-[#285943]'}`}>
      {content}
    </div>
  )
}
