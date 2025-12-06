"use client"

import { useState } from "react"
import LoginScreen from "@/components/auth/login-screen"
import Dashboard from "@/components/dashboard/dashboard"

export default function Home() {
  const [isLoggedIn, setIsLoggedIn] = useState(false)
  const [user, setUser] = useState<{ email: string; name: string } | null>(null)

  const handleLogin = (email: string, name: string) => {
    setUser({ email, name })
    setIsLoggedIn(true)
  }

  const handleLogout = () => {
    setIsLoggedIn(false)
    setUser(null)
  }

  return (
    <main className="min-h-screen bg-background">
      {!isLoggedIn ? <LoginScreen onLogin={handleLogin} /> : <Dashboard user={user!} onLogout={handleLogout} />}
    </main>
  )
}
