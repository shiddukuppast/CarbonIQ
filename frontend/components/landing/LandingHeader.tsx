'use client'

import React from 'react'
import { useRouter } from 'next/navigation'
import { ArrowRight } from 'lucide-react'
import { Button } from '@/components/ui/button'
import { Logo } from '@/components/ui/Logo'

export function LandingHeader() {
  const router = useRouter()

  return (
    <header className="mx-auto flex max-w-[1240px] items-center justify-between px-6 py-5 lg:px-8">
      <Logo onClick={() => router.push('/')} />
      <nav className="hidden items-center gap-8 text-sm font-medium text-[#4D6053] md:flex">
        <a href="#features" className="hover:text-[#285943]">
          Features
        </a>
        <a href="#how" className="hover:text-[#285943]">
          How it works
        </a>
        <a href="#audience" className="hover:text-[#285943]">
          Who it&apos;s for
        </a>
        <a href="#about" className="hover:text-[#285943]">
          About
        </a>
      </nav>
      <div className="flex items-center gap-2">
        <Button variant="ghost" onClick={() => router.push('/signin')}>
          Sign in
        </Button>
        <Button onClick={() => router.push('/signup')}>
          Get started <ArrowRight size={15} />
        </Button>
      </div>
    </header>
  )
}
