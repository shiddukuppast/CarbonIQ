'use client'

import React from 'react'
import { BarChart3, FileText, Shield, User } from 'lucide-react'
import { Button } from '@/components/ui/button'
import { Card } from '@/components/ui/Card'
import { PageTitle } from '@/components/ui/PageTitle'
import { Pill } from '@/components/ui/Pill'
import { useAuth } from '@/context/auth-context'

export interface SimplePageViewProps {
  view?: 'settings' | 'reports' | 'progress'
}

export function SimplePageView({ view = 'settings' }: SimplePageViewProps) {
  const { session, user } = useAuth()

  return (
    <div className="space-y-6">
      <PageTitle
        eyebrow="YOUR WORKSPACE"
        title="Workspace settings"
        description="Manage your profile and preferences for this workspace session."
      />

      <Card className="p-6">
        <div className="flex flex-col gap-2 sm:flex-row sm:items-center sm:justify-between border-b border-[#EDF1EB] pb-4">
          <div className="flex items-center gap-3">
            <span className="grid h-10 w-10 place-items-center rounded-xl bg-[#E7F1E5] text-[#285943]">
              <User size={18} />
            </span>
            <div>
              <h2 className="font-semibold text-[#1F3D2C]">Active Profile Details</h2>
              <p className="mt-0.5 text-xs text-[#4E6254]">
                Centrally synchronized across all CarbonIQ dashboard pages.
              </p>
            </div>
          </div>
          <Pill tone={session.isAuthenticated ? 'green' : 'amber'}>
            {session.isAuthenticated ? 'Authenticated Account' : 'Demo Mode'}
          </Pill>
        </div>

        <div className="mt-5 grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
          <div className="rounded-xl bg-[#F6F8F4] p-4">
            <p className="text-xs text-[#526658]">Full Name</p>
            <p className="mt-1.5 text-sm font-semibold text-[#1F3D2C] truncate">{user.name}</p>
            <p className="mt-1 text-[11px] text-[#4E6254]">ID: {user.id}</p>
          </div>

          <div className="rounded-xl bg-[#F6F8F4] p-4">
            <p className="text-xs text-[#526658]">Email Address</p>
            <p className="mt-1.5 text-sm font-semibold text-[#1F3D2C] truncate">{user.email}</p>
            <p className="mt-1 text-[11px] text-[#4E6254]">
              {session.isAuthenticated ? 'Session active' : 'Demo contact'}
            </p>
          </div>

          <div className="rounded-xl bg-[#F6F8F4] p-4">
            <p className="text-xs text-[#526658]">Workspace Name</p>
            <p className="mt-1.5 text-sm font-semibold text-[#285943] truncate">
              {user.workspaceName || 'Sustainability Workspace'}
            </p>
            <p className="mt-1 text-[11px] text-[#4E6254]">Account: {user.accountType}</p>
          </div>

          <div className="rounded-xl bg-[#F6F8F4] p-4">
            <p className="text-xs text-[#526658]">Account Status</p>
            <p className="mt-1.5 text-sm font-semibold text-[#1F3D2C]">
              {session.isAuthenticated ? 'Active Workspace' : 'Read-only Demo'}
            </p>
            <p className="mt-1 text-[11px] text-[#4E6254]">
              {session.isAuthenticated ? 'Verified account' : 'Public sandbox'}
            </p>
          </div>
        </div>
      </Card>

      <Card className="p-6">
        <div className="rounded-xl border border-dashed border-[#C8D8C5] bg-[#FAFCF8] p-8 text-center">
          <span className="mx-auto grid h-11 w-11 place-items-center rounded-xl bg-[#E7F1E5] text-[#285943]">
            <Shield size={20} />
          </span>
          <h2 className="mt-4 font-semibold text-[#1F3D2C]">
            Security & Storage Preferences
          </h2>
          <p className="mx-auto mt-2 max-w-[460px] text-sm leading-6 text-[#4E6254]">
            Client-side profile preferences are stored locally without sensitive credentials. All passwords and tokens remain strictly guarded.
          </p>
        </div>
      </Card>
    </div>
  )
}
