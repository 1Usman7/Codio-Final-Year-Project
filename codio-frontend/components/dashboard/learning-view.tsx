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
  console.log(`[LearningView] Component mounted/rendered with playlistUrl: ${playlistUrl}`)
  
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
  console.log(`[LearningView] Current state - currentVideoId: ${currentVideoId}, videoStatus: ${videoStatus}`)
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
    console.log(`[LearningView] ========== useEffect [currentVideoId] TRIGGERED ==========`)
    console.log(`[LearningView] useEffect dependency - currentVideoId: "${currentVideoId}"`)
    console.log(`[LearningView] Current videoStatus: ${videoStatus}`)
    
    if (currentVideoId) {
      console.log(`[LearningView] currentVideoId is truthy, calling startVideoProcessing...`)
      startVideoProcessing(currentVideoId)
    } else {
      console.log(`[LearningView] currentVideoId is empty/falsy, skipping processing`)
    }
    console.log(`[LearningView] ========== useEffect [currentVideoId] END ==========\n`)
  }, [currentVideoId])

  const fetchPlaylistVideos = async () => {
    console.log(`[LearningView] fetchPlaylistVideos called with URL: ${playlistUrl}`)
    console.log(`[LearningView] Step 1: Starting playlist fetch process...`)
    try {
      setIsLoading(true)
      console.log(`[LearningView] Step 2: Set isLoading = true`)
      setProcessingStatus("Fetching playlist information...")
      console.log(`[LearningView] Step 3: Calling backend API to get playlist videos...`)

      // Extract videos from playlist or single video URL
      const response = await api.getPlaylistVideos(playlistUrl)
      console.log(`[LearningView] Step 4: Received API response:`, response)

      if (response.success && response.videos.length > 0) {
        console.log(`[LearningView] Step 5: Success! Found ${response.videos.length} video(s)`)
        console.log(`[LearningView] Step 6: Video details:`, response.videos.map((v: Video) => ({ id: v.video_id, title: v.title })))
        setVideos(response.videos)
        const firstVideoId = response.videos[0].video_id
        console.log(`[LearningView] Step 7: Setting first video ID: ${firstVideoId}`)
        setCurrentVideoId(firstVideoId)
        console.log(`[LearningView] Step 8: Set currentVideoId state to: ${firstVideoId}`)
        setVideoDuration(response.videos[0].duration || 0)
        console.log(`[LearningView] Step 9: Set video duration: ${response.videos[0].duration}s`)
        toast.success(`Found ${response.videos.length} video${response.videos.length > 1 ? 's' : ''}`)
      } else {
        console.log(`[LearningView] ERROR: No videos found in response`)
        console.log(`[LearningView] Response details:`, { success: response.success, videoCount: response.videos?.length })
        toast.error("No videos found")
        setProcessingStatus("No videos found")
      }
    } catch (error: any) {
      console.error(`[LearningView] EXCEPTION in fetchPlaylistVideos:`, error)
      console.error(`[LearningView] Error details:`, { message: error?.message, stack: error?.stack })
      const errorMessage = error?.message || "Error connecting to backend"
      toast.error(errorMessage)
      setProcessingStatus(`Error: ${errorMessage}`)
    } finally {
      setIsLoading(false)
      console.log(`[LearningView] fetchPlaylistVideos completed (finally block)`)
    }
  }

  const startVideoProcessing = async (videoId: string) => {
    console.log(`[LearningView] startVideoProcessing called for video ID: ${videoId}`)
    console.log(`[LearningView] Processing Step 1: Checking video status with backend...`)
    try {
      console.log(`[LearningView] Processing Step 2: Calling api.getVideoStatus(${videoId})...`)
      
      // Check current status
      const statusResponse = await api.getVideoStatus(videoId)
      console.log(`[LearningView] Processing Step 3: Backend returned status:`, {
        status: statusResponse.status,
        progress: statusResponse.progress,
        stage: statusResponse.stage
      })
      
      console.log(`[LearningView] Processing Step 4: Updating component state...`)
      setVideoStatus(statusResponse.status)
      setProcessingProgress(statusResponse.progress || 0)
      setProcessingStage(statusResponse.stage || "")
      console.log(`[LearningView] Processing Step 5: State updated - videoStatus=${statusResponse.status}, progress=${statusResponse.progress}`)

      if (statusResponse.status === "completed") {
        console.log(`[LearningView] Processing Step 6: Video already completed and ready for pause-to-code!`)
        setProcessingStatus("Video ready!")
        console.log(`[LearningView] Video is ready - user can now pause to extract code`)
        return
      }

      if (statusResponse.status === "not_found") {
        // Start processing in background
        console.log(`[LearningView] Processing Step 6: Video not found in backend, initiating download...`)
        setProcessingStatus("Starting video download...")
        
        const videoUrl = `https://www.youtube.com/watch?v=${videoId}`
        console.log(`[LearningView] Processing Step 7: Calling processVideo API with URL: ${videoUrl}`)
        
        api.processVideo(videoUrl).then((response) => {
          console.log(`[LearningView] Processing Step 8: processVideo API response received:`, response)
          setProcessingStatus("Video downloaded successfully!")
          setVideoStatus("completed")
          setProcessingProgress(100)
          console.log(`[LearningView] Processing Step 9: Video download completed, status set to 'completed'`)
        }).catch((error) => {
          console.error(`[LearningView] ERROR in processVideo API:`, error)
          console.error(`[LearningView] Error details:`, { message: error?.message, stack: error?.stack })
          setProcessingStatus("Processing failed")
        })
      }

      // Poll for status updates
      if (processingIntervalRef.current) {
        console.log(`[LearningView] Processing Step 10: Clearing existing polling interval`)
        clearInterval(processingIntervalRef.current)
      }

      console.log(`[LearningView] Processing Step 11: Starting status polling (every 2 seconds)...`)
      processingIntervalRef.current = setInterval(async () => {
        console.log(`[LearningView] Poll: Checking video status...`)
        try {
          const status = await api.getVideoStatus(videoId)
          console.log(`[LearningView] Poll: Status update received:`, {
            status: status.status,
            progress: status.progress,
            stage: status.stage
          })
          
          setVideoStatus(status.status)
          setProcessingProgress(status.progress || 0)
          setProcessingStage(status.stage || "Processing...")
          
          if (status.status === "completed") {
            console.log(`[LearningView] Poll: Video processing COMPLETED! Stopping poll.`)
            setProcessingStatus("Video ready!")
            if (processingIntervalRef.current) {
              clearInterval(processingIntervalRef.current)
              console.log(`[LearningView] Poll: Polling interval cleared successfully`)
            }
          } else if (status.status === "downloading") {
            const progressText = status.stage || `Downloading... ${status.progress.toFixed(0)}%`
            setProcessingStatus(progressText)
            console.log(`[LearningView] Poll: Downloading progress: ${status.progress.toFixed(1)}%`)
          } else {
            console.log(`[LearningView] Poll: Current status: ${status.status}`)
          }
        } catch (error) {
          console.error(`[LearningView] Poll: ERROR checking status:`, error)
        }
      }, 2000) // Check every 2 seconds
    } catch (error) {
      console.error("[startVideoProcessing] Error:", error)
    }
  }

  const handlePauseToCoding = async (currentTime: number) => {
    console.log(`\n=================================================`)
    console.log(`[LearningView] handlePauseToCoding TRIGGERED`)
    console.log(`  Timestamp: ${currentTime.toFixed(2)}s`)
    console.log(`  Video ID: ${currentVideoId}`)
    console.log(`  Current videoStatus (cached): ${videoStatus}`)
    console.log(`  Processing Progress: ${processingProgress}%`)
    console.log(`  Processing Stage: ${processingStage}`)
    console.log(`=================================================\n`)
    
    console.log(`[LearningView] Pause-to-Code Step 1: Re-checking video status from backend...`)
    try {
      // Always re-check status from backend to avoid stale state
      const freshStatus = await api.getVideoStatus(currentVideoId)
      console.log(`[LearningView] Pause-to-Code Step 2: Fresh status from backend: ${freshStatus.status}`)
      
      // Check if video is completed and ready for code extraction
      if (freshStatus.status !== "completed") {
        console.log(`[LearningView] Pause-to-Code Step 3: Video NOT ready for code extraction`)
        console.log(`  Current status: '${freshStatus.status}' (required: 'completed')`)
        console.log(`  Showing info toast to user...`)
        toast.info("Video is still processing. Please wait or continue watching.", {
          description: freshStatus.stage || "Download in progress...",
          duration: 3000
        })
        console.log(`[LearningView] Exiting handlePauseToCoding - video not ready\n`)
        return
      }
      
      // Update local state with fresh status
      setVideoStatus(freshStatus.status)
      console.log(`[LearningView] Pause-to-Code Step 4: Updated local videoStatus to: ${freshStatus.status}`)
    } catch (error) {
      console.error(`[LearningView] ERROR checking video status:`, error)
      toast.error("Failed to check video status")
      return
    }

    console.log(`[LearningView] Pause-to-Code Step 5: Video IS ready! Proceeding with code extraction...`)
    // Video is ready, extract code at this timestamp
    console.log(`[LearningView] Pause-to-Code Step 6: Setting paused time to ${currentTime}s`)
    setPausedTime(currentTime)
    console.log(`[LearningView] Pause-to-Code Step 7: Setting extraction flags...`)
    setIsExtractingCode(true)
    setShowLoadingOverlay(true)
    console.log(`[LearningView] Pause-to-Code Step 8: Loading overlay displayed`)

    try {
      console.log(`[LearningView] Pause-to-Code Step 9: Calling backend API to extract frame...`)
      console.log(`  Endpoint: /api/v1/video/${currentVideoId}/frame?timestamp=${currentTime}`)
      console.log(`  Making HTTP GET request...`)
      
      // Call backend to extract frame and analyze code at this exact timestamp
      const result = await api.getFrameAtTimestamp(currentVideoId, currentTime)
      console.log(`[LearningView] Pause-to-Code Step 10: Backend response received:`, result)

      console.log(`[LearningView] Pause-to-Code Step 11: Hiding loading overlay...`)
      setShowLoadingOverlay(false)

      console.log(`[LearningView] Pause-to-Code Step 12: Analyzing response...`)
      if (result.code_content) {
        // Code detected - show in compiler
        console.log(`[LearningView] Pause-to-Code Step 13: CODE DETECTED!`)
        console.log(`  Code length: ${result.code_content.length} characters`)
        console.log(`  Confidence: ${(result.confidence * 100).toFixed(0)}%`)
        console.log(`  First 100 chars: ${result.code_content.substring(0, 100)}...`)
        console.log(`[LearningView] Pause-to-Code Step 14: Setting extracted code in state...`)
        setExtractedCode(result.code_content)
        toast.success(`Code extracted at ${currentTime.toFixed(1)}s!`, {
          description: `Confidence: ${(result.confidence * 100).toFixed(0)}%`
        })
        console.log(`[LearningView] Pause-to-Code Step 15: Opening compiler with extracted code...`)
        setShowCompiler(true)
        console.log(`[LearningView] Pause-to-Code Step 16: Compiler opened successfully`)
      } else if (result.segment_type === "learning") {
        // Learning phase (no code visible)
        console.log(`[LearningView] Pause-to-Code Step 10: Learning phase detected (no code)`)
        console.log(`  Learning topic: ${result.learning_topic || 'N/A'}`)
        setExtractedCode(undefined)
        toast.info("Learning phase detected", {
          description: result.learning_topic || "No code visible at this timestamp"
        })
        console.log(`[LearningView] Pause-to-Code Step 11: Opening compiler with no-code message...`)
        setShowCompiler(true)
      } else if (result.error) {
        // Error from backend
        console.log(`[LearningView] Pause-to-Code Step 10: Backend returned error:`, result.error)
        console.log(`  Error message: ${result.message}`)
        setExtractedCode(undefined)
        toast.error(result.message || "Failed to extract code")
        console.log(`[LearningView] Not opening compiler due to error`)
        return
      } else {
        // No code found at this timestamp
        console.log(`[LearningView] Pause-to-Code Step 10: No code detected at ${currentTime}s`)
        setExtractedCode(undefined)
        toast.info("No code detected at this timestamp", {
          description: "Try pausing when code is visible on screen"
        })
        console.log(`[LearningView] Pause-to-Code Step 11: Opening compiler with placeholder message...`)
        setShowCompiler(true)
      }
    } catch (error: any) {
      console.error(`[LearningView] EXCEPTION in handlePauseToCoding:`, error)
      console.error(`  Error type: ${error?.name}`)
      console.error(`  Error message: ${error?.message}`)
      console.error(`  Error stack:`, error?.stack)
      console.log(`[LearningView] Pause-to-Code ERROR: Cleaning up...`)
      setShowLoadingOverlay(false)
      setIsExtractingCode(false)
      toast.error("Failed to extract code", {
        description: error?.message || "Backend connection error"
      })
      console.log(`[LearningView] Error handled, overlay hidden`)
    } finally {
      setIsExtractingCode(false)
      console.log(`[LearningView] handlePauseToCoding completed (finally block)\n`)
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
        {/* Back Button and Dynamic Processing Status */}
        <div className="px-6 py-4 border-b border-border/50 flex items-center justify-between">
          <Button onClick={onBack} variant="outline" className="text-sm bg-transparent">
            ← Back to Dashboard
          </Button>
          
          {/* Dynamic Processing Status Indicator */}
          {videoStatus === "downloading" && (
            <div className="flex items-center gap-3 text-sm">
              <div className="animate-spin rounded-full h-4 w-4 border-b-2 border-primary"></div>
              <div className="flex flex-col items-start">
                <span className="text-xs text-muted-foreground">Downloading video...</span>
                <span className="font-semibold text-primary">{processingProgress.toFixed(1)}%</span>
              </div>
            </div>
          )}
          {videoStatus === "processing" && (
            <div className="flex items-center gap-3 text-sm">
              <div className="animate-spin rounded-full h-4 w-4 border-b-2 border-primary"></div>
              <div className="flex flex-col items-start">
                <span className="text-xs text-muted-foreground">{processingStage || "Processing..."}</span>
                <span className="font-semibold text-primary">{processingProgress.toFixed(0)}%</span>
              </div>
            </div>
          )}
          {videoStatus === "completed" && (
            <div className="flex items-center gap-2 text-sm">
              <div className="h-2 w-2 rounded-full bg-green-500 animate-pulse"></div>
              <span className="text-green-600 font-semibold">Video Ready - Pause to extract code</span>
            </div>
          )}
          {videoStatus === "not_found" && (
            <div className="text-sm text-muted-foreground">Preparing video...</div>
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
