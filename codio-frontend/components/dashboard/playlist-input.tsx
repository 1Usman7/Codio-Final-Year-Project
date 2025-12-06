"use client"

import type React from "react"

import { useState } from "react"
import { Button } from "@/components/ui/button"
import { Input } from "@/components/ui/input"
import { Card } from "@/components/ui/card"
import { Trash2, Plus } from "lucide-react"

interface PlaylistInputProps {
  onStartLearning: (url: string) => void
}

interface SavedPlaylist {
  id: string
  url: string
  title: string
  addedAt: string
}

export default function PlaylistInput({ onStartLearning }: PlaylistInputProps) {
  const [url, setUrl] = useState("")
  const [error, setError] = useState("")
  const [savedPlaylists, setSavedPlaylists] = useState<SavedPlaylist[]>([
    {
      id: "1",
      url: "https://youtube.com/playlist?list=PLu0W_9lII9agwh1XjRt242xIpHhPT2llg&si=DP6cUGJ7Z5_iX2R9",
      title: "Python for Beginners",
      addedAt: "2024-01-15",
    },
    {
      id: "2",
      url: "https://www.youtube.com/playlist?list=PLrAXtmErZgOdP_sPvB1-p8TSc5_biB35u",
      title: "Web Development Basics",
      addedAt: "2024-01-10",
    },
  ])

  const validateYouTubeUrl = (urlString: string): boolean => {
    try {
      const urlObj = new URL(urlString)
      return urlObj.hostname.includes("youtube.com") || urlObj.hostname.includes("youtu.be")
    } catch {
      return false
    }
  }

  const extractPlaylistTitle = (urlString: string): string => {
    try {
      const urlObj = new URL(urlString)
      return urlObj.searchParams.get("list") || "Untitled Playlist"
    } catch {
      return "Untitled Playlist"
    }
  }

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault()
    setError("")

    if (!url.trim()) {
      setError("Please enter a YouTube playlist URL")
      return
    }

    if (!validateYouTubeUrl(url)) {
      setError("Please enter a valid YouTube URL")
      return
    }

    const newPlaylist: SavedPlaylist = {
      id: Date.now().toString(),
      url,
      title: extractPlaylistTitle(url),
      addedAt: new Date().toISOString().split("T")[0],
    }

    setSavedPlaylists([newPlaylist, ...savedPlaylists])
    onStartLearning(url)
    setUrl("")
  }

  const handleDeletePlaylist = (id: string) => {
    setSavedPlaylists(savedPlaylists.filter((p) => p.id !== id))
  }

  return (
    <div className="space-y-8">
      {/* Welcome Section */}
      <div className="text-center space-y-4">
        <h2 className="text-4xl font-bold text-foreground">Welcome to Codio</h2>
        <p className="text-lg text-muted-foreground max-w-2xl mx-auto">
          Paste a YouTube playlist link and start learning by doing. Watch tutorials and practice code in real-time.
        </p>
      </div>

      {/* Input Card */}
      <Card className="max-w-2xl mx-auto p-8 border border-border/50">
        <form onSubmit={handleSubmit} className="space-y-6">
          <div>
            <label htmlFor="playlist-url" className="block text-sm font-medium text-foreground mb-3">
              YouTube Playlist URL
            </label>
            <div className="flex gap-2">
              <Input
                id="playlist-url"
                type="url"
                placeholder="https://www.youtube.com/playlist?list=..."
                value={url}
                onChange={(e) => setUrl(e.target.value)}
                className="flex-1 text-base"
              />
              <Button
                type="submit"
                className="bg-primary hover:bg-primary/90 text-primary-foreground font-semibold px-6 h-10"
              >
                <Plus className="w-4 h-4 mr-2" />
                Add
              </Button>
            </div>
            {error && <p className="text-destructive text-sm mt-2">{error}</p>}
          </div>
        </form>
      </Card>

      {/* Features Grid */}
      <div className="grid md:grid-cols-3 gap-6 max-w-4xl mx-auto">
        <Card className="p-6 border border-border/50 text-center">
          <div className="text-3xl mb-3">▶</div>
          <h3 className="font-semibold text-foreground mb-2">Watch & Learn</h3>
          <p className="text-sm text-muted-foreground">Stream YouTube tutorials directly in Codio</p>
        </Card>

        <Card className="p-6 border border-border/50 text-center">
          <div className="text-3xl mb-3">⏸</div>
          <h3 className="font-semibold text-foreground mb-2">Pause & Code</h3>
          <p className="text-sm text-muted-foreground">Pause videos and practice code instantly</p>
        </Card>

        <Card className="p-6 border border-border/50 text-center">
          <div className="text-3xl mb-3">▲</div>
          <h3 className="font-semibold text-foreground mb-2">Run & Execute</h3>
          <p className="text-sm text-muted-foreground">Execute Python code directly in your browser</p>
        </Card>
      </div>

      {/* Saved Playlists Section */}
      {savedPlaylists.length > 0 && (
        <div className="max-w-4xl mx-auto">
          <h3 className="text-xl font-semibold text-foreground mb-4">Recent Playlists</h3>
          <div className="grid gap-3">
            {savedPlaylists.map((playlist) => (
              <Card
                key={playlist.id}
                className="p-4 border border-border/50 hover:bg-muted/50 transition-colors cursor-pointer group"
              >
                <div className="flex items-center justify-between">
                  <div className="flex-1" onClick={() => onStartLearning(playlist.url)}>
                    <h4 className="font-medium text-foreground group-hover:text-primary transition-colors">
                      {playlist.title}
                    </h4>
                    <p className="text-xs text-muted-foreground mt-1">{playlist.addedAt}</p>
                  </div>
                  <Button
                    onClick={(e) => {
                      e.stopPropagation()
                      handleDeletePlaylist(playlist.id)
                    }}
                    variant="ghost"
                    size="sm"
                    className="text-destructive hover:bg-destructive/10"
                  >
                    <Trash2 className="w-4 h-4" />
                  </Button>
                </div>
              </Card>
            ))}
          </div>
        </div>
      )}
    </div>
  )
}
