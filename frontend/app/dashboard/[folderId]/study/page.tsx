'use client'

import { useState, useRef, useEffect } from 'react'
import Link from 'next/link'
import { useParams, useRouter } from 'next/navigation'
import {
  getNextQuestion,
  submitAnswer,
  getProgress,
  RecommendationResponse,
  AnswerResult,
  ProgressSummary,
  BKTQuestion
} from '@/lib/api'

// Temporary user ID until auth is implemented
const TEMP_USER_ID = 'demo_user'

export default function StudyModePage() {
  const params = useParams()
  const router = useRouter()
  const folderId = params.folderId as string

  // Canvas state
  const canvasRef = useRef<HTMLCanvasElement>(null)
  const [isDrawing, setIsDrawing] = useState(false)
  const [tool, setTool] = useState<'pen' | 'eraser'>('pen')
  const [color, setColor] = useState('#000000')
  const [lineWidth, setLineWidth] = useState(2)

  // BKT state
  const [currentQuestion, setCurrentQuestion] = useState<BKTQuestion | null>(null)
  const [reasoning, setReasoning] = useState<string>('')
  const [conceptName, setConceptName] = useState<string>('')
  const [progress, setProgress] = useState<ProgressSummary | null>(null)
  const [isLoading, setIsLoading] = useState(true)
  const [isSubmitting, setIsSubmitting] = useState(false)
  const [error, setError] = useState<string | null>(null)

  // Feedback state
  const [lastResult, setLastResult] = useState<AnswerResult | null>(null)
  const [showFeedback, setShowFeedback] = useState(false)

  // Timer state
  const [startTime, setStartTime] = useState<number>(Date.now())

  // Load next question from BKT
  const loadNextQuestion = async () => {
    setIsLoading(true)
    setError(null)
    setShowFeedback(false)
    setLastResult(null)

    try {
      const [recommendation, prog] = await Promise.all([
        getNextQuestion(TEMP_USER_ID, folderId),
        getProgress(TEMP_USER_ID, folderId)
      ])

      setCurrentQuestion(recommendation.question)
      setReasoning(recommendation.reasoning)
      setConceptName(recommendation.concept_name || '')
      setProgress(prog)
      setStartTime(Date.now())

      // Clear canvas for new question
      clearCanvas()
    } catch (err) {
      console.error('Failed to load question:', err)
      setError(err instanceof Error ? err.message : 'Failed to load question')
    } finally {
      setIsLoading(false)
    }
  }

  // Submit answer
  const handleSubmitAnswer = async (isCorrect: boolean) => {
    if (!currentQuestion) return

    setIsSubmitting(true)
    const timeTaken = Math.round((Date.now() - startTime) / 1000)

    try {
      const result = await submitAnswer(TEMP_USER_ID, folderId, {
        question_id: currentQuestion.id,
        is_correct: isCorrect,
        time_taken_seconds: timeTaken,
      })

      setLastResult(result)
      setShowFeedback(true)

      // Update progress
      const prog = await getProgress(TEMP_USER_ID, folderId)
      setProgress(prog)
    } catch (err) {
      console.error('Failed to submit answer:', err)
      setError(err instanceof Error ? err.message : 'Failed to submit answer')
    } finally {
      setIsSubmitting(false)
    }
  }

  // Canvas setup
  useEffect(() => {
    const canvas = canvasRef.current
    if (!canvas) return

    const ctx = canvas.getContext('2d')
    if (!ctx) return

    const resizeCanvas = () => {
      const rect = canvas.getBoundingClientRect()
      canvas.width = rect.width * window.devicePixelRatio
      canvas.height = rect.height * window.devicePixelRatio
      ctx.scale(window.devicePixelRatio, window.devicePixelRatio)
    }

    resizeCanvas()
    window.addEventListener('resize', resizeCanvas)

    return () => window.removeEventListener('resize', resizeCanvas)
  }, [])

  // Load initial question
  useEffect(() => {
    loadNextQuestion()
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [folderId])

  const startDrawing = (e: React.MouseEvent<HTMLCanvasElement> | React.TouchEvent<HTMLCanvasElement>) => {
    setIsDrawing(true)
    const canvas = canvasRef.current
    if (!canvas) return

    const ctx = canvas.getContext('2d')
    if (!ctx) return

    const rect = canvas.getBoundingClientRect()
    const x = ('touches' in e) ? e.touches[0].clientX - rect.left : e.clientX - rect.left
    const y = ('touches' in e) ? e.touches[0].clientY - rect.top : e.clientY - rect.top

    ctx.beginPath()
    ctx.moveTo(x, y)
    ctx.lineCap = 'round'
    ctx.lineJoin = 'round'
  }

  const draw = (e: React.MouseEvent<HTMLCanvasElement> | React.TouchEvent<HTMLCanvasElement>) => {
    if (!isDrawing) return

    const canvas = canvasRef.current
    if (!canvas) return

    const ctx = canvas.getContext('2d')
    if (!ctx) return

    const rect = canvas.getBoundingClientRect()
    const x = ('touches' in e) ? e.touches[0].clientX - rect.left : e.clientX - rect.left
    const y = ('touches' in e) ? e.touches[0].clientY - rect.top : e.clientY - rect.top

    ctx.strokeStyle = tool === 'eraser' ? '#ffffff' : color
    ctx.lineWidth = tool === 'eraser' ? lineWidth * 3 : lineWidth
    ctx.lineTo(x, y)
    ctx.stroke()
  }

  const stopDrawing = () => {
    setIsDrawing(false)
  }

  const clearCanvas = () => {
    const canvas = canvasRef.current
    if (!canvas) return

    const ctx = canvas.getContext('2d')
    if (!ctx) return

    ctx.clearRect(0, 0, canvas.width, canvas.height)
  }

  // No question available
  if (!isLoading && !currentQuestion && !error) {
    return (
      <div className="paper min-h-screen flex items-center justify-center">
        <div className="text-center max-w-md">
          <div className="bg-green-100 rounded-full w-24 h-24 flex items-center justify-center mx-auto mb-6">
            <svg className="w-12 h-12 text-green-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z" />
            </svg>
          </div>
          <h2 className="text-2xl font-bold text-gray-900 mb-2">All Done!</h2>
          <p className="text-gray-600 mb-6">{reasoning || "You've completed all available questions for now."}</p>
          <Link
            href={`/dashboard/${folderId}`}
            className="inline-flex items-center gap-2 bg-blue-600 hover:bg-blue-700 text-white font-semibold py-3 px-6 rounded-xl transition-all duration-200"
          >
            <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15 19l-7-7 7-7" />
            </svg>
            Back to Folder
          </Link>
        </div>
      </div>
    )
  }

  return (
    <div className="paper min-h-screen flex flex-col">
      {/* Header */}
      <div className="relative z-10 bg-white border-b border-gray-200" style={{ boxShadow: "0 2px 8px rgba(0,0,0,0.04)" }}>
        <div className="w-full px-4 sm:px-6 lg:px-8 py-4">
          <div className="flex items-center justify-between mb-3">
            <Link
              href={`/dashboard/${folderId}`}
              className="inline-flex items-center text-blue-600 hover:text-blue-700 font-semibold transition-all duration-200 hover:gap-2 gap-1 group text-sm md:text-base"
            >
              <svg className="w-4 h-4 md:w-5 md:h-5 transition-transform duration-200 group-hover:-translate-x-1" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15 19l-7-7 7-7" />
              </svg>
              Exit Study Mode
            </Link>

            {/* Progress indicator */}
            {progress && (
              <div className="flex items-center gap-4">
                <div className="hidden md:flex items-center gap-2 text-sm text-gray-600">
                  <span>Elo: <strong className="text-blue-600">{progress.elo_rating}</strong></span>
                  <span>|</span>
                  <span>Mastery: <strong className="text-green-600">{progress.mastery_percentage}%</strong></span>
                </div>
                <div className="bg-blue-100 text-blue-700 px-3 py-1 rounded-full text-xs md:text-sm font-semibold">
                  {progress.total_questions_answered} answered
                </div>
              </div>
            )}
          </div>

          {/* Question Display */}
          {isLoading ? (
            <div className="bg-gray-100 rounded-xl p-6 animate-pulse">
              <div className="h-6 bg-gray-200 rounded w-3/4"></div>
            </div>
          ) : currentQuestion ? (
            <div className="bg-gradient-to-br from-blue-50 to-blue-100 rounded-xl p-4 md:p-6 border border-blue-200">
              {/* Concept badge */}
              {conceptName && (
                <div className="mb-2">
                  <span className="text-xs font-semibold text-blue-600 bg-blue-200 px-2 py-1 rounded-full">
                    {conceptName}
                  </span>
                </div>
              )}
              <p className="text-gray-800 text-base md:text-lg font-medium leading-relaxed">
                {currentQuestion.question_text}
              </p>
              {/* AI reasoning */}
              {reasoning && (
                <p className="text-sm text-blue-600 mt-2 italic">
                  {reasoning}
                </p>
              )}
            </div>
          ) : error ? (
            <div className="bg-red-50 rounded-xl p-4 md:p-6 border border-red-200">
              <p className="text-red-700">{error}</p>
              <button
                onClick={loadNextQuestion}
                className="mt-2 text-red-600 hover:text-red-700 font-semibold text-sm"
              >
                Try again
              </button>
            </div>
          ) : null}
        </div>
      </div>

      {/* Toolbar */}
      <div className="relative z-10 bg-white border-b border-gray-200 px-4 sm:px-6 lg:px-8 py-3">
        <div className="flex flex-wrap items-center gap-2 md:gap-4">
          {/* Tools */}
          <div className="flex gap-2">
            <button
              onClick={() => setTool('pen')}
              className={`px-3 md:px-4 py-2 rounded-lg font-semibold transition-all duration-200 min-h-[44px] flex items-center gap-2 ${
                tool === 'pen'
                  ? 'bg-blue-600 text-white shadow-md'
                  : 'bg-gray-100 text-gray-700 hover:bg-gray-200'
              }`}
            >
              <svg className="w-4 h-4 md:w-5 md:h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15.232 5.232l3.536 3.536m-2.036-5.036a2.5 2.5 0 113.536 3.536L6.5 21.036H3v-3.572L16.732 3.732z" />
              </svg>
              <span className="hidden sm:inline">Pen</span>
            </button>

            <button
              onClick={() => setTool('eraser')}
              className={`px-3 md:px-4 py-2 rounded-lg font-semibold transition-all duration-200 min-h-[44px] flex items-center gap-2 ${
                tool === 'eraser'
                  ? 'bg-blue-600 text-white shadow-md'
                  : 'bg-gray-100 text-gray-700 hover:bg-gray-200'
              }`}
            >
              <svg className="w-4 h-4 md:w-5 md:h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 7l-.867 12.142A2 2 0 0116.138 21H7.862a2 2 0 01-1.995-1.858L5 7m5 4v6m4-6v6m1-10V4a1 1 0 00-1-1h-4a1 1 0 00-1 1v3M4 7h16" />
              </svg>
              <span className="hidden sm:inline">Eraser</span>
            </button>
          </div>

          {/* Line Width */}
          <div className="flex items-center gap-2">
            <label className="text-xs md:text-sm font-semibold text-gray-700 hidden sm:inline">Size:</label>
            <input
              type="range"
              min="1"
              max="10"
              value={lineWidth}
              onChange={(e) => setLineWidth(Number(e.target.value))}
              className="w-16 md:w-24"
            />
            <span className="text-xs md:text-sm text-gray-600 w-8">{lineWidth}px</span>
          </div>

          {/* Color Picker */}
          {tool === 'pen' && (
            <div className="flex items-center gap-2">
              <label className="text-xs md:text-sm font-semibold text-gray-700 hidden sm:inline">Color:</label>
              <input
                type="color"
                value={color}
                onChange={(e) => setColor(e.target.value)}
                className="w-10 h-10 md:w-12 md:h-12 rounded-lg border-2 border-gray-300 cursor-pointer"
              />
            </div>
          )}

          {/* Clear Button */}
          <button
            onClick={clearCanvas}
            className="ml-auto px-3 md:px-4 py-2 bg-red-500 hover:bg-red-600 text-white rounded-lg font-semibold transition-all duration-200 min-h-[44px] flex items-center gap-2"
          >
            <svg className="w-4 h-4 md:w-5 md:h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
            </svg>
            <span className="hidden sm:inline">Clear</span>
          </button>
        </div>
      </div>

      {/* Canvas Area */}
      <div className="relative z-10 flex-1 p-4 md:p-6">
        <div className="h-full bg-white rounded-xl shadow-lg border-2 border-gray-300 overflow-hidden">
          <canvas
            ref={canvasRef}
            onMouseDown={startDrawing}
            onMouseMove={draw}
            onMouseUp={stopDrawing}
            onMouseLeave={stopDrawing}
            onTouchStart={startDrawing}
            onTouchMove={draw}
            onTouchEnd={stopDrawing}
            className="w-full h-full cursor-crosshair touch-none"
            style={{ touchAction: 'none' }}
          />
        </div>
      </div>

      {/* Answer Submission Bar */}
      <div className="relative z-10 bg-white/80 backdrop-blur-md border-t border-gray-200 px-4 sm:px-6 lg:px-8 py-4">
        {showFeedback && lastResult ? (
          // Show feedback
          <div className={`rounded-xl p-4 mb-4 ${lastResult.is_correct ? 'bg-green-50 border border-green-200' : 'bg-red-50 border border-red-200'}`}>
            <div className="flex items-start gap-3">
              <div className={`rounded-full p-2 ${lastResult.is_correct ? 'bg-green-100' : 'bg-red-100'}`}>
                {lastResult.is_correct ? (
                  <svg className="w-6 h-6 text-green-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 13l4 4L19 7" />
                  </svg>
                ) : (
                  <svg className="w-6 h-6 text-red-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
                  </svg>
                )}
              </div>
              <div className="flex-1">
                <p className={`font-semibold ${lastResult.is_correct ? 'text-green-800' : 'text-red-800'}`}>
                  {lastResult.feedback_message}
                </p>
                <div className="flex flex-wrap gap-3 mt-2 text-sm">
                  <span className={lastResult.mastery_change >= 0 ? 'text-green-600' : 'text-red-600'}>
                    Mastery: {lastResult.mastery_change >= 0 ? '+' : ''}{(lastResult.mastery_change * 100).toFixed(1)}%
                  </span>
                  <span className={lastResult.elo_change >= 0 ? 'text-green-600' : 'text-red-600'}>
                    Elo: {lastResult.elo_change >= 0 ? '+' : ''}{lastResult.elo_change}
                  </span>
                </div>
                {lastResult.concept_mastered && (
                  <p className="text-green-600 font-semibold mt-2">
                    Concept mastered! {lastResult.unlocked_concepts.length > 0 && `Unlocked ${lastResult.unlocked_concepts.length} new concept(s)!`}
                  </p>
                )}
              </div>
            </div>
            <button
              onClick={loadNextQuestion}
              className="mt-4 w-full bg-blue-600 hover:bg-blue-700 text-white font-semibold py-3 px-6 rounded-xl transition-all duration-200"
            >
              Next Question
            </button>
          </div>
        ) : (
          // Show answer buttons
          <div className="flex flex-col sm:flex-row gap-3">
            <p className="text-gray-600 text-sm self-center">Did you solve it correctly?</p>
            <div className="flex gap-3 flex-1 sm:justify-end">
              <button
                onClick={() => handleSubmitAnswer(true)}
                disabled={isSubmitting || !currentQuestion}
                className="flex-1 sm:flex-none bg-green-600 hover:bg-green-700 disabled:bg-green-400 text-white font-semibold py-3 px-6 rounded-xl transition-all duration-200 flex items-center justify-center gap-2"
              >
                {isSubmitting ? (
                  <svg className="animate-spin h-5 w-5" viewBox="0 0 24 24">
                    <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" fill="none"></circle>
                    <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
                  </svg>
                ) : (
                  <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 13l4 4L19 7" />
                  </svg>
                )}
                I Got It Right
              </button>
              <button
                onClick={() => handleSubmitAnswer(false)}
                disabled={isSubmitting || !currentQuestion}
                className="flex-1 sm:flex-none bg-red-600 hover:bg-red-700 disabled:bg-red-400 text-white font-semibold py-3 px-6 rounded-xl transition-all duration-200 flex items-center justify-center gap-2"
              >
                <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
                </svg>
                I Got It Wrong
              </button>
            </div>
          </div>
        )}
      </div>
    </div>
  )
}
