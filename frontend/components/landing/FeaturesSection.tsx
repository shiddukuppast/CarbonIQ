'use client'

import React from 'react'
import { BrainCircuit, BusFront, Cloud, Recycle, Wallet, Zap } from 'lucide-react'
import { Card } from '@/components/ui/Card'
import { Pill } from '@/components/ui/Pill'

const features = [
  {
    icon: Zap,
    title: 'Smart electricity',
    desc: 'See what drives consumption and where simple changes make a measurable difference.',
  },
  {
    icon: BusFront,
    title: 'Transportation & fuel',
    desc: 'Understand fleet efficiency, routes, and the cost of getting from A to B.',
  },
  {
    icon: Recycle,
    title: 'Waste management',
    desc: 'Move beyond collection numbers with better segregation and recovery.',
  },
  {
    icon: BrainCircuit,
    title: 'Practical insights',
    desc: 'Rule-based recommendations that turn patterns into next best actions.',
  },
  {
    icon: Cloud,
    title: 'Carbon footprint',
    desc: 'Track your impact across resource categories with one shared baseline.',
  },
  {
    icon: Wallet,
    title: 'Cost & savings',
    desc: 'Model the financial upside of more sustainable operating decisions.',
  },
]

export function FeaturesSection() {
  return (
    <section id="features" className="mx-auto max-w-[1240px] px-6 py-20 lg:px-8 lg:py-28">
      <div className="max-w-[620px]">
        <Pill>ONE CLEAR VIEW</Pill>
        <h2 className="mt-4 text-4xl font-semibold tracking-[-.05em] text-[#234A36]">
          Turn scattered data into <span className="text-[#3B6B38]">clear action.</span>
        </h2>
        <p className="mt-4 text-[#4D6053] leading-relaxed">
          CarbonIQ brings the everyday decisions behind your footprint into one calm, connected
          workspace.
        </p>
      </div>

      <div className="mt-10 grid gap-4 md:grid-cols-2 lg:grid-cols-3">
        {features.map(({ icon: Icon, title, desc }) => (
          <Card
            key={title}
            className="group p-5 transition-all hover:-translate-y-1 hover:border-[#B8CFB4] hover:shadow-[0_14px_30px_rgba(43,73,53,.08)]"
          >
            <span className="grid h-10 w-10 place-items-center rounded-xl bg-[#E7F1E5] text-[#285943]">
              <Icon size={19} />
            </span>
            <h3 className="mt-5 font-semibold text-[#2F4436]">{title}</h3>
            <p className="mt-2 text-sm leading-6 text-[#4E6254]">{desc}</p>
          </Card>
        ))}
      </div>
    </section>
  )
}
