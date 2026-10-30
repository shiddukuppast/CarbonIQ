export type SessionMode = 'demo' | 'authenticated'

export type AccountType = 'individual' | 'college' | 'organization'

export interface UserProfile {
  id: string
  name: string
  email: string
  workspaceName: string
  accountType: AccountType
  createdAt?: string
  avatarUrl?: string
  initials?: string
}

export interface UserSession {
  mode: SessionMode
  isAuthenticated: boolean
  user: UserProfile
  createdAt: string
  token?: string
}

export type AuthMode = 'signin' | 'signup'
