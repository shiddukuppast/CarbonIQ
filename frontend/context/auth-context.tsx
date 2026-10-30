'use client'

import React, {
  createContext,
  useCallback,
  useContext,
  useEffect,
  useState,
} from 'react'
import { useRouter } from 'next/navigation'
import {
  authService,
  DEFAULT_DEMO_SESSION,
  DEFAULT_DEMO_USER,
} from '@/services/auth.service'
import type { AccountType, UserProfile, UserSession } from '@/types/auth'

export interface AuthContextType {
  session: UserSession
  user: UserProfile
  isHydrated: boolean
  token: string | null
  signIn: (email: string, password?: string, name?: string, workspaceName?: string, accountType?: AccountType) => Promise<void>
  signUp: (profile: {
    name: string
    email: string
    password?: string
    accountType?: AccountType
    workspaceName?: string
  }) => Promise<void>
  signOut: () => void
  isAccessModalOpen: boolean
  accessModalMessage?: string
  openAccessModal: (customMessage?: string) => void
  closeAccessModal: () => void
  requestMutation: (actionName?: string) => boolean
}

const AuthContext = createContext<AuthContextType | undefined>(undefined)

export function AuthProvider({ children }: { children: React.ReactNode }) {
  const router = useRouter()
  const [session, setSession] = useState<UserSession>(DEFAULT_DEMO_SESSION)
  const [isHydrated, setIsHydrated] = useState(false)
  const [isAccessModalOpen, setIsAccessModalOpen] = useState(false)
  const [accessModalMessage, setAccessModalMessage] = useState<string | undefined>()

  // Restore session from localStorage on initial mount and verify token against backend
  useEffect(() => {
    let isMounted = true

    async function initSession() {
      const existing = authService.getStoredSession()
      const token = authService.getToken()

      if (token && existing?.isAuthenticated) {
        // Attempt verifying with backend /auth/me
        try {
          const verified = await authService.verifySession()
          if (isMounted) {
            if (verified) {
              setSession(verified)
            } else {
              // Token was invalid or expired: clear token and fallback to demo session
              authService.clearToken()
              setSession(authService.createDemoSession())
            }
            setIsHydrated(true)
          }
          return
        } catch {
          // If network failed during verification, use cached existing session only if token is present
          if (isMounted) {
            if (existing && token) {
              setSession(existing)
            } else {
              setSession(authService.createDemoSession())
            }
            setIsHydrated(true)
          }
          return
        }
      }

      if (isMounted) {
        if (existing && existing.isAuthenticated && token) {
          setSession(existing)
        } else if (existing && !existing.isAuthenticated) {
          setSession(existing)
        } else {
          const demo = authService.createDemoSession()
          setSession(demo)
        }
        setIsHydrated(true)
      }
    }

    initSession()

    return () => {
      isMounted = false
    }
  }, [])

  const signIn = useCallback(
    async (email: string, password?: string, name?: string, workspaceName?: string, accountType?: AccountType) => {
      if (password) {
        // Real backend authentication
        const newSession = await authService.signIn(email, password)
        setSession(newSession)
      } else {
        // Demo authentication fallback
        const newSession = authService.signInDemo(email, name, workspaceName, accountType)
        setSession(newSession)
      }
    },
    []
  )

  const signUp = useCallback(
    async (profile: {
      name: string
      email: string
      password?: string
      accountType?: AccountType
      workspaceName?: string
    }) => {
      if (profile.password) {
        // Real backend registration
        const newSession = await authService.signUp({
          name: profile.name,
          email: profile.email,
          password: profile.password,
          accountType: profile.accountType,
          workspaceName: profile.workspaceName,
        })
        setSession(newSession)
      } else {
        // Demo signup fallback
        const newSession = authService.signUpDemo(profile)
        setSession(newSession)
      }
    },
    []
  )

  const signOut = useCallback(() => {
    authService.signOut()
    const cleanDemo = authService.createDemoSession()
    setSession(cleanDemo)
    router.push('/')
  }, [router])

  const openAccessModal = useCallback((customMessage?: string) => {
    setAccessModalMessage(customMessage)
    setIsAccessModalOpen(true)
  }, [])

  const closeAccessModal = useCallback(() => {
    setIsAccessModalOpen(false)
    setAccessModalMessage(undefined)
  }, [])

  const token = session.token || authService.getToken()
  const isTrulyAuthenticated = Boolean(session.isAuthenticated && token)
  const effectiveSession: UserSession = {
    ...session,
    isAuthenticated: isTrulyAuthenticated,
    mode: isTrulyAuthenticated ? 'authenticated' : 'demo',
    token: isTrulyAuthenticated ? token || undefined : undefined,
  }
  const user = session.user || DEFAULT_DEMO_USER

  /**
   * Guards data-mutating actions:
   * Returns true if authenticated with valid token.
   * If in demo mode, opens the access modal and returns false.
   */
  const requestMutation = useCallback(
    (actionName?: string): boolean => {
      if (isTrulyAuthenticated) {
        return true
      }
      const message = actionName
        ? `You're exploring CarbonIQ in demo mode. Sign in or create an account to ${actionName} and manage your own sustainability data.`
        : undefined
      openAccessModal(message)
      return false
    },
    [isTrulyAuthenticated, openAccessModal]
  )

  return (
    <AuthContext.Provider
      value={{
        session: effectiveSession,
        user,
        isHydrated,
        token: isTrulyAuthenticated ? token : null,
        signIn,
        signUp,
        signOut,
        isAccessModalOpen,
        accessModalMessage,
        openAccessModal,
        closeAccessModal,
        requestMutation,
      }}
    >
      {children}
    </AuthContext.Provider>
  )
}

export function useAuth() {
  const context = useContext(AuthContext)
  if (!context) {
    throw new Error('useAuth must be used within an AuthProvider')
  }
  return context
}
