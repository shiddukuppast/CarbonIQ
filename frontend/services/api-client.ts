/**
 * Centralized API Client for Python FastAPI integration.
 * Reads base URL from NEXT_PUBLIC_API_URL or defaults to http://localhost:8000/api.
 * Automatically attaches Authorization Bearer JWT token if available.
 */

export const TOKEN_STORAGE_KEY = 'carboniq_token'

export function getApiBaseUrl(): string {
  const base = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000/api'
  return base.replace(/\/+$/, '')
}

export function buildUrl(endpoint: string): string {
  const base = getApiBaseUrl()
  let cleanEndpoint = endpoint.startsWith('/') ? endpoint : `/${endpoint}`
  // If base ends with /api and endpoint also starts with /api/, avoid duplicate /api/api/
  if (base.endsWith('/api') && cleanEndpoint.startsWith('/api/')) {
    cleanEndpoint = cleanEndpoint.substring(4)
  }
  return `${base}${cleanEndpoint}`
}

export function getStoredToken(): string | null {
  if (typeof window === 'undefined') return null
  try {
    return localStorage.getItem(TOKEN_STORAGE_KEY)
  } catch {
    return null
  }
}

export interface RequestOptions extends RequestInit {
  token?: string
}

export class ApiError extends Error {
  status: number
  data: any

  constructor(status: number, message: string, data?: any) {
    super(message)
    this.name = 'ApiError'
    this.status = status
    this.data = data
  }
}

/**
 * Extracts a human-friendly error message from a FastAPI error payload.
 */
export function extractErrorMessage(errorData: any, fallback: string): string {
  if (!errorData) return fallback
  if (typeof errorData === 'string') return errorData
  if (typeof errorData.detail === 'string') return errorData.detail
  if (Array.isArray(errorData.detail) && errorData.detail.length > 0) {
    const first = errorData.detail[0]
    return first.msg || first.message || fallback
  }
  if (typeof errorData.message === 'string') return errorData.message
  return fallback
}

export async function apiClient<T>(endpoint: string, options: RequestOptions = {}): Promise<T> {
  const { token, headers, ...customConfig } = options

  const activeToken = token || getStoredToken()

  const config: RequestInit = {
    method: customConfig.method || 'GET',
    headers: {
      'Content-Type': 'application/json',
      ...(activeToken ? { Authorization: `Bearer ${activeToken}` } : {}),
      ...headers,
    },
    ...customConfig,
  }

  const url = buildUrl(endpoint)

  let response: Response
  try {
    response = await fetch(url, config)
  } catch (netErr: any) {
    throw new ApiError(0, `Network failure: Unable to reach CarbonIQ backend at ${url}.`, netErr)
  }

  if (!response.ok) {
    if (response.status === 401 && typeof window !== 'undefined') {
      try {
        localStorage.removeItem(TOKEN_STORAGE_KEY)
      } catch {
        // Storage unavailable
      }
    }
    const errorData = await response.json().catch(() => null)
    const message = extractErrorMessage(errorData, response.statusText || 'Request failed')
    throw new ApiError(response.status, message, errorData)
  }

  // Handle 204 No Content
  if (response.status === 204) {
    return {} as T
  }

  return response.json()
}

// Convenience helpers
apiClient.get = <T>(endpoint: string, options?: RequestOptions) =>
  apiClient<T>(endpoint, { ...options, method: 'GET' })

apiClient.post = <T>(endpoint: string, body?: any, options?: RequestOptions) =>
  apiClient<T>(endpoint, {
    ...options,
    method: 'POST',
    body: body !== undefined ? (typeof body === 'string' ? body : JSON.stringify(body)) : undefined,
  })

apiClient.put = <T>(endpoint: string, body?: any, options?: RequestOptions) =>
  apiClient<T>(endpoint, {
    ...options,
    method: 'PUT',
    body: body !== undefined ? (typeof body === 'string' ? body : JSON.stringify(body)) : undefined,
  })

apiClient.delete = <T>(endpoint: string, options?: RequestOptions) =>
  apiClient<T>(endpoint, { ...options, method: 'DELETE' })

export const api = apiClient
