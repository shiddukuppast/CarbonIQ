'use client'

import React from 'react'
import { AudienceSection } from './AudienceSection'
import { CtaSection } from './CtaSection'
import { FeaturesSection } from './FeaturesSection'
import { HeroSection } from './HeroSection'
import { HowItWorksSection } from './HowItWorksSection'
import { LandingFooter } from './LandingFooter'
import { LandingHeader } from './LandingHeader'
import { StatsSection } from './StatsSection'

export function LandingPage() {
  return (
    <div className="min-h-screen bg-[#F7F8F2] text-[#28352D]">
      <LandingHeader />
      <main>
        <HeroSection />
        <StatsSection />
        <FeaturesSection />
        <HowItWorksSection />
        <AudienceSection />
        <CtaSection />
      </main>
      <LandingFooter />
    </div>
  )
}
