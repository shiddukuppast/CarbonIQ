'use client'

import React from 'react'
import Link from 'next/link'
import { usePathname, useRouter } from 'next/navigation'
import { Settings, X } from 'lucide-react'
import { Logo } from '@/components/ui/Logo'
import { Pill } from '@/components/ui/Pill'
import { useAuth } from '@/context/auth-context'
import { DASHBOARD_NAV_ITEMS } from '@/lib/constants'
import { computeInitials } from '@/services/auth.service'

export interface DashboardSidebarProps {
  isMobileOpen?: boolean
  onCloseMobile?: () => void
}

export function DashboardSidebar({
  isMobileOpen = false,
  onCloseMobile,
}: DashboardSidebarProps) {
  const pathname = usePathname()
  const router = useRouter()
  const { session, user } = useAuth()

  const userName = user.name
  const initials = user.initials || computeInitials(userName)
  const isDemo = session.mode === 'demo' || !session.isAuthenticated

  const isCurrentActive = (href: string) => {
    if (href === '/dashboard') {
      return pathname === '/dashboard'
    }
    return pathname.startsWith(href)
  }

  const sidebarContent = (
    <div className="flex h-full min-h-full flex-col px-4 py-5 justify-between overflow-y-auto">
      <div>
        <div className="flex items-center justify-between px-3">
          <Logo onClick={() => router.push('/')} />
          {onCloseMobile && (
            <button
              type="button"
              onClick={onCloseMobile}
              aria-label="Close menu"
              className="rounded-lg p-1.5 text-[#748178] hover:bg-[#F0F4EE] lg:hidden cursor-pointer"
            >
              <X size={18} />
            </button>
          )}
        </div>

        <div className="mt-8 px-3 flex items-center justify-between">
          <span className="text-[10px] font-semibold uppercase tracking-[.16em] text-[#9AA69C]">
            Workspace
          </span>
          <Pill tone={isDemo ? 'amber' : 'green'}>
            {isDemo ? 'Demo' : 'Active'}
          </Pill>
        </div>

        <nav className="mt-3 space-y-1">
          {DASHBOARD_NAV_ITEMS.filter((item) => {
            if (item.id === 'transportation') {
              return user.accountType === 'college' || user.accountType === 'organization'
            }
            return true
          }).map(({ id, label, href, icon: Icon }) => {
            const active = isCurrentActive(href)
            return (
              <Link
                key={id}
                href={href}
                onClick={onCloseMobile}
                className={`flex w-full items-center gap-3 rounded-xl px-3 py-2.5 text-left text-sm transition-colors ${
                  active
                    ? 'bg-[#E7F1E5] font-medium text-[#285943]'
                    : 'text-[#748178] hover:bg-[#F0F4EE] hover:text-[#285943]'
                }`}
              >
                <Icon size={17} strokeWidth={1.8} />
                {label}
              </Link>
            )
          })}
        </nav>
      </div>

      <div className="mt-auto pt-4 shrink-0">
        <Link
          href="/dashboard/settings"
          onClick={onCloseMobile}
          className={`flex w-full items-center gap-3 rounded-xl px-3 py-2.5 text-left text-sm ${
            pathname === '/dashboard/settings'
              ? 'bg-[#E7F1E5] text-[#285943] font-medium'
              : 'text-[#748178] hover:bg-[#F0F4EE] hover:text-[#285943]'
          }`}
        >
          <Settings size={17} />
          <span>Settings</span>
        </Link>

        {/* Bottom profile card: single fixed workspace profile without category switcher */}
        <div className="mt-4 rounded-2xl border border-[#E0E7DE] bg-white p-3 shadow-xs">
          <div className="flex items-center justify-between">
            <p className="text-[10px] font-semibold uppercase tracking-[.14em] text-[#9AA69C]">
              {isDemo ? 'Demo profile' : 'Active profile'}
            </p>
            <span
              className="rounded-full bg-[#EDF3EC] px-2 py-0.5 text-[9px] font-semibold uppercase tracking-wider text-[#285943]"
              suppressHydrationWarning
            >
              {user.accountType === 'college'
                ? 'College'
                : user.accountType === 'organization'
                  ? 'Organization'
                  : 'Individual'}
            </span>
          </div>

          <div className="mt-3 flex items-center gap-2">
            <span className="grid h-8 w-8 place-items-center rounded-full bg-[#DDEBDD] text-xs font-semibold text-[#285943]">
              {initials}
            </span>
            <div className="min-w-0 flex-1">
              <p className="truncate text-xs font-semibold text-[#405448]" suppressHydrationWarning>
                {userName}
              </p>
              <p className="truncate text-[10px] text-[#8A978D]" suppressHydrationWarning>
                {user.workspaceName || 'CarbonIQ Workspace'}
              </p>
            </div>
          </div>
        </div>
      </div>
    </div>
  )

  return (
    <>
      {/* Desktop sidebar: fixed to left viewport edge at 100dvh */}
      <aside className="fixed inset-y-0 left-0 z-30 hidden w-[248px] shrink-0 flex-col border-r border-[#E0E7DE] bg-[#FBFCF8] lg:flex h-screen h-[100dvh]">
        {sidebarContent}
      </aside>

      {/* Mobile drawer */}
      {isMobileOpen && (
        <div className="fixed inset-0 z-50 flex lg:hidden">
          <div
            className="fixed inset-0 bg-black/30 backdrop-blur-xs"
            onClick={onCloseMobile}
            aria-hidden="true"
          />
          <div className="relative w-[280px] max-w-[85vw] h-full bg-[#FBFCF8] shadow-2xl animate-in slide-in-from-left duration-200 overflow-y-auto">
            {sidebarContent}
          </div>
        </div>
      )}
    </>
  )
}
