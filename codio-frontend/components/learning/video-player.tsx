"use client"

import { useEffect, useRef, useState } from "react"
import { Button } from "@/components/ui/button"
import { Volume2, VolumeX, Maximize2, Play, Pause } from "lucide-react"

interface VideoPlayerProps {
  videoId: string
  onPause?: (currentTime: number) => void
  onPauseToCoding?: (currentTime: number) => void
  onFullscreen?: (isFullscreen: boolean) => void
  onTimeUpdate?: (currentTime: number, isPlaying: boolean) => void
  resumeFromTime?: number
  title: string
}

export default function VideoPlayer({ videoId, onPause, onPauseToCoding, onFullscreen, onTimeUpdate, resumeFromTime, title }: VideoPlayerProps) {
  const playerRef = useRef<any>(null)
  const containerRef = useRef<HTMLDivElement>(null)
  const timeUpdateIntervalRef = useRef<NodeJS.Timeout | null>(null)
  const wasPlayingRef = useRef<boolean>(false)
  const [isPlaying, setIsPlaying] = useState(false)
  const [isMuted, setIsMuted] = useState(false)
  const [currentTime, setCurrentTime] = useState(0)
  const [duration, setDuration] = useState(0)
  const [isReady, setIsReady] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const [isFullscreen, setIsFullscreen] = useState(false)

  useEffect(() => {
    if (!videoId || videoId.trim() === "") {
      setError("No video ID provided")
      return
    }

    setError(null)

    if ((window as any).YT) {
      initializePlayer()
      return
    }

    const tag = document.createElement("script")
    tag.src = "https://www.youtube.com/iframe_api"
    document.body.appendChild(tag)
    ;(window as any).onYouTubeIframeAPIReady = () => {
      initializePlayer()
    }

    return () => {
      if (document.body.contains(tag)) {
        document.body.removeChild(tag)
      }
      if (timeUpdateIntervalRef.current) {
        clearInterval(timeUpdateIntervalRef.current)
      }
    }
  }, [videoId])

  useEffect(() => {
    const handleFullscreenChange = () => {
      const isCurrentlyFullscreen = !!document.fullscreenElement
      setIsFullscreen(isCurrentlyFullscreen)
      onFullscreen?.(isCurrentlyFullscreen)
    }
    document.addEventListener("fullscreenchange", handleFullscreenChange)
    return () => document.removeEventListener("fullscreenchange", handleFullscreenChange)
  }, [onFullscreen])

  useEffect(() => {
    if (resumeFromTime !== undefined && playerRef.current && isReady) {
      playerRef.current.seekTo(resumeFromTime, true)
    }
  }, [resumeFromTime, isReady])

  const initializePlayer = () => {
    try {
      if (!videoId || videoId.trim() === "") {
        setError("Invalid video ID")
        return
      }

      if (playerRef.current) {
        playerRef.current.destroy()
      }

      playerRef.current = new (window as any).YT.Player("youtube-player", {
        videoId,
        playerVars: {
          controls: 1,
          modestbranding: 1,
          rel: 0,
          fs: 1,
          cc_load_policy: 0,
          iv_load_policy: 3,
          autohide: 0,
        },
        events: {
          onReady: (event: any) => {
            setIsReady(true)
            setDuration(event.target.getDuration())
            setError(null)
            
            if (timeUpdateIntervalRef.current) {
              clearInterval(timeUpdateIntervalRef.current)
            }
            timeUpdateIntervalRef.current = setInterval(() => {
              if (playerRef.current) {
                const time = playerRef.current.getCurrentTime()
                const playing = playerRef.current.getPlayerState() === 1
                setCurrentTime(time)
                onTimeUpdate?.(time, playing)
              }
            }, 1000)
          },
          onStateChange: (event: any) => {
            const playing = event.data === 1
            const paused = event.data === 2
            const buffering = event.data === 3
            
            if (playing) {
              wasPlayingRef.current = true
            }
            
            setIsPlaying(playing)
            
            if (paused) {
              const currentTime = event.target.getCurrentTime()
              
              if (wasPlayingRef.current && !buffering && onPauseToCoding) {
                console.log(`[VideoPlayer] Pause detected at ${currentTime}s - triggering pause-to-code`)
                onPauseToCoding(currentTime)
                wasPlayingRef.current = false
              }
              
              onPause?.(currentTime)
            }
            
            if (playerRef.current) {
              const time = playerRef.current.getCurrentTime()
              setCurrentTime(time)
              onTimeUpdate?.(time, playing)
            }
          },
          onError: (event: any) => {
            const errorCode = event.data
            let errorMessage = "Error loading video"
            if (errorCode === 2) {
              errorMessage = "Invalid video ID"
            } else if (errorCode === 5) {
              errorMessage = "HTML5 player error"
            } else if (errorCode === 100) {
              errorMessage = "Video not found"
            } else if (errorCode === 101 || errorCode === 150) {
              errorMessage = "Video cannot be played"
            }
            setError(errorMessage)
          },
        },
      })
    } catch (err) {
      setError("Failed to initialize video player")
      console.error("Video player error:", err)
    }
  }

  const handlePlayPause = () => {
    if (!playerRef.current) return
    if (isPlaying) {
      playerRef.current.pauseVideo()
    } else {
      playerRef.current.playVideo()
    }
  }

  const handleMute = () => {
    if (!playerRef.current) return
    if (isMuted) {
      playerRef.current.unMute()
    } else {
      playerRef.current.mute()
    }
    setIsMuted(!isMuted)
  }

  const handleFullscreen = () => {
    const element = containerRef.current
    if (element?.requestFullscreen) {
      element.requestFullscreen()
    }
  }

  const formatTime = (seconds: number) => {
    const mins = Math.floor(seconds / 60)
    const secs = Math.floor(seconds % 60)
    return `${mins}:${secs.toString().padStart(2, '0')}`
  }

  return (
    <div ref={containerRef} className="w-full h-full flex flex-col bg-black">
      <div className="px-6 py-4 border-b border-border/50 bg-card/50">
        <h2 className="text-lg font-semibold text-foreground truncate">{title}</h2>
      </div>

      <div className="flex-1 relative bg-black overflow-hidden">
        {error ? (
          <div className="w-full h-full flex items-center justify-center bg-black">
            <div className="text-center">
              <p className="text-red-500 mb-2">{error}</p>
              <p className="text-sm text-muted-foreground">Please check the video ID and try again</p>
            </div>
          </div>
        ) : (
          <div 
            id="youtube-player" 
            className="w-full h-full" 
            style={{
              position: 'relative',
              zIndex: 1,
              pointerEvents: 'auto'
            }}
          />
        )}

        <div className="absolute bottom-0 left-0 right-0 bg-gradient-to-t from-black/80 to-transparent p-4 opacity-0 hover:opacity-100 transition-opacity">
          <div className="flex items-center justify-between gap-4">
            <div className="flex items-center gap-2">
              <Button
                onClick={handlePlayPause}
                disabled={!isReady}
                variant="ghost"
                size="sm"
                className="text-white hover:bg-white/20"
              >
                {isPlaying ? <Pause className="w-4 h-4" /> : <Play className="w-4 h-4" />}
              </Button>

              <Button
                onClick={handleMute}
                disabled={!isReady}
                variant="ghost"
                size="sm"
                className="text-white hover:bg-white/20"
              >
                {isMuted ? <VolumeX className="w-4 h-4" /> : <Volume2 className="w-4 h-4" />}
              </Button>

              <span className="text-xs text-white/70 font-mono">
                {formatTime(currentTime)} / {formatTime(duration)}
              </span>
            </div>

            <Button
              onClick={handleFullscreen}
              disabled={!isReady}
              variant="ghost"
              size="sm"
              className="text-white hover:bg-white/20"
            >
              <Maximize2 className="w-4 h-4" />
            </Button>
          </div>
        </div>
      </div>

      <div className="px-6 py-3 border-t border-border/50 bg-card/50 text-xs text-muted-foreground">
        <p>Pause the video to open the Python compiler and practice coding</p>
      </div>
    </div>
  )
}
