'use client'

import React from 'react'
import { useRouter } from 'next/navigation'
import { Lock, X } from 'lucide-react'
import { Button } from './button'
import { Pill } from './Pill'

export interface DemoAccessModalProps {
  isOpen: boolean
  onClose: () => void
  customMessage?: string
}

export function DemoAccessModal({ isOpen, onClose, customMessage }: DemoAccessModalProps) {
  const router = useRouter()

  if (!isOpen) return null

  const handleSignIn = () => {
    onClose()
    router.push('/signin')
  }

  const handleSignUp = () => {
    onClose()
    router.push('/signup')
  }

  return (
    <div
      role="dialog"
      aria-modal="true"
      aria-labelledby="demo-access-title"
      className="fixed inset-0 z-50 flex items-center justify-center bg-[#234A36]/40 p-4 backdrop-blur-xs animate-in fade-in duration-200"
    >
      <div className="relative w-full max-w-md rounded-2xl border border-[#E0E7DE] bg-white p-6 shadow-2xl sm:p-8">
        <button
          type="button"
          onClick={onClose}
          aria-label="Close dialog"
          className="absolute right-4 top-4 rounded-lg p-1.5 text-[#7A887D] hover:bg-[#F3F7F1] hover:text-[#285943]"
        >
          <X size={18} />
        </button>

        <div className="flex items-center gap-3">
          <span className="grid h-10 w-10 place-items-center rounded-xl bg-[#E7F1E5] text-[#285943]">
            <Lock size={19} />
          </span>
          <Pill tone="amber">DEMO MODE ACCESS</Pill>
        </div>

        <h2 id="demo-access-title" className="mt-4 text-xl font-semibold tracking-[-0.03em] text-[#234A36]">
          Action Restricted in Demo Mode
        </h2>

        <p className="mt-2 text-sm leading-6 text-[#6B7B6F]">
          {customMessage ||
            "You're exploring CarbonIQ in demo mode. Sign in or create an account to add and manage your own sustainability data."}
        </p>

        <div className="mt-6 flex flex-col gap-2.5 sm:flex-row sm:items-center">
          <Button onClick={handleSignIn} className="w-full sm:flex-1">
            Sign in
          </Button>
          <Button variant="secondary" onClick={handleSignUp} className="w-full sm:flex-1">
            Create account
          </Button>
        </div>

        <div className="mt-4 text-center">
          <button
            type="button"
            onClick={onClose}
            className="text-xs text-[#7A887D] hover:text-[#285943]"
          >
            Continue exploring in read-only demo mode
          </button>
        </div>
      </div>
    </div>
  )
}
