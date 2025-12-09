"use client"

import type React from "react"

import { useState, useEffect } from "react"
import { Button } from "@/components/ui/button"
import { Input } from "@/components/ui/input"
import { Card } from "@/components/ui/card"
import { Trash2, Plus } from "lucide-react"
import { api } from "@/lib/api"
import { toast } from "sonner"

interface PlaylistInputProps {
  onStartLearning: (url: string, playlistTitle: string) => void
  userEmail: string
}

interface SavedPlaylist {
  playlist_id: string
  playlist_url: string
  playlist_title: string
  total_videos: number
  completed_videos: number
  progress_percentage: number
  first_accessed: string
  last_accessed: string
}

export default function PlaylistInput({ onStartLearning, userEmail }: PlaylistInputProps) {
  const [url, setUrl] = useState("")
  const [error, setError] = useState("")
  const [isLoading, setIsLoading] = useState(false)
  const [savedPlaylists, setSavedPlaylists] = useState<SavedPlaylist[]>([])

  // Fetch user playlists on mount
  useEffect(() => {
    const fetchUserPlaylists = async () => {
      console.log("[PlaylistInput] Fetching playlists from backend...")
      setIsLoading(true)
      
      try {
        const response = await api.getUserPlaylists(userEmail)
        console.log("[PlaylistInput] Received playlists:", response)
        
        if (response.success && response.playlists) {
          setSavedPlaylists(response.playlists)
          console.log(`[PlaylistInput] Loaded ${response.playlists.length} playlists`)
        }
      } catch (error) {
        console.error("[PlaylistInput] Error fetching playlists:", error)
        toast.error("Failed to load playlists")
      } finally {
        setIsLoading(false)
      }
    };
    
    console.log("[PlaylistInput] Component mounted, fetching playlists for:", userEmail)
    fetchUserPlaylists()
  }, [userEmail])

  const validateYouTubeUrl = (urlString: string): boolean => {
    try {
      const urlObj = new URL(urlString)
      return urlObj.hostname.includes("youtube.com") || urlObj.hostname.includes("youtu.be")
    } catch {
      return false
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

    console.log("[PlaylistInput] Starting learning with URL:", url)
    // Pass URL to parent, which will fetch playlist info and save to backend
    onStartLearning(url, "Loading...")
    setUrl("")
  }

  const handleDeletePlaylist = async (playlistId: string, e: React.MouseEvent) => {
    e.stopPropagation()
    console.log("[PlaylistInput] Deleting playlist:", playlistId)
    
    try {
      const response = await api.deleteUserPlaylist(userEmail, playlistId)
      
      if (response.success) {
        console.log("[PlaylistInput] Playlist deleted successfully")
        // Remove from local state
        setSavedPlaylists(savedPlaylists.filter((p) => p.playlist_id !== playlistId))
        toast.success("Playlist removed")
      } else {
        toast.error("Failed to delete playlist")
      }
    } catch (error) {
      console.error("[PlaylistInput] Error deleting playlist:", error)
      toast.error("Failed to delete playlist")
    }
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
      {isLoading ? (
        <div className="max-w-4xl mx-auto text-center py-8">
          <div className="inline-block animate-spin rounded-full h-8 w-8 border-b-2 border-primary"></div>
          <p className="text-sm text-muted-foreground mt-2">Loading your playlists...</p>
        </div>
      ) : savedPlaylists.length > 0 ? (
        <div className="max-w-4xl mx-auto">
          <h3 className="text-xl font-semibold text-foreground mb-4">Recent Playlists</h3>
          <div className="grid gap-3">
            {savedPlaylists.map((playlist) => (
              <Card
                key={playlist.playlist_id}
                className="p-4 border border-border/50 hover:bg-muted/50 transition-colors cursor-pointer group"
                onClick={() => onStartLearning(playlist.playlist_url, playlist.playlist_title)}
              >
                <div className="flex items-center justify-between">
                  <div className="flex-1">
                    <div className="flex items-center gap-3">
                      <h4 className="font-medium text-foreground group-hover:text-primary transition-colors">
                        {playlist.playlist_title}
                      </h4>
                      <span className="text-xs px-2 py-1 rounded-full bg-primary/10 text-primary font-medium">
                        {playlist.progress_percentage.toFixed(0)}% Complete
                      </span>
                    </div>
                    <div className="flex items-center gap-4 mt-2 text-xs text-muted-foreground">
                      <span>{playlist.completed_videos} / {playlist.total_videos} videos completed</span>
                      <span>•</span>
                      <span>Last accessed: {new Date(playlist.last_accessed).toLocaleDateString()}</span>
                    </div>
                  </div>
                  <Button
                    onClick={(e) => handleDeletePlaylist(playlist.playlist_id, e)}
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
      ) : (
        <div className="max-w-4xl mx-auto text-center py-8">
          <p className="text-muted-foreground">No playlists yet. Add one above to get started!</p>
        </div>
      )}
    </div>
  )
}
