"use client"

import { useState } from "react"
import { Button } from "@/components/ui/button"
import { Input } from "@/components/ui/input"
import { Search, X, Clock, Play } from "lucide-react"
import { api } from "@/lib/api"
import { toast } from "sonner"

interface TranscriptSearchProps {
  videoId: string
  onJumpToTimestamp?: (timestamp: number) => void
}

interface TranscriptMatch {
  timestamp: number
  text: string
  duration: number
  match_start?: number
  match_length?: number
}

export default function TranscriptSearch({ videoId, onJumpToTimestamp }: TranscriptSearchProps) {
  const [query, setQuery] = useState("")
  const [isSearching, setIsSearching] = useState(false)
  const [matches, setMatches] = useState<TranscriptMatch[]>([])
  const [hasSearched, setHasSearched] = useState(false)

  const handleSearch = async () => {
    if (!query.trim()) {
      toast.error("Please enter a search query")
      return
    }

    setIsSearching(true)
    setHasSearched(true)

    try {
      const response = await api.searchTranscript(videoId, query.trim())
      
      if (response.success) {
        setMatches(response.matches || [])
        if (response.matches_count === 0) {
          toast.info("No matches found")
        } else {
          toast.success(`Found ${response.matches_count} match${response.matches_count !== 1 ? 'es' : ''}`)
        }
      } else {
        toast.error(response.error || "Search failed")
        setMatches([])
      }
    } catch (error: any) {
      console.error("Transcript search error:", error)
      toast.error(error.message || "Failed to search transcript")
      setMatches([])
    } finally {
      setIsSearching(false)
    }
  }

  const handleKeyPress = (e: React.KeyboardEvent) => {
    if (e.key === "Enter") {
      handleSearch()
    }
  }

  const formatTime = (seconds: number) => {
    const mins = Math.floor(seconds / 60)
    const secs = Math.floor(seconds % 60)
    return `${mins}:${secs.toString().padStart(2, '0')}`
  }

  const handleJumpToTimestamp = (timestamp: number) => {
    if (onJumpToTimestamp) {
      onJumpToTimestamp(timestamp)
    }
  }

  const highlightMatch = (text: string, matchStart?: number, matchLength?: number) => {
    if (matchStart === undefined || matchLength === undefined) {
      return text
    }

    const before = text.substring(0, matchStart)
    const match = text.substring(matchStart, matchStart + matchLength)
    const after = text.substring(matchStart + matchLength)

    return (
      <>
        {before}
        <mark className="bg-yellow-200 dark:bg-yellow-900 px-1 rounded">{match}</mark>
        {after}
      </>
    )
  }

  return (
    <div className="flex flex-col h-full">
      {/* Search Input */}
      <div className="p-4 border-b border-border">
        <div className="flex gap-2">
          <div className="relative flex-1">
            <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 text-muted-foreground w-4 h-4" />
            <Input
              type="text"
              placeholder="Search transcript..."
              value={query}
              onChange={(e) => setQuery(e.target.value)}
              onKeyPress={handleKeyPress}
              className="pl-10 pr-10"
            />
            {query && (
              <Button
                variant="ghost"
                size="sm"
                className="absolute right-1 top-1/2 transform -translate-y-1/2 h-6 w-6 p-0"
                onClick={() => {
                  setQuery("")
                  setMatches([])
                  setHasSearched(false)
                }}
              >
                <X className="w-3 h-3" />
              </Button>
            )}
          </div>
          <Button
            onClick={handleSearch}
            disabled={isSearching || !query.trim()}
            size="default"
          >
            {isSearching ? "Searching..." : "Search"}
          </Button>
        </div>
      </div>

      {/* Results */}
      <div className="flex-1 overflow-y-auto">
        {!hasSearched ? (
          <div className="flex items-center justify-center h-full text-muted-foreground">
            <div className="text-center">
              <Search className="w-12 h-12 mx-auto mb-4 opacity-50" />
              <p className="text-sm">Enter keywords to search the video transcript</p>
            </div>
          </div>
        ) : matches.length === 0 ? (
          <div className="flex items-center justify-center h-full text-muted-foreground">
            <div className="text-center">
              <p className="text-sm">No matches found for "{query}"</p>
              <p className="text-xs mt-2 opacity-70">Try different keywords</p>
            </div>
          </div>
        ) : (
          <div className="p-4 space-y-3">
            {matches.map((match, index) => (
              <div
                key={index}
                className="p-3 rounded-lg border border-border bg-card hover:bg-accent/50 transition-colors cursor-pointer"
                onClick={() => handleJumpToTimestamp(match.timestamp)}
              >
                <div className="flex items-start justify-between gap-3 mb-2">
                  <div className="flex items-center gap-2 text-sm text-muted-foreground">
                    <Clock className="w-4 h-4" />
                    <span className="font-mono font-semibold">{formatTime(match.timestamp)}</span>
                  </div>
                  <Button
                    variant="ghost"
                    size="sm"
                    className="h-7 w-7 p-0"
                    onClick={(e) => {
                      e.stopPropagation()
                      handleJumpToTimestamp(match.timestamp)
                    }}
                  >
                    <Play className="w-3 h-3" />
                  </Button>
                </div>
                <p className="text-sm text-foreground leading-relaxed">
                  {highlightMatch(match.text, match.match_start, match.match_length)}
                </p>
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  )
}

