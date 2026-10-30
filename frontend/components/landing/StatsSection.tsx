'use client'

import React from 'react'

export function StatsSection() {
  return (
    <section className="border-y border-[#E4EADF] bg-white/70">
      <div className="mx-auto grid max-w-[1240px] grid-cols-1 gap-5 px-6 py-7 sm:grid-cols-3 lg:px-8">
        <div className="flex items-center gap-3 sm:border-r sm:border-[#E1E8DF]">
          <span className="text-3xl font-semibold tracking-[-.06em] text-[#285943]">12.4M+</span>
          <span className="text-xs leading-4 text-[#485C4E] font-medium">
            kWh of energy
            <br />
            monitored
          </span>
        </div>
        <div className="flex items-center gap-3 sm:border-r sm:border-[#E1E8DF] sm:pl-6">
          <span className="text-3xl font-semibold tracking-[-.06em] text-[#285943]">18.6k</span>
          <span className="text-xs leading-4 text-[#485C4E] font-medium">
            resource records
            <br />
            optimized
          </span>
        </div>
        <div className="flex items-center gap-3 sm:pl-6">
          <span className="text-3xl font-semibold tracking-[-.06em] text-[#285943]">4.2k</span>
          <span className="text-xs leading-4 text-[#485C4E] font-medium">
            tonnes of impact
            <br />
            tracked
          </span>
        </div>
      </div>
    </section>
  )
}
