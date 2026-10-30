import type { AccountType, UserProfile, UserSession } from '../types/auth'
import { apiClient, TOKEN_STORAGE_KEY } from './api-client'

export const SESSION_STORAGE_KEY = 'carboniq_session'

export interface BackendUserProfile {
  id: string
  full_name: string
  email: string
  workspace_id: string
  workspace_name: string
  account_type?: string
  created_at: string
  avatar_url?: string
  initials: string
}

export interface BackendTokenResponse {
  access_token: string
  token_type: string
  user: BackendUserProfile
}

/**
 * Computes a two-letter uppercase initial pair from a full name.
 * e.g., "Aarav Kapoor" -> "AK", "Priya" -> "PR"
 */
export function computeInitials(name?: string): string {
  if (!name || !name.trim()) return 'CI'
  const cleaned = name.trim()
  const parts = cleaned.split(/\s+/)
  if (parts.length === 1) {
    return parts[0].substring(0, 2).toUpperCase()
  }
  return (parts[0][0] + parts[parts.length - 1][0]).toUpperCase()
}

/**
 * Derives a human-friendly name from an email address when a full name is not entered.
 * e.g., "priya.sharma@example.com" -> "Priya Sharma"
 */
export function formatNameFromEmail(email: string): string {
  if (!email || !email.includes('@')) return 'CarbonIQ User'
  const prefix = email.split('@')[0]
  const words = prefix.replace(/[._-]+/g, ' ').trim().split(/\s+/)
  return words
    .filter(Boolean)
    .map((w) => w.charAt(0).toUpperCase() + w.slice(1).toLowerCase())
    .join(' ')
}

export const DEFAULT_DEMO_USER: UserProfile = {
  id: 'demo-user-aarav',
  name: 'Aarav Kapoor',
  email: 'demo@carboniq.local',
  workspaceName: 'Demo Workspace',
  accountType: 'individual',
  createdAt: '2026-10-01T00:00:00.000Z',
  initials: 'AK',
}

export const DEFAULT_DEMO_SESSION: UserSession = {
  mode: 'demo',
  isAuthenticated: false,
  user: DEFAULT_DEMO_USER,
  createdAt: '2026-10-01T00:00:00.000Z',
}

function normalizeAccountType(raw?: string): AccountType {
  const lower = (raw || '').toLowerCase().trim()
  if (lower === 'college') return 'college'
  if (lower === 'organization') return 'organization'
  return 'individual'
}

function isValidSession(session: any): session is UserSession {
  if (!session || typeof session !== 'object') return false
  if (session.mode !== 'demo' && session.mode !== 'authenticated') return false
  if (typeof session.isAuthenticated !== 'boolean') return false
  if (!session.user || typeof session.user !== 'object') return false
  const u = session.user
  if (typeof u.name !== 'string' || !u.name.trim()) return false
  if (typeof u.email !== 'string') return false
  return true
}

/**
 * Frontend auth service managing real FastAPI backend authentication and demo sessions.
 * Never stores plaintext passwords. Stores JWT securely in localStorage.
 */
