"use client"

import type React from "react"

import { useState } from "react"
import { Button } from "@/components/ui/button"
import { Input } from "@/components/ui/input"
import { Card } from "@/components/ui/card"
import { api, setTokens } from "@/lib/api"

interface SignupScreenProps {
  onSignup: (email: string, name: string) => void
  onSwitchToLogin: () => void
}

export default function SignupScreen({ onSignup, onSwitchToLogin }: SignupScreenProps) {
  const [email, setEmail] = useState("")
  const [name, setName] = useState("")
  const [password, setPassword] = useState("")
  const [confirmPassword, setConfirmPassword] = useState("")
  const [isLoading, setIsLoading] = useState(false)
  const [error, setError] = useState("")
  const [success, setSuccess] = useState("")

  const validateEmail = (email: string): boolean => {
    const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/
    return emailRegex.test(email)
  }

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    setError("")
    setSuccess("")
    console.log("[SignupScreen] Form submitted")

    // Validation
    if (!name.trim()) {
      setError("Please enter your name")
      return
    }

    if (name.trim().length < 2) {
      setError("Name must be at least 2 characters")
      return
    }

    if (!email.trim()) {
      setError("Please enter your email")
      return
    }

    if (!validateEmail(email)) {
      setError("Please enter a valid email address")
      return
    }

    if (!password) {
      setError("Please enter a password")
      return
    }

    if (password.length < 6) {
      setError("Password must be at least 6 characters")
      return
    }

    if (password !== confirmPassword) {
      setError("Passwords do not match")
      return
    }

    setIsLoading(true)
    console.log("[SignupScreen] Creating account for:", email)

    try {
      // Call signup API
      const response = await api.signup(email.toLowerCase().trim(), name.trim(), password)
      console.log("[SignupScreen] Signup response:", response)

      if (response.success) {
        console.log("[SignupScreen] Account created successfully")
        setSuccess("Account created successfully! Logging you in...")
        
        // Store JWT tokens if available
        if (response.access_token && response.refresh_token) {
          console.log("[SignupScreen] Storing JWT tokens")
          setTokens(response.access_token, response.refresh_token)
          console.log("[SignupScreen] Tokens stored successfully")
        }
        
        // Auto-login after successful signup
        setTimeout(() => {
          onSignup(email.toLowerCase().trim(), name.trim())
        }, 1500)
      } else {
        console.error("[SignupScreen] Signup failed:", response.error)
        setError(response.error || "Failed to create account")
      }
    } catch (error: any) {
      console.error("[SignupScreen] Exception during signup:", error)
      setError(error?.message || "An error occurred. Please try again.")
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
          <h1 className="text-4xl font-bold text-foreground mb-2">Create Account</h1>
          <p className="text-muted-foreground">Join Codio and start learning by doing</p>
        </div>

        {/* Signup Card */}
        <Card className="p-8 border border-border/50 shadow-lg">
          <form onSubmit={handleSubmit} className="space-y-6">
            <div>
              <label htmlFor="name" className="block text-sm font-medium text-foreground mb-2">
                Full Name
              </label>
              <Input
                id="name"
                type="text"
                placeholder="Muhammad Saleh"
                value={name}
                onChange={(e) => setName(e.target.value)}
                disabled={isLoading}
                className="w-full"
              />
            </div>

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
              <p className="text-xs text-muted-foreground mt-1">At least 6 characters</p>
            </div>

            <div>
              <label htmlFor="confirmPassword" className="block text-sm font-medium text-foreground mb-2">
                Confirm Password
              </label>
              <Input
                id="confirmPassword"
                type="password"
                placeholder="••••••••"
                value={confirmPassword}
                onChange={(e) => setConfirmPassword(e.target.value)}
                disabled={isLoading}
                className="w-full"
              />
            </div>

            {error && (
              <div className="p-3 rounded-lg bg-destructive/10 border border-destructive/20 text-destructive text-sm">
                {error}
              </div>
            )}

            {success && (
              <div className="p-3 rounded-lg bg-green-500/10 border border-green-500/20 text-green-600 text-sm">
                {success}
              </div>
            )}

            <Button
              type="submit"
              disabled={isLoading || !email || !password || !name || !confirmPassword}
              className="w-full bg-primary hover:bg-primary/90 text-primary-foreground font-semibold py-2 h-10"
            >
              {isLoading ? "Creating Account..." : "Create Account"}
            </Button>
          </form>

          {/* Switch to Login */}
          <div className="mt-6 text-center">
            <p className="text-sm text-muted-foreground">
              Already have an account?{" "}
              <button
                onClick={onSwitchToLogin}
                className="text-primary hover:underline font-medium"
                disabled={isLoading}
              >
                Login here
              </button>
            </p>
          </div>
        </Card>

        {/* Features */}
        <div className="mt-8 text-center text-sm text-muted-foreground">
          <p>By signing up, you agree to our Terms of Service and Privacy Policy</p>
        </div>
      </div>
    </div>
  )
}
