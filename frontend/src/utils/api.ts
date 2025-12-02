import axios, { AxiosError, InternalAxiosRequestConfig, AxiosResponse } from 'axios'
import { message } from 'antd'
import { getToken, removeToken } from './auth'

const api = axios.create({
  baseURL: '/api/v1',
  timeout: 30000,
  headers: {
    'Content-Type': 'application/json',
  },
})

// Request interceptor
api.interceptors.request.use(
  (config: InternalAxiosRequestConfig) => {
    const token = getToken()
    if (token && config.headers) {
      config.headers.Authorization = `Bearer ${token}`
    }
    return config
  },
  (error: AxiosError) => {
    return Promise.reject(error)
  }
)

// Response interceptor
api.interceptors.response.use(
  (response: AxiosResponse) => {
    return response
  },
  (error: AxiosError<{ detail?: string }>) => {
    if (error.response) {
      const { status, data } = error.response

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
      } else {
        message.error(data?.detail || 'Request failed')
      }
    } else if (error.request) {
      message.error('Network error, please check your connection')
    }

    return Promise.reject(error)
  }
)

export default api
