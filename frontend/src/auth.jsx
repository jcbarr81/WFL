import { createContext, useCallback, useContext, useEffect, useMemo, useState } from 'react'
import * as api from './api'

const AuthContext = createContext(null)

export const AuthProvider = ({ children }) => {
  const [user, setUser] = useState(null)
  const [loading, setLoading] = useState(true)
  const [authError, setAuthError] = useState(null)

  const refresh = useCallback(async () => {
    setLoading(true)
    try {
      const current = await api.me()
      setUser(current)
      setAuthError(null)
    } catch (err) {
      setUser(null)
    } finally {
      setLoading(false)
    }
  }, [])

  useEffect(() => {
    refresh()
  }, [refresh])

  const login = useCallback(async (email, password) => {
    setAuthError(null)
    const data = await api.login(email, password)
    setUser(data)
    return data
  }, [])

  const register = useCallback(async (email, password) => {
    setAuthError(null)
    const data = await api.register(email, password)
    setUser(data)
    return data
  }, [])

  const logout = useCallback(async () => {
    try {
      await api.logout()
    } finally {
      setUser(null)
    }
  }, [])

  const value = useMemo(
    () => ({
      user,
      loading,
      authError,
      setAuthError,
      login,
      register,
      logout,
      refresh,
    }),
    [user, loading, authError, login, register, logout, refresh],
  )

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>
}

export const useAuth = () => {
  const ctx = useContext(AuthContext)
  if (!ctx) {
    throw new Error('useAuth must be used within AuthProvider')
  }
  return ctx
}
