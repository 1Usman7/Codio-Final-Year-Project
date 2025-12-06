"use client"

import { useState, useEffect, useRef } from "react"
import { Button } from "@/components/ui/button"
import VideoPlayer from "@/components/learning/video-player"
import PythonCompiler from "@/components/learning/python-compiler"
import ProgressSidebar from "@/components/learning/progress-sidebar"
import { api } from "@/lib/api"
import { toast } from "sonner"

interface LearningViewProps {
  playlistUrl: string
  onBack: () => void
}

interface Video {
  video_id: string
  title: string
  thumbnail: string
  duration: number
  url: string
}

export default function LearningView({ playlistUrl, onBack }: LearningViewProps) {
  const [showCompiler, setShowCompiler] = useState(false)
  const [isTransitioning, setIsTransitioning] = useState(false)
  const [videos, setVideos] = useState<Video[]>([])
  const [currentVideoIndex, setCurrentVideoIndex] = useState(0)
  const [isVideoFullscreen, setIsVideoFullscreen] = useState(false)
  const [isLoading, setIsLoading] = useState(true)
  const [extractedCode, setExtractedCode] = useState<string | undefined>(undefined)
  const [pausedTime, setPausedTime] = useState<number | undefined>(undefined)
  const [processingStatus, setProcessingStatus] = useState<string>("")
  const [videoStatus, setVideoStatus] = useState<string>("not_found")
  const [currentVideoId, setCurrentVideoId] = useState<string>("")
  const [processingProgress, setProcessingProgress] = useState<number>(0)
  const [processingStage, setProcessingStage] = useState<string>("")
  const [watchTime, setWatchTime] = useState<number>(0) // seconds watched
  const [videoDuration, setVideoDuration] = useState<number>(0) // total video duration
  const [isVideoPlaying, setIsVideoPlaying] = useState<boolean>(false)
  const [showLoadingOverlay, setShowLoadingOverlay] = useState<boolean>(false)
  const [isExtractingCode, setIsExtractingCode] = useState<boolean>(false)
  const processingIntervalRef = useRef<NodeJS.Timeout | null>(null)

  useEffect(() => {
    fetchPlaylistVideos()
    
    return () => {
      if (processingIntervalRef.current) {
        clearInterval(processingIntervalRef.current)
      }
    }
  }, [playlistUrl])

  useEffect(() => {
    if (currentVideoId) {
      startVideoProcessing(currentVideoId)
    }
  }, [currentVideoId])

  const fetchPlaylistVideos = async () => {
    try {
      setIsLoading(true)
      setProcessingStatus("Fetching playlist information...")

      // Extract videos from playlist or single video URL
      const response = await api.getPlaylistVideos(playlistUrl)

      if (response.success && response.videos.length > 0) {
        setVideos(response.videos)
        setCurrentVideoId(response.videos[0].video_id)
        setVideoDuration(response.videos[0].duration || 0)
        toast.success(`Found ${response.videos.length} video${response.videos.length > 1 ? 's' : ''}`)
      } else {
        toast.error("No videos found")
        setProcessingStatus("No videos found")
      }
    } catch (error: any) {
      console.error("Error fetching playlist:", error)
      const errorMessage = error?.message || "Error connecting to backend"
      toast.error(errorMessage)
      setProcessingStatus(`Error: ${errorMessage}`)
    } finally {
      setIsLoading(false)
    }
  }

  const startVideoProcessing = async (videoId: string) => {
    try {
      console.log(`[startVideoProcessing] Starting for video ID: ${videoId}`)
      
      // Check current status
      const statusResponse = await api.getVideoStatus(videoId)
      console.log(`[startVideoProcessing] Current status:`, statusResponse)
      
      setVideoStatus(statusResponse.status)
      setProcessingProgress(statusResponse.progress || 0)
      setProcessingStage(statusResponse.stage || "")

      if (statusResponse.status === "completed") {
        console.log(`[startVideoProcessing] Video already completed`)
        setProcessingStatus("Video ready!")
        return
      }

      if (statusResponse.status === "not_found") {
        // Start processing in background
        console.log(`[startVideoProcessing] Video not found, starting download...`)
        setProcessingStatus("Starting video download...")
        
        const videoUrl = `https://www.youtube.com/watch?v=${videoId}`
        console.log(`[startVideoProcessing] Calling processVideo API for: ${videoUrl}`)
        
        api.processVideo(videoUrl).then((response) => {
          console.log(`[startVideoProcessing] API response:`, response)
          setProcessingStatus("Video downloaded successfully!")
          setVideoStatus("completed")
          setProcessingProgress(100)
        }).catch((error) => {
          console.error("[startVideoProcessing] Error processing video:", error)
          setProcessingStatus("Processing failed")
        })
      }

      // Poll for status updates
      if (processingIntervalRef.current) {
        clearInterval(processingIntervalRef.current)
      }

      console.log(`[startVideoProcessing] Starting status polling...`)
      processingIntervalRef.current = setInterval(async () => {
        try {
          const status = await api.getVideoStatus(videoId)
          console.log(`[startVideoProcessing] Poll status:`, status)
          
          setVideoStatus(status.status)
          setProcessingProgress(status.progress || 0)
          setProcessingStage(status.stage || "Processing...")
          
          if (status.status === "completed") {
            console.log(`[startVideoProcessing] Processing completed!`)
            setProcessingStatus("Video ready!")
            if (processingIntervalRef.current) {
              clearInterval(processingIntervalRef.current)
            }
          } else if (status.status === "downloading") {
            const progressText = status.stage || `Downloading... ${status.progress.toFixed(0)}%`
            setProcessingStatus(progressText)
          }
        } catch (error) {
          console.error("[startVideoProcessing] Error checking status:", error)
        }
      }, 2000) // Check every 2 seconds
    } catch (error) {
      console.error("[startVideoProcessing] Error:", error)
    }
  }

  const handlePauseToCoding = async (currentTime: number) => {
    console.log(`[handlePauseToCoding] Triggered at ${currentTime}s, videoStatus: ${videoStatus}`)
    
    // Only proceed if video is completed
    if (videoStatus !== "completed") {
      console.log(`[handlePauseToCoding] Video not ready, status: ${videoStatus}`)
      toast.info("Video is still processing. Please wait.", {
        description: "You can continue watching while processing completes."
      })
      return
    }

    setPausedTime(currentTime)
    setIsExtractingCode(true)
    setShowLoadingOverlay(true)

    try {
      console.log(`[handlePauseToCoding] Extracting frame at ${currentTime}s for video ${currentVideoId}`)
      
      // Use real-time frame extraction endpoint
      const result = await api.getFrameAtTimestamp(currentVideoId, currentTime)
      console.log(`[handlePauseToCoding] Frame extraction result:`, result)

      setShowLoadingOverlay(false)

      if (result.code_content) {
        setExtractedCode(result.code_content)
        console.log(`[handlePauseToCoding] Code extracted successfully`)
        toast.success(`Code extracted! (Confidence: ${(result.confidence * 100).toFixed(0)}%)`)
        setShowCompiler(true)
      } else if (result.segment_type === "learning") {
        setExtractedCode(undefined)
        console.log(`[handlePauseToCoding] Learning phase detected`)
        toast.info(`Learning phase: ${result.learning_topic || "No code at this timestamp"}`)
        setShowCompiler(true)
      } else if (result.error) {
        setExtractedCode(undefined)
        console.log(`[handlePauseToCoding] Error:`, result.error)
        toast.info(result.message || "Video still processing")
      } else {
        setExtractedCode(undefined)
        console.log(`[handlePauseToCoding] No code found`)
        toast.info("No code found at this timestamp")
        setShowCompiler(true)
      }
    } catch (error) {
      console.error("[handlePauseToCoding] Error getting code:", error)
      setShowLoadingOverlay(false)
      toast.error("Failed to extract code")
    } finally {
      setIsExtractingCode(false)
    }
  }

  const handleShowCompiler = async (currentTime?: number) => {
    setIsTransitioning(true)

    if (currentTime !== undefined && currentVideoId) {
      // Check if video is processed
      if (videoStatus !== "completed") {
        toast.info("The video is still processing. Please wait.", {
          description: "You can continue watching while processing completes."
        })
        setIsTransitioning(false)
        return
      }

      try {
        toast.loading("Analyzing frame...")
        
        // Use real-time frame extraction endpoint
        const result = await api.getFrameAtTimestamp(currentVideoId, currentTime)

        toast.dismiss()

        if (result.code_content) {
          setExtractedCode(result.code_content)
          toast.success(`Code extracted! (Confidence: ${(result.confidence * 100).toFixed(0)}%)`)
        } else if (result.segment_type === "learning") {
          setExtractedCode(undefined)
          toast.info(`Learning phase: ${result.learning_topic || "No code at this timestamp"}`)
        } else if (result.error) {
          setExtractedCode(undefined)
          toast.info(result.message || "Video still processing")
        } else {
          setExtractedCode(undefined)
          toast.info("No code found at this timestamp")
        }
      } catch (error) {
        console.error("Error getting code:", error)
        toast.dismiss()
        toast.error("Failed to extract code")
      }
    }

    setTimeout(() => {
      setShowCompiler(true)
      setIsTransitioning(false)
    }, 150)
  }

  const handleHideCompiler = () => {
    setIsTransitioning(true)
    setTimeout(() => {
      setShowCompiler(false)
      setExtractedCode(undefined)
      setIsTransitioning(false)
    }, 150)
  }

  const handleSelectVideo = async (index: number) => {
    if (index === currentVideoIndex) return

    setIsTransitioning(true)
    
    // Cancel current video processing
    if (currentVideoId) {
      try {
        await api.cancelVideoProcessing(currentVideoId)
      } catch (error) {
        console.error("Error cancelling video:", error)
      }
    }

    // Clear interval
    if (processingIntervalRef.current) {
      clearInterval(processingIntervalRef.current)
    }

    setTimeout(() => {
      setCurrentVideoIndex(index)
      setCurrentVideoId(videos[index].video_id)
      setVideoDuration(videos[index].duration || 0)
      setWatchTime(0) // Reset watch time for new video
      setShowCompiler(false)
      setVideoStatus("not_found")
      setProcessingProgress(0)
      setIsTransitioning(false)
    }, 150)
  }

  const handleVideoFullscreen = (isFullscreen: boolean) => {
    setIsVideoFullscreen(isFullscreen)
  }

  const handleTimeUpdate = (currentTime: number, isPlaying: boolean) => {
    // Only count watch time when video is actually playing
    if (isPlaying) {
      setWatchTime(Math.floor(currentTime))
    }
    setIsVideoPlaying(isPlaying)
  }

  if (isLoading) {
    return (
      <div className="flex items-center justify-center h-[calc(100vh-80px)]">
        <div className="text-center max-w-md">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-primary mx-auto mb-4"></div>
          <p className="text-muted-foreground mb-2">{processingStatus || "Loading..."}</p>
        </div>
      </div>
    )
  }

  if (videos.length === 0) {
    return (
      <div className="flex items-center justify-center h-[calc(100vh-80px)]">
        <div className="text-center">
          <p className="text-muted-foreground mb-4">No videos found</p>
          <Button onClick={onBack} variant="outline">
            ← Back to Dashboard
          </Button>
        </div>
      </div>
    )
  }

  if (isVideoFullscreen && showCompiler) {
    return (
      <div className="w-screen h-screen">
        <PythonCompiler
          onClose={() => {
            setShowCompiler(false)
            setIsVideoFullscreen(false)
          }}
          isFullscreen={true}
        />
      </div>
    )
  }

  const currentVideo = videos[currentVideoIndex]

  // Calculate watch statistics
  const watchedMinutes = Math.floor(watchTime / 60)
  const watchedSeconds = watchTime % 60
  const totalMinutes = Math.floor(videoDuration / 60)
  const totalSeconds = videoDuration % 60
  const remainingTime = Math.max(0, videoDuration - watchTime)
  const remainingMinutes = Math.floor(remainingTime / 60)
  const remainingSeconds = remainingTime % 60

  return (
    <div className="flex gap-0 h-[calc(100vh-80px)] bg-background">
      {/* Main Content - Video and Compiler Container */}
      <div className="flex-1 flex flex-col overflow-hidden">
        {/* Back Button and Status */}
        <div className="px-6 py-4 border-b border-border/50 flex items-center justify-between">
          <Button onClick={onBack} variant="outline" className="text-sm bg-transparent">
            ← Back to Dashboard
          </Button>
          
          {/* Processing Status Only */}
          {videoStatus === "processing" && (
            <div className="flex items-center gap-2 text-sm">
              <div className="animate-spin rounded-full h-4 w-4 border-b-2 border-primary"></div>
              <div className="flex flex-col items-start">
                <span className="text-xs text-muted-foreground">{processingStage}</span>
                <span className="font-semibold text-primary">{processingProgress.toFixed(0)}%</span>
              </div>
            </div>
          )}
          {videoStatus === "completed" && (
            <div className="text-sm text-green-600 font-semibold">Ready (100%)</div>
          )}
        </div>

        <div className="flex-1 flex overflow-hidden relative">
          {showLoadingOverlay && (
            <div className="absolute inset-0 bg-black/80 backdrop-blur-sm z-50 flex items-center justify-center">
              <div className="text-center">
                <div className="animate-spin rounded-full h-16 w-16 border-b-4 border-primary mx-auto mb-4"></div>
                <p className="text-white text-lg font-semibold">Extracting code from video...</p>
                <p className="text-white/70 text-sm mt-2">This may take 3-5 seconds</p>
              </div>
            </div>
          )}

          <div
            className={`absolute inset-0 transition-all duration-300 ${showCompiler ? "opacity-0 pointer-events-none" : "opacity-100 pointer-events-auto"}`}
          >
            <VideoPlayer
              videoId={currentVideoId}
              onPause={handleShowCompiler}
              onPauseToCoding={handlePauseToCoding}
              onFullscreen={handleVideoFullscreen}
              onTimeUpdate={handleTimeUpdate}
              resumeFromTime={pausedTime}
              title={currentVideo?.title || "Loading..."}
            />
          </div>

          {/* Compiler Container - Same size as video */}
          <div
            className={`absolute inset-0 transition-all duration-300 ${showCompiler ? "opacity-100 pointer-events-auto" : "opacity-0 pointer-events-none"
              }`}
          >
            {showCompiler && <PythonCompiler onClose={handleHideCompiler} isFullscreen={isVideoFullscreen} initialCode={extractedCode} />}
          </div>
        </div>
      </div>

      {/* Progress Sidebar - Only show when compiler is not open */}
      {!showCompiler && (
        <ProgressSidebar 
          videos={videos.map((v, idx) => ({
            id: v.video_id,
            title: v.title,
            duration: v.duration,
            description: idx === currentVideoIndex ? 
              (videoStatus === "completed" ? "Ready" : videoStatus === "processing" ? "Processing..." : "Not processed") 
              : "Click to play"
          }))} 
          currentVideoIndex={currentVideoIndex} 
          onSelectVideo={handleSelectVideo}
          watchedTime={watchTime}
          totalTime={videoDuration}
        />
      )}
    </div>
  )
}
