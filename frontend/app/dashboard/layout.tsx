'use client'

import React, { useState } from 'react'
import { DashboardSidebar } from '@/components/dashboard/DashboardSidebar'
import { DashboardTopbar } from '@/components/dashboard/DashboardTopbar'
import { DemoAccessModal } from '@/components/ui/DemoAccessModal'
import { useAuth } from '@/context/auth-context'

export default function DashboardLayout({
  children,
}: {
  children: React.ReactNode
}) {
  const [isMobileOpen, setIsMobileOpen] = useState(false)
  const { isAccessModalOpen, closeAccessModal, accessModalMessage } = useAuth()

  return (
    <div className="relative flex h-screen h-[100dvh] w-full overflow-hidden bg-[#F7F8F2] text-[#28352D]">
      <DashboardSidebar
        isMobileOpen={isMobileOpen}
        onCloseMobile={() => setIsMobileOpen(false)}
      />

      <div className="flex min-w-0 flex-1 flex-col h-full overflow-hidden lg:pl-[248px]">
        <DashboardTopbar onOpenMobile={() => setIsMobileOpen(true)} />

        <div className="flex-1 overflow-y-auto overflow-x-hidden min-h-0">
          <main className="mx-auto w-full max-w-[1380px] p-5 sm:p-8">
            {children}
          </main>
        </div>
      </div>

      <DemoAccessModal
        isOpen={isAccessModalOpen}
        onClose={closeAccessModal}
        customMessage={accessModalMessage}
      />
    </div>
  )
}
