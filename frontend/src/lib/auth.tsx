import type { ReactNode } from "react"
import { createContext, useCallback, useContext, useEffect, useMemo, useState } from "react"
import { api } from "./api"
import type { AuthUser } from "./types"

const TOKEN_KEY = "tirs_token"

type AuthContextValue = {
  token: string | null
  user: AuthUser | null
  loading: boolean
  login: (email: string, password: string) => Promise<void>
  register: (name: string, email: string, password: string) => Promise<void>
  logout: () => Promise<void>
  refresh: () => Promise<void>
}

const AuthContext = createContext<AuthContextValue | undefined>(undefined)

export function AuthProvider({ children }: { children: ReactNode }) {
  const [token, setToken] = useState<string | null>(() => localStorage.getItem(TOKEN_KEY))
  const [user, setUser] = useState<AuthUser | null>(null)
  const [loading, setLoading] = useState<boolean>(true)

  const updateToken = useCallback((next: string | null) => {
    if (next) {
      localStorage.setItem(TOKEN_KEY, next)
    } else {
      localStorage.removeItem(TOKEN_KEY)
    }
    setToken(next)
  }, [])

  const refresh = useCallback(async () => {
    if (!token) {
      setUser(null)
      setLoading(false)
      return
    }

    try {
      const me = await api.me(token)
      setUser(me)
    } catch (error) {
      updateToken(null)
      setUser(null)
    } finally {
      setLoading(false)
    }
  }, [token, updateToken])

  useEffect(() => {
    refresh()
  }, [refresh])

  const login = useCallback(async (email: string, password: string) => {
    const result = await api.login(email, password)
    updateToken(result.token)
    setUser(result.user)
  }, [updateToken])

  const register = useCallback(async (name: string, email: string, password: string) => {
    const result = await api.register(name, email, password)
    updateToken(result.token)
    setUser(result.user)
  }, [updateToken])

  const logout = useCallback(async () => {
    if (token) {
      try {
        await api.logout(token)
      } catch (error) {
        // Ignore logout failures; JWT is stateless.
      }
    }
    updateToken(null)
    setUser(null)
  }, [token, updateToken])

  const value = useMemo(
    () => ({ token, user, loading, login, register, logout, refresh }),
    [token, user, loading, login, register, logout, refresh],
  )

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>
}

export function useAuth() {
  const context = useContext(AuthContext)
  if (!context) {
    throw new Error("useAuth must be used within AuthProvider")
  }
  return context
}
