'use client'

import { useState, useRef, useEffect } from 'react'
import Link from 'next/link'
import { useParams } from 'next/navigation'

// Type definitions
type Question = {
  id: string
  questionText: string
  questionNumber: number
  pdfName: string
}

// Fake question data
const FAKE_QUESTIONS: { [key: string]: Question } = {
  'q1': {
    id: 'q1',
    questionText: 'Find the derivative of f(x) = 3x² + 2x - 5',
    questionNumber: 1,
    pdfName: 'Calculus Chapter 3',
  },
  'q2': {
    id: 'q2',
    questionText: 'Evaluate the integral: ∫(4x³ - 2x + 1)dx',
    questionNumber: 2,
    pdfName: 'Calculus Chapter 3',
  },
  'q3': {
    id: 'q3',
    questionText: 'Using the chain rule, find dy/dx for y = sin(x²)',
    questionNumber: 3,
    pdfName: 'Calculus Chapter 3',
  },
  'q4': {
    id: 'q4',
    questionText: 'Find the critical points of f(x) = x³ - 6x² + 9x + 2',
    questionNumber: 4,
    pdfName: 'Calculus Chapter 3',
  },
  'q5': {
    id: 'q5',
    questionText: 'A 5kg object is accelerating at 3m/s². What is the net force?',
    questionNumber: 1,
    pdfName: 'Physics Problem Set',
  },
  'q6': {
    id: 'q6',
    questionText: 'Calculate the momentum of a 10kg object moving at 15m/s',
    questionNumber: 2,
    pdfName: 'Physics Problem Set',
  },
}

const FOLDER_NAMES: { [key: string]: string } = {
  '1': 'Calculus',
  '2': 'Physics',
}

export default function QuestionCanvasPage() {
  const params = useParams()
  const folderId = params.folderId as string
  const questionId = params.questionId as string

  const canvasRef = useRef<HTMLCanvasElement>(null)
  const [isDrawing, setIsDrawing] = useState(false)
  const [tool, setTool] = useState<'pen' | 'eraser'>('pen')
  const [color, setColor] = useState('#000000')
  const [lineWidth, setLineWidth] = useState(2)

  const question = FAKE_QUESTIONS[questionId]
  const folderName = FOLDER_NAMES[folderId] || 'Unknown Folder'

  useEffect(() => {
    const canvas = canvasRef.current
    if (!canvas) return

    const ctx = canvas.getContext('2d')
    if (!ctx) return

    // Set canvas size to match display size
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

  if (!question) {
    return (
      <div className="min-h-screen bg-[#fefdfb] flex items-center justify-center">
        <div className="text-center">
          <p className="text-gray-600 text-lg mb-4">Question not found</p>
          <Link href="/dashboard" className="text-blue-600 hover:text-blue-700 font-semibold">
            ← Back to Dashboard
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
              Back to {folderName}
            </Link>

            <div className="flex items-center gap-2">
              <span className="bg-blue-100 text-blue-700 px-3 py-1 rounded-full text-xs md:text-sm font-semibold">
                Question {question.questionNumber}
              </span>
            </div>
          </div>

          {/* Question Display */}
          <div className="bg-gradient-to-br from-blue-50 to-blue-100 rounded-xl p-4 md:p-6 border border-blue-200">
            <p className="text-gray-800 text-base md:text-lg font-medium leading-relaxed">
              {question.questionText}
            </p>
          </div>
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

          {/* Color Picker (only for pen) */}
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

      {/* AI Feedback Area (placeholder for now) */}
      <div className="relative z-10 bg-white/80 backdrop-blur-md border-t border-gray-200 px-4 sm:px-6 lg:px-8 py-3">
        <div className="flex items-center gap-2 text-sm text-gray-600">
          <div className="w-2 h-2 bg-green-500 rounded-full animate-pulse"></div>
          <span className="font-medium">AI is monitoring your work...</span>
          <span className="text-xs text-gray-400 ml-auto hidden md:inline">
            Mistakes will be highlighted in red
          </span>
        </div>
      </div>
    </div>
  )
}
