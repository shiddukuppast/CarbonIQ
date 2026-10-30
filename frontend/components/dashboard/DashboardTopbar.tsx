'use client'

import React, { useState } from 'react'
import { usePathname, useRouter } from 'next/navigation'
import { Bell, ChevronDown, LogOut, Menu, User } from 'lucide-react'
import { Pill } from '@/components/ui/Pill'
import { useAuth } from '@/context/auth-context'
import { DASHBOARD_NAV_ITEMS } from '@/lib/constants'
import { computeInitials } from '@/services/auth.service'

export interface DashboardTopbarProps {
  onOpenMobile: () => void
}

export function DashboardTopbar({ onOpenMobile }: DashboardTopbarProps) {
  const pathname = usePathname()
  const router = useRouter()
  const { session, user, signOut } = useAuth()
  const [profileDropdownOpen, setProfileDropdownOpen] = useState(false)

  const activeNavItem = DASHBOARD_NAV_ITEMS.find((n) => n.href === pathname)
  const isOverview = pathname === '/dashboard'

  const userName = user.name
  const initials = user.initials || computeInitials(userName)
  const isDemo = session.mode === 'demo' || !session.isAuthenticated

  const firstName = userName.split(' ')[0] || 'Aarav'
  const title = isOverview
    ? `Good morning, ${firstName}`
    : activeNavItem?.label || 'Settings'
  const subtitle = isOverview
    ? 'Here’s your sustainability snapshot for October.'
    : `Explore your ${(title || 'workspace').toLowerCase()} data and actions.`

  return (
    <header className="relative flex h-[76px] shrink-0 items-center justify-between border-b border-[#E0E7DE] bg-[#FBFCF8] px-5 sm:px-8">
      <div className="flex items-center gap-3">
        <button
          type="button"
          onClick={onOpenMobile}
          aria-label="Open mobile menu"
          className="rounded-lg p-2 text-[#617168] hover:bg-[#EEF3EC] lg:hidden cursor-pointer"
        >
          <Menu size={20} />
        </button>
        <div>
          <p
            className="text-lg font-semibold tracking-[-.03em] text-[#2F4436]"
            suppressHydrationWarning
          >
            {title}
          </p>
          <p className="mt-0.5 hidden text-xs text-[#8A978D] sm:block">{subtitle}</p>
        </div>
      </div>

      <div className="flex items-center gap-2 sm:gap-4">
        <div className="hidden items-center gap-2 rounded-lg border border-[#E0E7DE] bg-white px-3 py-2 text-xs text-[#65756A] sm:flex">
          <span className="h-1.5 w-1.5 rounded-full bg-[#8EAE83]" />
          Oct 2026
          <ChevronDown size={13} />
        </div>

        {isDemo ? (
          <button
            type="button"
            onClick={() => router.push('/signin')}
            className="hidden sm:inline-flex items-center gap-1.5 rounded-full bg-[#FBF1D8] px-3 py-1 text-[11px] font-medium text-[#8A6C2E] hover:bg-[#f6e7c1] transition-colors cursor-pointer"
          >
            <span>Demo Mode</span>
            <span className="font-semibold underline">Sign In</span>
          </button>
        ) : (
          <Pill tone="green" className="hidden sm:inline-flex">
            Authenticated
          </Pill>
        )}

        <button
          type="button"
          aria-label="Notifications"
          className="relative rounded-lg p-2 text-[#718076] hover:bg-[#EEF3EC] cursor-pointer"
        >
          <Bell size={18} />
          <span className="absolute right-1.5 top-1.5 h-1.5 w-1.5 rounded-full bg-[#B6B86B]" />
        </button>

        <div className="relative">
          <button
            type="button"
            onClick={() => setProfileDropdownOpen(!profileDropdownOpen)}
            aria-label="User profile options"
            className="grid h-9 w-9 place-items-center rounded-full bg-[#285943] text-xs font-semibold text-white cursor-pointer hover:bg-[#1F4635] transition-colors"
          >
            {initials}
          </button>

          {profileDropdownOpen && (
            <>
              <div
                className="fixed inset-0 z-30"
                onClick={() => setProfileDropdownOpen(false)}
                aria-hidden="true"
              />
              <div className="absolute right-0 top-11 z-40 w-56 rounded-xl border border-[#E0E7DE] bg-white p-2 shadow-xl animate-in fade-in duration-150">
                <div className="border-b border-[#EEF2EC] px-3 py-2">
                  <p className="truncate text-xs font-semibold text-[#285943]">{userName}</p>
                  <p className="truncate text-[10px] text-[#7A887D]">{user.email}</p>
                  {user.workspaceName && (
                    <p className="truncate text-[10px] text-[#8A978D] font-medium">
                      {user.workspaceName}
                    </p>
                  )}
                  <div className="mt-1.5 flex items-center gap-1.5">
                    <span
                      className={`inline-block h-2 w-2 rounded-full ${
                        !isDemo ? 'bg-[#4B8A63]' : 'bg-[#B6B86B]'
                      }`}
                    />
                    <span className="text-[10px] text-[#637568]">
                      {!isDemo ? 'Authenticated workspace' : 'Read-only demo'}
                    </span>
                  </div>
                </div>

                <div className="py-1">
                  <button
                    type="button"
                    onClick={() => {
                      setProfileDropdownOpen(false)
                      router.push('/dashboard/settings')
                    }}
                    className="flex w-full items-center gap-2 rounded-lg px-3 py-2 text-left text-xs text-[#526357] hover:bg-[#F3F7F1] cursor-pointer"
                  >
                    <User size={14} />
                    <span>Workspace settings</span>
                  </button>

                  {!isDemo ? (
                    <button
                      type="button"
                      onClick={() => {
                        setProfileDropdownOpen(false)
                        signOut()
                      }}
                      className="flex w-full items-center gap-2 rounded-lg px-3 py-2 text-left text-xs font-medium text-[#A35C49] hover:bg-[#FDF2F0] cursor-pointer"
                    >
                      <LogOut size={14} />
                      <span>Sign out</span>
                    </button>
                  ) : (
                    <button
                      type="button"
                      onClick={() => {
                        setProfileDropdownOpen(false)
                        router.push('/signin')
                      }}
                      className="flex w-full items-center gap-2 rounded-lg px-3 py-2 text-left text-xs font-medium text-[#285943] hover:bg-[#F0F5ED] cursor-pointer"
                    >
                      <User size={14} />
                      <span>Sign in to save records</span>
                    </button>
                  )}
                </div>
              </div>
            </>
          )}
        </div>
      </div>
    </header>
  )
}
