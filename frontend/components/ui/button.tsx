'use client'

import React from 'react'
import { cn } from '@/lib/utils'

export interface ButtonProps extends React.ButtonHTMLAttributes<HTMLButtonElement> {
  children: React.ReactNode
  variant?: 'primary' | 'secondary' | 'ghost' | 'white'
  className?: string
}

export function Button({
  children,
  variant = 'primary',
  onClick,
  className,
  type = 'button',
  disabled,
  ...props
}: ButtonProps) {
  const variantStyles =
    variant === 'primary'
      ? 'bg-[#285943] text-white shadow-[0_7px_18px_rgba(40,89,67,.18)] hover:bg-[#1F4635] focus-visible:ring-2 focus-visible:ring-[#285943]/40'
      : variant === 'secondary'
        ? 'border border-[#DCE6DA] bg-white text-[#285943] hover:bg-[#F3F7F1] focus-visible:ring-2 focus-visible:ring-[#285943]/30'
        : variant === 'white'
          ? 'bg-white text-[#285943] hover:bg-[#F0F5ED] shadow-sm focus-visible:ring-2 focus-visible:ring-white/80'
          : 'text-[#3E5244] font-medium hover:bg-[#EDF2EA] hover:text-[#1F4635] focus-visible:ring-2 focus-visible:ring-[#285943]/20'

  return (
    <button
      type={type}
      onClick={onClick}
      disabled={disabled}
      className={cn(
        'inline-flex items-center justify-center gap-2 rounded-xl px-4 py-2.5 text-sm font-medium transition-all active:scale-[.98] disabled:opacity-50 disabled:pointer-events-none outline-none cursor-pointer',
        variantStyles,
        className
      )}
      {...props}
    >
      {children}
    </button>
  )
}
