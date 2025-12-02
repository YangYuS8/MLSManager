/**
 * API Client Configuration
 *
 * Configures the generated API client with authentication
 * and error handling interceptors.
 */

import { client } from './generated/client.gen'
import { getToken, removeToken } from '../utils/auth'
import { message } from 'antd'
import type { ResolvedRequestOptions } from './generated/client/types.gen'

// Configure base URL (empty means same origin)
client.setConfig({
  baseUrl: '',
})

// Request interceptor - add auth token
client.interceptors.request.use((request: Request, _options: ResolvedRequestOptions) => {
  const token = getToken()
  if (token) {
    request.headers.set('Authorization', `Bearer ${token}`)
  }
  return request
})

// Response interceptor - handle errors
client.interceptors.response.use((response: Response, _request: Request, _options: ResolvedRequestOptions) => {
  if (!response.ok) {
    const status = response.status

    if (status === 401) {
      removeToken()
      window.location.href = '/login'
      message.error('Session expired, please login again')
    } else if (status === 403) {
      message.error('Permission denied')
    } else if (status === 404) {
      message.error('Resource not found')
    } else if (status >= 500) {
      message.error('Server error, please try again later')
    }
  }

  return response
})

export { client }

// Re-export all API functions for convenience
export * from './generated'
