'use client'

import React, { useEffect } from 'react'
import { CheckCircle2, Info, X } from 'lucide-react'

export interface ToastNotificationProps {
  message: string | null
  type?: 'success' | 'info'
  onClose: () => void
  durationMs?: number
}

export function ToastNotification({
  message,
  type = 'success',
  onClose,
  durationMs = 3500,
}: ToastNotificationProps) {
  useEffect(() => {
    if (!message) return
    const timer = window.setTimeout(onClose, durationMs)
    return () => window.clearTimeout(timer)
  }, [message, durationMs, onClose])

  if (!message) return null

  return (
    <div className="fixed bottom-6 right-6 z-50 flex items-center gap-3 rounded-xl border border-[#C5DDC0] bg-[#EAF4E8] px-4 py-3 text-sm text-[#24503B] shadow-lg animate-in slide-in-from-bottom-3 duration-200">
      {type === 'success' ? (
        <CheckCircle2 size={18} className="text-[#367954] shrink-0" />
      ) : (
        <Info size={18} className="text-[#367954] shrink-0" />
      )}
      <span className="font-medium">{message}</span>
      <button
        type="button"
        onClick={onClose}
        aria-label="Close notification"
        className="ml-2 rounded p-1 text-[#5A7765] hover:bg-[#D9EBD5] hover:text-[#24503B] cursor-pointer"
      >
        <X size={15} />
      </button>
    </div>
  )
}
