'use client'

import React from 'react'
import { cn } from '@/lib/utils'

export interface CardProps {
  children: React.ReactNode
  className?: string
}

export function Card({ children, className }: CardProps) {
  return (
    <section
      className={cn(
        'rounded-2xl border border-[#E0E7DE] bg-white shadow-[0_8px_24px_rgba(43,73,53,.035)]',
        className
      )}
    >
      {children}
    </section>
  )
}
