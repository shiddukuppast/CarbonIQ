'use client'

import React from 'react'
import { useRouter } from 'next/navigation'
import { ArrowRight, Droplets, Target, UserRound } from 'lucide-react'
import { Pill } from '@/components/ui/Pill'

const audienceOptions: {
  title: string
  desc: string
  icon: React.ElementType
}[] = [
  {
    title: 'Individuals & Households',
    desc: 'Make small shifts that add up at home, on the road, and in your everyday routines.',
    icon: UserRound,
  },
  {
    title: 'Colleges & Campuses',
    desc: 'Coordinate buildings, departments, campus mobility, and student-led initiatives.',
    icon: Droplets,
  },
  {
    title: 'Teams & Organizations',
    desc: 'Connect office operations, fleet efficiency, costs, and sustainability reporting.',
    icon: Target,
  },
]

export function AudienceSection() {
  const router = useRouter()

  const handleExplore = () => {
    router.push('/dashboard')
  }

  return (
    <section id="audience" className="mx-auto max-w-[1240px] px-6 py-20 lg:px-8 lg:py-28">
      <div className="text-center">
        <Pill>BUILT FOR YOUR CONTEXT</Pill>
        <h2 className="mt-4 text-4xl font-semibold tracking-[-.05em] text-[#234A36]">
          One platform, <span className="text-[#3B6B38]">your priorities.</span>
        </h2>
      </div>

      <div className="mt-10 grid gap-4 md:grid-cols-3">
        {audienceOptions.map(({ title, desc, icon: Icon }) => (
          <button
            key={title}
            type="button"
            onClick={handleExplore}
            className="rounded-2xl border border-[#E0E7DE] bg-white p-6 text-left transition-all hover:-translate-y-1 hover:border-[#9DBB99] hover:shadow-[0_14px_30px_rgba(43,73,53,.08)] cursor-pointer"
          >
            <span className="grid h-11 w-11 place-items-center rounded-xl bg-[#F0F5ED] text-[#285943]">
              <Icon size={20} />
            </span>
            <h3 className="mt-6 text-lg font-semibold text-[#2F4436]">{title}</h3>
            <p className="mt-2 text-sm leading-6 text-[#4E6254]">{desc}</p>
            <span className="mt-6 inline-flex items-center gap-1 text-sm font-medium text-[#285943]">
              Explore workspace <ArrowRight size={15} />
            </span>
          </button>
        ))}
      </div>
    </section>
  )
}
