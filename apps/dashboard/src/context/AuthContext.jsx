/**
 * AuthContext.jsx — Context quản lý trạng thái Firebase Auth
 *
 * Wrap toàn bộ app trong <AuthProvider>
 * Dùng useAuth() hook ở mọi component để biết user đang đăng nhập hay chưa
 *
 * Demo: Google Sign-In (dễ demo cho ban giám khảo AISC'26)
 */

import { createContext, useContext, useEffect, useState } from 'react'
import { onAuthStateChanged, signInWithPopup, signOut } from 'firebase/auth'
import { auth, googleProvider } from '../firebase.js'

const AuthContext = createContext(null)

export function AuthProvider({ children }) {
  const [user, setUser]       = useState(null)
  const [loading, setLoading] = useState(true)

  // Lắng nghe thay đổi auth state (persist qua reload)
  useEffect(() => {
    const unsub = onAuthStateChanged(auth, u => {
      setUser(u)
      setLoading(false)
    })
    return () => unsub()
  }, [])

  const loginWithGoogle = () => signInWithPopup(auth, googleProvider)
  const logout          = () => signOut(auth)

  return (
    <AuthContext.Provider value={{ user, loading, loginWithGoogle, logout }}>
      {children}
    </AuthContext.Provider>
  )
}

// eslint-disable-next-line react-refresh/only-export-components
export function useAuth() {
  return useContext(AuthContext)
}
