const TOKEN_KEY = 'mlsmanager_token'
const USERNAME_KEY = 'mlsmanager_username'

export const getToken = (): string | null => {
  return localStorage.getItem(TOKEN_KEY)
}

export const setToken = (token: string): void => {
  localStorage.setItem(TOKEN_KEY, token)
}

export const removeToken = (): void => {
  localStorage.removeItem(TOKEN_KEY)
  localStorage.removeItem(USERNAME_KEY)
}

export const getUsername = (): string | null => {
  return localStorage.getItem(USERNAME_KEY)
}

export const setUsername = (username: string): void => {
  localStorage.setItem(USERNAME_KEY, username)
}
