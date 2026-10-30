'use client'

import React, { useState } from 'react'
import { useRouter } from 'next/navigation'
import { Building2, Check, GraduationCap, User } from 'lucide-react'
import { Button } from '@/components/ui/button'
import { Card } from '@/components/ui/Card'
import { Logo } from '@/components/ui/Logo'
import { Pill } from '@/components/ui/Pill'
import { useAuth } from '@/context/auth-context'
import { isValidEmail } from '@/lib/validation'
import type { AccountType, AuthMode } from '@/types/auth'

export interface AuthFormProps {
  mode: AuthMode
}

interface RoleOption {
  id: AccountType
  label: string
  description: string
  icon: React.ElementType
}

const ROLE_OPTIONS: RoleOption[] = [
  {
    id: 'individual',
    label: 'Individual / Student',
    description: 'Track personal sustainability, energy usage, and waste.',
    icon: User,
  },
  {
    id: 'college',
    label: 'College',
    description: 'Manage campus sustainability, student transportation, and bus routes.',
    icon: GraduationCap,
  },
  {
    id: 'organization',
    label: 'Organization',
    description: 'Monitor organizational sustainability, resource usage, and transportation.',
    icon: Building2,
  },
]

export function AuthForm({ mode }: AuthFormProps) {
  const router = useRouter()
  const { signIn, signUp } = useAuth()
  const isSignup = mode === 'signup'

  const [name, setName] = useState('')
  const [email, setEmail] = useState('')
  const [password, setPassword] = useState('')
  const [confirmPassword, setConfirmPassword] = useState('')
  const [accountType, setAccountType] = useState<AccountType>('individual')
  const [workspaceName, setWorkspaceName] = useState('')
  const [error, setError] = useState('')
  const [submitted, setSubmitted] = useState(false)

  const submit = async (event: React.FormEvent<HTMLFormElement>) => {
    event.preventDefault()
    setError('')

    if (isSignup && !name.trim()) {
      return setError('Please enter your full name.')
    }
    if (!isValidEmail(email)) {
      return setError('Please enter a valid email address.')
    }
    if (!password) {
      return setError('Please enter a password.')
    }
    if (isSignup && password.length < 8) {
      return setError('Password must be at least 8 characters long.')
    }
    if (isSignup && password !== confirmPassword) {
      return setError('Passwords do not match.')
    }
    if (isSignup && !accountType) {
      return setError('Please select how you will use CarbonIQ.')
    }

    setSubmitted(true)

    try {
      if (isSignup) {
        await signUp({
          name: name.trim(),
          email: email.trim(),
          password,
          accountType,
          workspaceName: workspaceName.trim() || undefined,
        })
      } else {
        await signIn(email.trim(), password)
      }

      router.push('/dashboard')
    } catch (err: any) {
      setSubmitted(false)
      const msg = err.message || 'Authentication failed. Please check your credentials and try again.'
      setError(msg)
    }
  }

  return (
    <main className="flex min-h-screen items-center justify-center bg-[#F7F8F2] px-5 py-10">
      <div className={`w-full ${isSignup ? 'max-w-lg' : 'max-w-md'}`}>
        <Logo onClick={() => router.push('/')} />
        <Card className="mt-8 p-6 sm:p-8">
          <Pill>{isSignup ? 'CREATE YOUR WORKSPACE' : 'WELCOME BACK'}</Pill>
          <h1 className="mt-4 text-3xl font-semibold tracking-[-.05em] text-[#234A36]">
            {isSignup ? 'Start with a clearer picture.' : 'Sign in to CarbonIQ.'}
          </h1>
          <p className="mt-2 text-sm leading-6 text-[#7A887D]">
            Frontend demonstration mode. Simulated authenticated session.
          </p>

          <form onSubmit={submit} className="mt-7 space-y-4" noValidate>
            {isSignup && (
              <label className="block text-sm text-[#536458]">
                Full name
                <input
                  className="field"
                  value={name}
                  onChange={(e) => {
                    setName(e.target.value)
                    if (error === 'Please enter your full name.' && e.target.value.trim()) {
                      setError('')
                    }
                  }}
                />
              </label>
            )}

            <label className="block text-sm text-[#536458]">
              Email
              <input
                className="field"
                type="email"
                value={email}
                onChange={(e) => {
                  const val = e.target.value
                  setEmail(val)
                  if (error === 'Please enter a valid email address.' && isValidEmail(val)) {
                    setError('')
                  }
                }}
              />
            </label>

            <label className="block text-sm text-[#536458]">
              Password
              <input
                className="field"
                type="password"
                value={password}
                onChange={(e) => {
                  const val = e.target.value
                  setPassword(val)
                  if (error === 'Please enter a password.' && val) {
                    setError('')
                  } else if (error === 'Passwords do not match.' && val === confirmPassword) {
                    setError('')
                  }
                }}
              />
            </label>

            {isSignup && (
              <>
                <label className="block text-sm text-[#536458]">
                  Confirm password
                  <input
                    className="field"
                    type="password"
                    value={confirmPassword}
                    onChange={(e) => {
                      const val = e.target.value
                      setConfirmPassword(val)
                      if (error === 'Passwords do not match.' && val === password) {
                        setError('')
                      }
                    }}
                  />
                </label>

                {/* Role / Account Type Selector */}
                <div className="pt-2">
                  <label className="block text-sm font-medium text-[#405448] mb-2">
                    How will you use CarbonIQ? <span className="text-[#B95D47]">*</span>
                  </label>
                  <div className="space-y-2.5" role="radiogroup" aria-label="How will you use CarbonIQ?">
                    {ROLE_OPTIONS.map((opt) => {
                      const isSelected = accountType === opt.id
                      const Icon = opt.icon
                      return (
                        <div
                          key={opt.id}
                          role="radio"
                          aria-checked={isSelected}
                          tabIndex={0}
                          onClick={() => setAccountType(opt.id)}
                          onKeyDown={(e) => {
                            if (e.key === ' ' || e.key === 'Enter') {
                              e.preventDefault()
                              setAccountType(opt.id)
                            }
                          }}
                          className={`flex items-start gap-3 rounded-xl p-3 border transition-all cursor-pointer text-left ${
                            isSelected
                              ? 'border-[#285943] bg-[#F2F7F1] shadow-xs ring-1 ring-[#285943]'
                              : 'border-[#E0E7DE] bg-white hover:bg-[#F9FAF7] hover:border-[#CCD8C8]'
                          }`}
                        >
                          <div
                            className={`mt-0.5 grid h-9 w-9 shrink-0 place-items-center rounded-lg transition-colors ${
                              isSelected ? 'bg-[#285943] text-white' : 'bg-[#EAEFE8] text-[#55695B]'
                            }`}
                          >
                            <Icon size={18} strokeWidth={2} />
                          </div>
                          <div className="flex-1 min-w-0">
                            <div className="flex items-center justify-between">
                              <span className={`text-sm font-semibold ${isSelected ? 'text-[#234A36]' : 'text-[#3B4C41]'}`}>
                                {opt.label}
                              </span>
                              <div
                                className={`h-4 w-4 rounded-full border grid place-items-center transition-colors ${
                                  isSelected
                                    ? 'border-[#285943] bg-[#285943] text-white'
                                    : 'border-[#BDC7BC] bg-white'
                                }`}
                              >
                                {isSelected && <Check size={10} strokeWidth={3} />}
                              </div>
                            </div>
                            <p className="mt-0.5 text-xs text-[#728277] leading-relaxed">
                              {opt.description}
                            </p>
                          </div>
                        </div>
                      )
                    })}
                  </div>
                </div>

                <label className="block text-sm text-[#536458] pt-1">
                  Workspace name <span className="text-xs text-[#8A978D] font-normal">(optional)</span>
                  <input
                    className="field"
                    placeholder="e.g., Campus Operations or Green Living"
                    value={workspaceName}
                    onChange={(e) => setWorkspaceName(e.target.value)}
                  />
                </label>
              </>
            )}

            {error && (
              <p
                role="alert"
                className="rounded-lg bg-[#FBF1D8] px-3 py-2 text-xs text-[#8A6C2E] animate-in fade-in"
              >
                {error}
              </p>
            )}

            <Button type="submit" className="w-full">
              {submitted
                ? 'Opening workspace…'
                : isSignup
                  ? 'Create workspace'
                  : 'Sign in'}
            </Button>
          </form>

          <div className="mt-5 flex justify-between text-xs text-[#7A887D]">
            <button
              type="button"
              onClick={() => router.push('/')}
              className="hover:text-[#285943] cursor-pointer"
            >
              Back to home
            </button>
            {isSignup ? (
              <button
                type="button"
                onClick={() => router.push('/signin')}
                className="font-medium text-[#285943] cursor-pointer"
              >
                Already have an account? Sign in
              </button>
            ) : (
              <button
                type="button"
                onClick={() => router.push('/signup')}
                className="font-medium text-[#285943] cursor-pointer"
              >
                Sign up
              </button>
            )}
          </div>
        </Card>
      </div>
    </main>
  )
}
