"use client"

import type React from "react"

import { useState } from "react"
import { Button } from "@/components/ui/button"
import { Input } from "@/components/ui/input"
import { Card } from "@/components/ui/card"

interface LoginScreenProps {
  onLogin: (email: string, name: string) => void
}

export default function LoginScreen({ onLogin }: LoginScreenProps) {
  const [email, setEmail] = useState("")
  const [password, setPassword] = useState("")
  const [isLoading, setIsLoading] = useState(false)
  const [error, setError] = useState("")

  // Fake credentials for demo
  const DEMO_CREDENTIALS = [
    { email: "student@codio.com", password: "password123", name: "Alex Student" },
    { email: "learner@codio.com", password: "password123", name: "Jordan Learner" },
  ]

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    setError("")
    setIsLoading(true)

    // Simulate API call
    await new Promise((resolve) => setTimeout(resolve, 800))

    const user = DEMO_CREDENTIALS.find((cred) => cred.email === email && cred.password === password)

    if (user) {
      onLogin(user.email, user.name)
    } else {
      setError("Invalid credentials. Try: student@codio.com / password123")
    }

    setIsLoading(false)
  }

  return (
    <div className="min-h-screen flex items-center justify-center bg-gradient-to-br from-background via-background to-primary/5 px-4">
      <div className="w-full max-w-md">
        {/* Logo and Header */}
        <div className="text-center mb-8">
          <div className="inline-flex items-center justify-center w-16 h-16 rounded-lg bg-primary/10 mb-4">
            <div className="text-3xl font-bold text-primary">C</div>
          </div>
          <h1 className="text-4xl font-bold text-foreground mb-2">Codio</h1>
          <p className="text-muted-foreground">Learn coding by doing</p>
        </div>

        {/* Login Card */}
        <Card className="p-8 border border-border/50 shadow-lg">
          <form onSubmit={handleSubmit} className="space-y-6">
            <div>
              <label htmlFor="email" className="block text-sm font-medium text-foreground mb-2">
                Email
              </label>
              <Input
                id="email"
                type="email"
                placeholder="student@codio.com"
                value={email}
                onChange={(e) => setEmail(e.target.value)}
                disabled={isLoading}
                className="w-full"
              />
            </div>

            <div>
              <label htmlFor="password" className="block text-sm font-medium text-foreground mb-2">
                Password
              </label>
              <Input
                id="password"
                type="password"
                placeholder="••••••••"
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                disabled={isLoading}
                className="w-full"
              />
            </div>

            {error && (
              <div className="p-3 rounded-lg bg-destructive/10 border border-destructive/20 text-destructive text-sm">
                {error}
              </div>
            )}

            <Button
              type="submit"
              disabled={isLoading || !email || !password}
              className="w-full bg-primary hover:bg-primary/90 text-primary-foreground font-semibold py-2 h-10"
            >
              {isLoading ? "Signing in..." : "Sign In"}
            </Button>
          </form>

          <div className="mt-6 pt-6 border-t border-border/50">
            <p className="text-xs text-muted-foreground text-center mb-3">Demo Credentials:</p>
            <div className="space-y-2 text-xs text-muted-foreground">
              <p>Email: student@codio.com</p>
              <p>Password: password123</p>
            </div>
          </div>
        </Card>

        {/* Footer */}
        <p className="text-center text-xs text-muted-foreground mt-6">
          Interactive learning platform for coding education
        </p>
      </div>
    </div>
  )
}
