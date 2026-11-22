import { createContext, useContext, useEffect, useState, type ReactNode } from 'react'
import { api } from '../lib/api'
import type { User } from '../types'

type AuthValue = { user: User | null; loading: boolean; login: (email: string, password: string) => Promise<void>; register: (fullName: string, email: string, password: string) => Promise<void>; logout: () => void }
const AuthContext = createContext<AuthValue | null>(null)

export function AuthProvider({ children }: { children: ReactNode }) {
  const [user, setUser] = useState<User | null>(null)
  const [loading, setLoading] = useState(true)
  useEffect(() => {
    if (!localStorage.getItem('mediguide_token')) { setLoading(false); return }
    api<User>('/auth/me').then(setUser).catch(() => localStorage.removeItem('mediguide_token')).finally(() => setLoading(false))
  }, [])
  const authenticate = async (path: string, body: object) => {
    const result = await api<{ access_token: string; user: User }>(path, { method: 'POST', body: JSON.stringify(body) })
    localStorage.setItem('mediguide_token', result.access_token)
    setUser(result.user)
  }
  return <AuthContext.Provider value={{ user, loading, login: (email, password) => authenticate('/auth/login', { email, password }), register: (full_name, email, password) => authenticate('/auth/register', { full_name, email, password }), logout: () => { localStorage.removeItem('mediguide_token'); setUser(null) } }}>{children}</AuthContext.Provider>
}

export function useAuth() {
  const value = useContext(AuthContext)
  if (!value) throw new Error('useAuth must be used inside AuthProvider')
  return value
}

