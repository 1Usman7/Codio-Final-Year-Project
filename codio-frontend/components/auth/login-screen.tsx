"use client"

import type React from "react"

import { useState } from "react"
import { Button } from "@/components/ui/button"
import { Input } from "@/components/ui/input"
import { Card } from "@/components/ui/card"
import { api, setTokens } from "@/lib/api"

interface LoginScreenProps {
  onLogin: (email: string, name: string) => void
  onSwitchToSignup: () => void
}

export default function LoginScreen({ onLogin, onSwitchToSignup }: LoginScreenProps) {
  const [email, setEmail] = useState("")
  const [password, setPassword] = useState("")
  const [isLoading, setIsLoading] = useState(false)
  const [error, setError] = useState("")

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    setError("")
    setIsLoading(true)
    console.log("[LoginScreen] Attempting login for:", email)

    try {
      // Call login API
      const response = await api.login(email.toLowerCase().trim(), password)
      console.log("[LoginScreen] Login response:", response)

      if (response.success && response.user) {
        console.log("[LoginScreen] Login successful")
        
        // Store JWT tokens
        if (response.access_token && response.refresh_token) {
          console.log("[LoginScreen] Storing JWT tokens")
          setTokens(response.access_token, response.refresh_token)
          console.log("[LoginScreen] Tokens stored successfully")
        } else {
          console.warn("[LoginScreen] No tokens received in response")
        }
        
        onLogin(response.user.email, response.user.name)
      } else {
        console.error("[LoginScreen] Login failed:", response.error)
        setError(response.error || "Invalid credentials")
      }
    } catch (error: any) {
      console.error("[LoginScreen] Exception during login:", error)
      setError(error?.message || "Failed to connect to server")
    } finally {
      setIsLoading(false)
    }
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

          {/* Switch to Signup */}
          <div className="mt-6 text-center">
            <p className="text-sm text-muted-foreground">
              Don't have an account?{" "}
              <button
                onClick={onSwitchToSignup}
                className="text-primary hover:underline font-medium"
                disabled={isLoading}
              >
                Sign up here
              </button>
            </p>
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
