'use client'

import { useState, useEffect } from 'react'
import Link from 'next/link'
import { useParams } from 'next/navigation'
import { getSubjectQuestions, Question, initializeMastery } from '@/lib/api'

// Type definitions for UI
type UIQuestion = {
  id: string
  questionText: string
  questionNumber: number
  pdfName: string
  created_at: string
}

const FOLDER_COLORS = [
  { bg: 'from-blue-50 to-blue-100', icon: 'text-blue-500' },
  { bg: 'from-purple-50 to-purple-100', icon: 'text-purple-500' },
  { bg: 'from-green-50 to-green-100', icon: 'text-green-500' },
  { bg: 'from-orange-50 to-orange-100', icon: 'text-orange-500' },
  { bg: 'from-pink-50 to-pink-100', icon: 'text-pink-500' },
  { bg: 'from-indigo-50 to-indigo-100', icon: 'text-indigo-500' },
]

const getRandomFolderColor = () => {
  return FOLDER_COLORS[Math.floor(Math.random() * FOLDER_COLORS.length)]
}

export default function FolderQuestionsPage() {
  const params = useParams()
  const folderId = params.folderId as string

  const [questions, setQuestions] = useState<UIQuestion[]>([])
  const [isLoading, setIsLoading] = useState(true)
  const [folderName, setFolderName] = useState('Loading...')
  const [folderColor] = useState(getRandomFolderColor())

  // Load questions from API
  const loadQuestions = async () => {
    setIsLoading(true)
    try {
      const response = await getSubjectQuestions(folderId, 1, 100)
      // Convert API questions to UI format
      const uiQuestions: UIQuestion[] = response.questions.map(q => ({
        id: q.id,
        questionText: q.text_content,
        questionNumber: q.question_number,
        pdfName: 'Uploaded PDF', // TODO: Get actual PDF name
        created_at: q.created_at,
      }))
      setQuestions(uiQuestions)
      // Set folder name based on first question or default
      if (uiQuestions.length > 0) {
        setFolderName('Questions')
      }
    } catch (error) {
      console.error('Failed to load questions:', error)
      setFolderName('Folder')
    } finally {
      setIsLoading(false)
    }
  }

  useEffect(() => {
    loadQuestions()
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [folderId])

  // Initialize BKT mastery for this folder/subject when user opens it
  useEffect(() => {
    async function initializeBKT() {
      try {
        // Only initialize for folders that have knowledge graphs
        // For now, we'll try to initialize for all folders (will silently fail if no graph exists)
        await initializeMastery('dev_user_123', folderId)
        console.log(`BKT mastery initialized for ${folderName}`)
      } catch (error) {
        // Silently fail - this is expected if there's no knowledge graph for this subject yet
        console.log(`No knowledge graph for ${folderName} - BKT not initialized`)
      }
    }

    initializeBKT()
  }, [folderId, folderName])

  // Format date nicely
  const formatDate = (dateString: string) => {
    const date = new Date(dateString)
    return date.toLocaleDateString('en-US', {
      month: 'short',
      day: 'numeric',
      year: 'numeric'
    })
  }

  return (
    <div className="paper min-h-screen">
      {/* Main content */}
      <div className="relative z-10 w-full px-4 sm:px-6 lg:px-8 py-8 md:py-12">
        {/* Header with back button */}
        <div className="mb-8">
          <Link
            href="/dashboard"
            className="inline-flex items-center text-blue-600 hover:text-blue-700 mb-4 font-semibold transition-all duration-200 hover:gap-3 gap-2 group"
          >
            <svg className="w-5 h-5 transition-transform duration-200 group-hover:-translate-x-1" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15 19l-7-7 7-7" />
            </svg>
            Back to Dashboard
          </Link>
          <div className="flex items-center gap-3 animate-fade-in">
            <div className={`p-3 rounded-xl bg-gradient-to-br ${folderColor.bg}`}>
              <svg
                className={`w-12 h-12 ${folderColor.icon}`}
                fill="currentColor"
                viewBox="0 0 20 20"
              >
                <path d="M2 6a2 2 0 012-2h5l2 2h5a2 2 0 012 2v6a2 2 0 01-2 2H4a2 2 0 01-2-2V6z" />
              </svg>
            </div>
            <div>
              <h1 className="text-3xl md:text-4xl font-bold text-gray-900">
                {folderName}
              </h1>
              <p className="text-sm md:text-base text-gray-600">
                {questions.length} {questions.length === 1 ? 'question' : 'questions'} to solve
              </p>
            </div>
          </div>
        </div>

        {/* Loading State */}
        {isLoading ? (
          <div className="text-center py-12 animate-fade-in">
            <div className="inline-block animate-spin rounded-full h-12 w-12 border-4 border-gray-300 border-t-blue-600 mb-4"></div>
            <p className="text-gray-600 text-lg">Loading questions...</p>
          </div>
        ) : questions.length > 0 ? (
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-4 md:gap-6">
            {questions.map((question, index) => (
              <Link
                key={question.id ?? `${folderId}-${index}`}
                href={`/dashboard/${folderId}/question/${question.id}`}
                className="bg-white rounded-xl p-6 transition-all duration-300 border border-gray-200 cursor-pointer hover:-translate-y-1 group"
                style={{
                  animation: `fadeInUp 0.5s ease-out ${index * 0.1}s both`,
                  boxShadow: "0 4px 12px rgba(0,0,0,0.06)",
                }}
                onMouseEnter={(e) => {
                  e.currentTarget.style.boxShadow = "0 12px 24px rgba(0,0,0,0.08)";
                }}
                onMouseLeave={(e) => {
                  e.currentTarget.style.boxShadow = "0 4px 12px rgba(0,0,0,0.06)";
                }}
              >
                {/* Question Number Badge */}
                <div className="flex items-start justify-between mb-4">
                  <div className="bg-gradient-to-br from-blue-500 to-blue-600 text-white rounded-lg px-4 py-2 font-bold text-sm">
                    Question {question.questionNumber}
                  </div>
                  <div className="text-gray-400 group-hover:text-blue-500 transition-colors duration-200">
                    <svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 5l7 7-7 7" />
                    </svg>
                  </div>
                </div>

                {/* Question Text */}
                <div className="mb-4">
                  <p className="text-gray-800 text-base md:text-lg leading-relaxed line-clamp-3">
                    {question.questionText}
                  </p>
                </div>

                {/* Footer */}
                <div className="flex items-center justify-between pt-4 border-t border-gray-200">
                  <span className="text-xs md:text-sm text-gray-500">
                    {question.pdfName}
                  </span>
                  <button className="text-blue-600 hover:text-blue-700 font-semibold text-sm md:text-base transition-colors duration-200">
                    Start Working →
                  </button>
                </div>
              </Link>
            ))}
          </div>
        ) : (
          <div className="text-center py-12 md:py-16 bg-white/50 backdrop-blur-sm rounded-lg border-2 border-dashed border-gray-300 animate-fade-in">
            <div className="max-w-md mx-auto">
              <div className="bg-gray-100 rounded-full w-20 h-20 md:w-24 md:h-24 flex items-center justify-center mx-auto mb-4 md:mb-6">
                <svg className="w-10 h-10 md:w-12 md:h-12 text-gray-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M8.228 9c.549-1.165 2.03-2 3.772-2 2.21 0 4 1.343 4 3 0 1.4-1.278 2.575-3.006 2.907-.542.104-.994.54-.994 1.093m0 3h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
                </svg>
              </div>
              <p className="text-gray-700 text-base md:text-lg font-semibold mb-2">
                No questions yet
              </p>
              <p className="text-gray-500 text-sm md:text-base">
                Upload a PDF to this folder and our AI will parse the questions for you
              </p>
            </div>
          </div>
        )}
      </div>

      {/* Add keyframe animations */}
      <style jsx>{`
        @keyframes fadeInUp {
          from {
            opacity: 0;
            transform: translateY(20px);
          }
          to {
            opacity: 1;
            transform: translateY(0);
          }
        }

        @keyframes fade-in {
          from {
            opacity: 0;
          }
          to {
            opacity: 1;
          }
        }

        .animate-fade-in {
          animation: fade-in 0.3s ease-out;
        }
      `}</style>
    </div>
  )
}