export const authService = {
  getToken(): string | null {
    if (typeof window === 'undefined') return null
    try {
      return localStorage.getItem(TOKEN_STORAGE_KEY)
    } catch {
      return null
    }
  },

  saveToken(token: string): void {
    if (typeof window === 'undefined') return
    try {
      localStorage.setItem(TOKEN_STORAGE_KEY, token)
    } catch {
      // Storage unavailable
    }
  },

  clearToken(): void {
    if (typeof window === 'undefined') return
    try {
      localStorage.removeItem(TOKEN_STORAGE_KEY)
    } catch {
      // Storage unavailable
    }
  },

  getStoredSession(): UserSession | null {
    if (typeof window === 'undefined') return null
    try {
      const stored = localStorage.getItem(SESSION_STORAGE_KEY)
      if (!stored) return null
      const parsed = JSON.parse(stored)
      if (isValidSession(parsed)) {
        const safeAccountType = normalizeAccountType(parsed.user.accountType)
        const token = this.getToken() || parsed.token
        const isAuthenticated = Boolean(parsed.isAuthenticated && token)
        const mode = isAuthenticated ? 'authenticated' : 'demo'

        return {
          ...parsed,
          mode,
          isAuthenticated,
          token: token || undefined,
          user: {
            ...parsed.user,
            id: parsed.user.id || (mode === 'demo' ? 'demo-user-aarav' : 'user-auth'),
            workspaceName: parsed.user.workspaceName || (mode === 'demo' ? 'Demo Workspace' : 'Sustainability Workspace'),
            accountType: safeAccountType,
            initials: parsed.user.initials || computeInitials(parsed.user.name),
          },
        }
      }
      return null
    } catch {
      return null
    }
  },

  saveSession(session: UserSession): void {
    if (typeof window === 'undefined') return
    try {
      localStorage.setItem(SESSION_STORAGE_KEY, JSON.stringify(session))
      if (session.token) {
        this.saveToken(session.token)
      }
    } catch {
      // Storage unavailable
    }
  },

  /**
   * Real backend registration via POST /auth/register
   */
  async signUp(profile: {
    name: string
    email: string
    password: string
    accountType?: AccountType
    workspaceName?: string
  }): Promise<UserSession> {
    const res = await apiClient.post<BackendTokenResponse>('/auth/register', {
      full_name: profile.name.trim(),
      email: profile.email.trim(),
      password: profile.password,
      account_type: profile.accountType || 'individual',
      workspace_name: profile.workspaceName?.trim() || undefined,
    })

    const token = res.access_token
    this.saveToken(token)

    const session: UserSession = {
      mode: 'authenticated',
      isAuthenticated: true,
      token,
      user: {
        id: res.user.id,
        name: res.user.full_name,
        email: res.user.email,
        workspaceName: res.user.workspace_name,
        accountType: normalizeAccountType(res.user.account_type),
        initials: res.user.initials || computeInitials(res.user.full_name),
        createdAt: res.user.created_at,
        avatarUrl: res.user.avatar_url,
      },
      createdAt: new Date().toISOString(),
    }

    this.saveSession(session)
    return session
  },

  /**
   * Real backend login via POST /auth/login
   */
  async signIn(email: string, password: string): Promise<UserSession> {
    const res = await apiClient.post<BackendTokenResponse>('/auth/login', {
      email: email.trim(),
      password,
    })

    const token = res.access_token
    this.saveToken(token)

    const session: UserSession = {
      mode: 'authenticated',
      isAuthenticated: true,
      token,
      user: {
        id: res.user.id,
        name: res.user.full_name,
        email: res.user.email,
        workspaceName: res.user.workspace_name,
        accountType: normalizeAccountType(res.user.account_type),
        initials: res.user.initials || computeInitials(res.user.full_name),
        createdAt: res.user.created_at,
        avatarUrl: res.user.avatar_url,
      },
      createdAt: new Date().toISOString(),
    }

    this.saveSession(session)
    return session
  },

  /**
   * Verifies current session against backend GET /auth/me
   */
  async verifySession(): Promise<UserSession | null> {
    const token = this.getToken()
    if (!token) return null

    try {
      const user = await apiClient.get<BackendUserProfile>('/auth/me', { token })
      const session: UserSession = {
        mode: 'authenticated',
        isAuthenticated: true,
        token,
        user: {
          id: user.id,
          name: user.full_name,
          email: user.email,
          workspaceName: user.workspace_name,
          accountType: normalizeAccountType(user.account_type),
          initials: user.initials || computeInitials(user.full_name),
          createdAt: user.created_at,
          avatarUrl: user.avatar_url,
        },
        createdAt: new Date().toISOString(),
      }
      this.saveSession(session)
      return session
    } catch {
      // Invalid/expired token
      this.clearToken()
      return null
    }
  },

  createDemoSession(workspaceName: string = 'Demo Workspace', accountType: AccountType = 'individual'): UserSession {
    const session: UserSession = {
      mode: 'demo',
      isAuthenticated: false,
      user: {
        ...DEFAULT_DEMO_USER,
        workspaceName,
        accountType,
      },
      createdAt: new Date().toISOString(),
    }
    this.saveSession(session)
    return session
  },

  signInDemo(
    email: string,
    providedName?: string,
    workspaceName?: string,
    accountType?: AccountType
  ): UserSession {
    const name = providedName?.trim() || formatNameFromEmail(email)
    const session: UserSession = {
      mode: 'demo',
      isAuthenticated: false,
      user: {
        id: `user-${Date.now().toString(36)}`,
        name,
        email: email.trim(),
        workspaceName: workspaceName?.trim() || 'Demo Workspace',
        accountType: accountType || 'individual',
        initials: computeInitials(name),
        createdAt: new Date().toISOString(),
      },
      createdAt: new Date().toISOString(),
    }
    this.saveSession(session)
    return session
  },

  signUpDemo(profile: {
    name: string
    email: string
    accountType?: AccountType
    workspaceName?: string
  }): UserSession {
    const name = profile.name.trim()
    const safeAccountType: AccountType = profile.accountType || 'individual'
    const session: UserSession = {
      mode: 'demo',
      isAuthenticated: false,
      user: {
        id: `user-${Date.now().toString(36)}`,
        name,
        email: profile.email.trim(),
        workspaceName: profile.workspaceName?.trim() || `${name}'s Demo Workspace`,
        accountType: safeAccountType,
        initials: computeInitials(name),
        createdAt: new Date().toISOString(),
      },
      createdAt: new Date().toISOString(),
    }
    this.saveSession(session)
    return session
  },

  signOut(): void {
    this.clearToken()
    if (typeof window !== 'undefined') {
      try {
        localStorage.removeItem(SESSION_STORAGE_KEY)
      } catch {
        // Storage unavailable
      }
    }
  },
}
