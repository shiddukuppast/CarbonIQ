'use client'

import React from 'react'

export interface PageTitleProps {
  eyebrow: string
  title: string
  description: string
  action?: React.ReactNode
}

export function PageTitle({ eyebrow, title, description, action }: PageTitleProps) {
  return (
    <div className="flex flex-col justify-between gap-4 sm:flex-row sm:items-end">
      <div>
        <p className="text-[10px] font-semibold uppercase tracking-[.16em] text-[#4D6354]">
          {eyebrow}
        </p>
        <h1 className="mt-2 text-3xl font-semibold tracking-[-.05em] text-[#2F4436] sm:text-4xl">
          {title}
        </h1>
        <p className="mt-2 max-w-[600px] text-sm leading-6 text-[#4B5E51]">{description}</p>
      </div>
      {action}
    </div>
  )
}
