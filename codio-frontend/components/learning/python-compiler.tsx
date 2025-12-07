"use client"

import { useState, useEffect, useRef } from "react"
import { Button } from "@/components/ui/button"
import { Play, X, ChevronDown } from "lucide-react"

interface PythonCompilerProps {
  onClose: () => void
  isFullscreen?: boolean
  initialCode?: string
}

export default function PythonCompiler({ onClose, isFullscreen = false, initialCode }: PythonCompilerProps) {
  console.log(`[PythonCompiler] Component mounted with:`, {
    hasInitialCode: !!initialCode,
    initialCodeLength: initialCode?.length || 0,
    isFullscreen
  })
  
  const [code, setCode] = useState(initialCode || `# No code detected at this timestamp
# 
# This could mean:
# - The instructor is explaining concepts without showing code
# - The video is in a learning/theory phase
# - No code is visible on screen at this moment
#
# Try pausing when you see code on the video screen.
# You can also write your own code here!

print("Write your Python code here...")
`)
  const [output, setOutput] = useState("")
  const [isRunning, setIsRunning] = useState(false)
  const [error, setError] = useState("")
  const [executionTime, setExecutionTime] = useState(0)
  const [lineCount, setLineCount] = useState(1)
  const [showTerminal, setShowTerminal] = useState(true)
  const [terminalHeight, setTerminalHeight] = useState(40)
  const [isDragging, setIsDragging] = useState(false)
  const outputRef = useRef<HTMLDivElement>(null)
  const dividerRef = useRef<HTMLDivElement>(null)
  
  // Check if this code was extracted from video
  const hasExtractedCode = !!initialCode && !initialCode.includes("Welcome to Codio")

  useEffect(() => {
    console.log(`[PythonCompiler] useEffect triggered - initialCode changed:`, {
      hasInitialCode: !!initialCode,
      codeLength: initialCode?.length || 0
    })
    
    // Always replace code with fresh AI-extracted code on each pause
    if (initialCode) {
      console.log(`[PythonCompiler] Step 1: Setting extracted code (${initialCode.length} chars)`)
      console.log(`[PythonCompiler] Step 2: Code preview: ${initialCode.substring(0, 100)}...`)
      setCode(initialCode)
      console.log(`[PythonCompiler] Step 3: Code state updated`)
      // Clear any previous output when new code is loaded
      setOutput("")
      setError("")
      console.log(`[PythonCompiler] Step 4: Cleared output and error states`)
    } else {
      console.log(`[PythonCompiler] WARNING: No code provided, showing placeholder`)
      // No code detected - show placeholder
      setCode(`# No code detected at this timestamp
# 
# This could mean:
# - The instructor is explaining concepts without showing code
# - The video is in a learning/theory phase
# - No code is visible on screen at this moment
#
# Try pausing when you see code on the video screen.
# You can also write your own code here!

print("Write your Python code here...")
`)
      setOutput("")
      setError("")
      console.log(`[PythonCompiler] Placeholder code set`)
    }
  }, [initialCode])

  useEffect(() => {
    setLineCount(code.split("\n").length)
  }, [code])

  useEffect(() => {
    if (outputRef.current) {
      outputRef.current.scrollTop = outputRef.current.scrollHeight
    }
  }, [output, error])

  useEffect(() => {
    const handleMouseMove = (e: MouseEvent) => {
      if (!isDragging) return

      const container = dividerRef.current?.parentElement
      if (!container) return

      const containerHeight = container.clientHeight
      const newHeight = ((e.clientY - container.getBoundingClientRect().top) / containerHeight) * 100

      if (newHeight > 20 && newHeight < 80) {
        setTerminalHeight(100 - newHeight)
      }
    }

    const handleMouseUp = () => {
      setIsDragging(false)
    }

    if (isDragging) {
      document.addEventListener("mousemove", handleMouseMove)
      document.addEventListener("mouseup", handleMouseUp)
    }

    return () => {
      document.removeEventListener("mousemove", handleMouseMove)
      document.removeEventListener("mouseup", handleMouseUp)
    }
  }, [isDragging])

  const runCode = async () => {
    setIsRunning(true)
    setError("")
    setOutput("")

    const startTime = performance.now()

    try {
      const response = await fetch("https://emkc.org/api/v2/piston/execute", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          language: "python",
          version: "3.10.0",
          files: [{ content: code }],
        }),
      })

      const data = await response.json()
      const endTime = performance.now()
      setExecutionTime(endTime - startTime)

      if (data.run.code === 0) {
        setOutput(data.run.stdout || "Code executed successfully!")
        setError("")
      } else {
        setError(data.run.stderr || "Error running code")
        setOutput("")
      }
    } catch (err: any) {
      setError(err.message || "Error running code")
      setOutput("")
    } finally {
      setIsRunning(false)
    }
  }

  if (isFullscreen) {
    return (
      <div className="fixed inset-0 z-50 flex flex-col bg-[#1e1e1e]">
        {/* Close Button Header */}
        <div className="px-4 py-3 border-b border-[#3e3e42] bg-[#252526] flex items-center justify-between">
          <div className="flex items-center gap-3">
            <p className="text-xs font-mono text-[#cccccc]">Python Compiler - Fullscreen</p>
            {hasExtractedCode && (
              <span className="px-2 py-1 bg-blue-600/20 text-blue-400 text-xs rounded border border-blue-600/30">
                Code extracted from video
              </span>
            )}
          </div>
          <Button 
            onClick={onClose} 
            variant="ghost" 
            size="sm" 
            className="text-[#cccccc] hover:bg-[#3e3e42]"
          >
            {hasExtractedCode ? "← Back to Video" : <X className="w-4 h-4" />}
          </Button>
        </div>

        {/* Editor and Output */}
        <div className="flex-1 flex flex-col overflow-hidden">
          {/* Code Editor */}
          <div className="flex-1 flex flex-col overflow-hidden" style={{ height: `${100 - terminalHeight}%` }}>
            <div className="flex-1 flex overflow-hidden">
              {/* Line Numbers */}
              <div className="bg-[#1e1e1e] border-r border-[#3e3e42] px-3 py-4 text-right font-mono text-xs text-[#858585] select-none overflow-hidden">
                {Array.from({ length: lineCount }, (_, i) => (
                  <div key={i + 1} className="h-6 leading-6">
                    {i + 1}
                  </div>
                ))}
              </div>

              {/* Code Input */}
              <textarea
                value={code}
                onChange={(e) => setCode(e.target.value)}
                className="flex-1 p-4 bg-[#1e1e1e] text-[#d4d4d4] font-mono text-sm resize-none focus:outline-none"
                spellCheck="false"
                placeholder="Write your Python code here..."
              />
            </div>
          </div>

          {/* Resizable Divider */}
          <div
            ref={dividerRef}
            onMouseDown={() => setIsDragging(true)}
            className="h-1 bg-[#3e3e42] hover:bg-[#007acc] cursor-row-resize transition-colors"
          />

          {/* Terminal/Output Section */}
          <div
            className="border-t border-[#3e3e42] bg-[#1e1e1e] flex flex-col overflow-hidden"
            style={{ height: `${terminalHeight}%` }}
          >
            {/* Terminal Header */}
            <div className="px-4 py-3 border-b border-[#3e3e42] bg-[#252526] flex items-center justify-between flex-shrink-0">
              <div className="flex items-center gap-2">
                <ChevronDown className="w-4 h-4 text-[#cccccc]" />
                <p className="text-xs font-mono text-[#cccccc]">OUTPUT</p>
              </div>
              <div className="flex gap-2 items-center">
                {executionTime > 0 && <span className="text-xs text-[#858585]">{executionTime.toFixed(2)}ms</span>}
                <Button
                  onClick={runCode}
                  disabled={isRunning}
                  className="text-xs h-7 bg-[#007acc] hover:bg-[#005a9e] text-white flex items-center gap-1"
                >
                  <Play className="w-3 h-3" />
                  {isRunning ? "Running..." : "Run"}
                </Button>
              </div>
            </div>

            {/* Terminal Content */}
            <div
              ref={outputRef}
              className="flex-1 overflow-auto p-4 font-mono text-sm text-[#d4d4d4] space-y-1 bg-[#1e1e1e]"
            >
              {error ? (
                <div className="text-[#f48771]">
                  <p className="font-semibold mb-2">Error:</p>
                  <pre className="whitespace-pre-wrap break-words text-xs">{error}</pre>
                </div>
              ) : output ? (
                <div>
                  <pre className="whitespace-pre-wrap break-words text-xs text-[#ce9178]">{output}</pre>
                </div>
              ) : (
                <p className="text-[#858585] text-xs">Output will appear here...</p>
              )}
            </div>
          </div>
        </div>
      </div>
    )
  }

  return (
    <div className="w-full h-full flex flex-col bg-[#1e1e1e]">
      {/* Header */}
      <div className="px-4 py-3 border-b border-[#3e3e42] bg-[#252526] flex items-center justify-between flex-shrink-0">
        <div className="flex items-center gap-3">
          <p className="text-xs font-mono text-[#cccccc]">Python Compiler</p>
          {hasExtractedCode && (
            <span className="px-2 py-1 bg-blue-600/20 text-blue-400 text-xs rounded border border-blue-600/30">
              Code extracted from video
            </span>
          )}
        </div>
        <Button 
          onClick={onClose} 
          variant="ghost" 
          size="sm" 
          className="text-[#cccccc] hover:bg-[#3e3e42]"
        >
          {hasExtractedCode ? "← Back to Video" : <X className="w-4 h-4" />}
        </Button>
      </div>

      <div className="flex-1 flex flex-col overflow-hidden">
        {/* Code Editor */}
        <div className="flex-1 flex flex-col overflow-hidden" style={{ height: `${100 - terminalHeight}%` }}>
          <div className="flex-1 flex overflow-hidden">
            {/* Line Numbers */}
            <div className="bg-[#1e1e1e] border-r border-[#3e3e42] px-3 py-4 text-right font-mono text-xs text-[#858585] select-none overflow-hidden">
              {Array.from({ length: lineCount }, (_, i) => (
                <div key={i + 1} className="h-6 leading-6">
                  {i + 1}
                </div>
              ))}
            </div>

            {/* Code Input */}
            <textarea
              value={code}
              onChange={(e) => setCode(e.target.value)}
              className="flex-1 p-4 bg-[#1e1e1e] text-[#d4d4d4] font-mono text-sm resize-none focus:outline-none"
              spellCheck="false"
              placeholder="Write your Python code here..."
            />
          </div>
        </div>

        {/* Resizable Divider */}
        <div
          ref={dividerRef}
          onMouseDown={() => setIsDragging(true)}
          className="h-1 bg-[#3e3e42] hover:bg-[#007acc] cursor-row-resize transition-colors flex-shrink-0"
        />

        {/* Terminal/Output Section */}
        <div
          className="border-t border-[#3e3e42] bg-[#1e1e1e] flex flex-col overflow-hidden flex-shrink-0"
          style={{ height: `${terminalHeight}%` }}
        >
          {/* Terminal Header */}
          <div className="px-4 py-3 border-b border-[#3e3e42] bg-[#252526] flex items-center justify-between flex-shrink-0">
            <div className="flex items-center gap-2">
              <ChevronDown className="w-4 h-4 text-[#cccccc]" />
              <p className="text-xs font-mono text-[#cccccc]">OUTPUT</p>
            </div>
            <div className="flex gap-2 items-center">
              {executionTime > 0 && <span className="text-xs text-[#858585]">{executionTime.toFixed(2)}ms</span>}
              <Button
                onClick={runCode}
                disabled={isRunning}
                className="text-xs h-7 bg-[#007acc] hover:bg-[#005a9e] text-white flex items-center gap-1"
              >
                <Play className="w-3 h-3" />
                {isRunning ? "Running..." : "Run"}
              </Button>
            </div>
          </div>

          {/* Terminal Content */}
          <div
            ref={outputRef}
            className="flex-1 overflow-auto p-4 font-mono text-sm text-[#d4d4d4] space-y-1 bg-[#1e1e1e]"
          >
            {error ? (
              <div className="text-[#f48771]">
                <p className="font-semibold mb-2">Error:</p>
                <pre className="whitespace-pre-wrap break-words text-xs">{error}</pre>
              </div>
            ) : output ? (
              <div>
                <pre className="whitespace-pre-wrap break-words text-xs text-[#ce9178]">{output}</pre>
              </div>
            ) : (
              <p className="text-[#858585] text-xs">Output will appear here...</p>
            )}
          </div>
        </div>
      </div>
    </div>
  )
}
