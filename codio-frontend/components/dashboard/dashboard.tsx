"use client"

import { useState } from "react"
import { Button } from "@/components/ui/button"
import PlaylistInput from "./playlist-input"
import LearningView from "./learning-view"

interface DashboardProps {
  user: { email: string; name: string }
  onLogout: () => void
}

export default function Dashboard({ user, onLogout }: DashboardProps) {
  const [currentView, setCurrentView] = useState<"home" | "learning">("home")
  const [playlistUrl, setPlaylistUrl] = useState("")

  const handleStartLearning = (url: string) => {
    setPlaylistUrl(url)
    setCurrentView("learning")
  }

  const handleBackToHome = () => {
    setCurrentView("home")
    setPlaylistUrl("")
  }

  return (
    <div className="min-h-screen bg-background">
      {/* Header */}
      <header className="border-b border-border/50 bg-card/50 backdrop-blur-sm sticky top-0 z-40">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-4 flex items-center justify-between">
          <div className="flex items-center gap-3">
            <div className="w-10 h-10 rounded-lg bg-primary/10 flex items-center justify-center">
              <span className="text-xl font-bold text-primary">C</span>
            </div>
            <div>
              <h1 className="text-xl font-bold text-foreground">Codio</h1>
              <p className="text-xs text-muted-foreground">Interactive Learning</p>
            </div>
          </div>
          <div className="flex items-center gap-4">
            <div className="text-right">
              <p className="text-sm font-medium text-foreground">{user.name}</p>
              <p className="text-xs text-muted-foreground">{user.email}</p>
            </div>
            <Button onClick={onLogout} variant="outline" className="text-sm bg-transparent">
              Logout
            </Button>
          </div>
        </div>
      </header>

      {/* Main Content */}
      <main className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        {currentView === "home" ? (
          <PlaylistInput onStartLearning={handleStartLearning} />
        ) : (
          <LearningView playlistUrl={playlistUrl} onBack={handleBackToHome} />
        )}
      </main>
    </div>
  )
}
