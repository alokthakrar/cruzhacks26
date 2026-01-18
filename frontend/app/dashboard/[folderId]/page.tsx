'use client'

import { useState, useEffect } from 'react'
import Link from 'next/link'
import { useParams, useRouter } from 'next/navigation'
import {
  getSubjectQuestions,
  getSubjects,
  Question,
  initializeBKT,
  getMasteryState,
  getProgress,
  MasteryState,
  ProgressSummary
} from '@/lib/api'

// Type definitions for UI
type UIQuestion = {
  id: string
  questionText: string
  questionNumber: number
  pdfName: string
  created_at: string
}

// Map color names to Tailwind classes
const FOLDER_COLOR_MAP: Record<string, { bg: string; icon: string; badge: string; badgeHover: string }> = {
  Blue: { bg: 'from-blue-50 to-blue-100', icon: 'text-blue-500', badge: 'from-blue-500 to-blue-600', badgeHover: 'text-blue-500' },
  Purple: { bg: 'from-purple-50 to-purple-100', icon: 'text-purple-500', badge: 'from-purple-500 to-purple-600', badgeHover: 'text-purple-500' },
  Green: { bg: 'from-green-50 to-green-100', icon: 'text-green-500', badge: 'from-green-500 to-green-600', badgeHover: 'text-green-500' },
  Orange: { bg: 'from-orange-50 to-orange-100', icon: 'text-orange-500', badge: 'from-orange-500 to-orange-600', badgeHover: 'text-orange-500' },
  Pink: { bg: 'from-pink-50 to-pink-100', icon: 'text-pink-500', badge: 'from-pink-500 to-pink-600', badgeHover: 'text-pink-500' },
  Indigo: { bg: 'from-indigo-50 to-indigo-100', icon: 'text-indigo-500', badge: 'from-indigo-500 to-indigo-600', badgeHover: 'text-indigo-500' },
}

const getColorClasses = (colorName: string) => {
  return FOLDER_COLOR_MAP[colorName] || FOLDER_COLOR_MAP['Blue']
}

// Temporary user ID until auth is implemented
const TEMP_USER_ID = 'demo_user'

export default function FolderQuestionsPage() {
  const params = useParams()
  const router = useRouter()
  const folderId = params.folderId as string

  const [questions, setQuestions] = useState<UIQuestion[]>([])
  const [isLoading, setIsLoading] = useState(true)
  const [folderName, setFolderName] = useState('Loading...')
  const [folderColor, setFolderColor] = useState('Blue')

  // BKT state
  const [masteryState, setMasteryState] = useState<MasteryState | null>(null)
  const [progress, setProgress] = useState<ProgressSummary | null>(null)
  const [isInitializing, setIsInitializing] = useState(false)
  const [bktError, setBktError] = useState<string | null>(null)

  // Load folder info (name and color) from API
  const loadFolderInfo = async () => {
    try {
      const subjects = await getSubjects()
      const folder = subjects.find(s => s.id === folderId)
      if (folder) {
        setFolderName(folder.name)
        setFolderColor(folder.color || 'Blue')
      }
    } catch (error) {
      console.error('Failed to load folder info:', error)
    }
  }

  // Load questions from API
  const loadQuestions = async () => {
    setIsLoading(true)
    try {
      const response = await getSubjectQuestions(folderId, 1, 100)
      // Convert API questions to UI format
      const uiQuestions: UIQuestion[] = response.questions.map(q => ({
        id: q._id,  // MongoDB uses _id
        questionText: q.text_content,
        questionNumber: q.question_number,
        pdfName: 'Uploaded PDF', // TODO: Get actual PDF name
        created_at: q.created_at,
      }))
      setQuestions(uiQuestions)
    } catch (error) {
      console.error('Failed to load questions:', error)
    } finally {
      setIsLoading(false)
    }
  }

  // Load BKT mastery state
  const loadMasteryState = async () => {
    try {
      const [mastery, prog] = await Promise.all([
        getMasteryState(TEMP_USER_ID, folderId),
        getProgress(TEMP_USER_ID, folderId)
      ])
      setMasteryState(mastery)
      setProgress(prog)
      setBktError(null)
    } catch (error) {
      // Mastery not initialized yet - that's OK
      console.log('Mastery state not found, user needs to initialize')
      setMasteryState(null)
      setProgress(null)
    }
  }

  // Navigate to a random question
  const navigateToRandomQuestion = () => {
    if (questions.length > 0) {
      const randomIndex = Math.floor(Math.random() * questions.length)
      const randomQuestion = questions[randomIndex]
      router.push(`/dashboard/${folderId}/question/${randomQuestion.id}`)
    }
  }

  // Initialize BKT for this subject
  const handleStartLearning = async () => {
    setIsInitializing(true)
    setBktError(null)
    try {
      await initializeBKT(TEMP_USER_ID, folderId)
      await loadMasteryState()
      // Navigate to a random question
      navigateToRandomQuestion()
    } catch (error) {
      console.error('Failed to initialize BKT:', error)
      setBktError(error instanceof Error ? error.message : 'Failed to start learning')
    } finally {
      setIsInitializing(false)
    }
  }

  // Continue learning (already initialized) - go to random question
  const handleContinueLearning = () => {
    navigateToRandomQuestion()
  }

  useEffect(() => {
    loadFolderInfo()
    loadQuestions()
    loadMasteryState()
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [folderId])

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
            <div className={`p-3 rounded-xl bg-gradient-to-br ${getColorClasses(folderColor).bg}`}>
              <svg
                className={`w-12 h-12 ${getColorClasses(folderColor).icon}`}
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

        {/* BKT Progress Card */}
        {(masteryState || progress) && (
          <div className="mb-8 bg-gradient-to-br from-blue-50 to-indigo-50 rounded-2xl p-6 border border-blue-200 animate-fade-in">
            <div className="flex flex-col md:flex-row md:items-center justify-between gap-4">
              <div>
                <h2 className="text-xl font-bold text-gray-900 mb-2">Your Progress</h2>
                <div className="flex flex-wrap gap-4 text-sm">
                  <div className="flex items-center gap-2">
                    <div className="w-3 h-3 bg-green-500 rounded-full"></div>
                    <span className="text-gray-700">
                      <strong>{progress?.concepts_mastered || 0}</strong> concepts mastered
                    </span>
                  </div>
                  <div className="flex items-center gap-2">
                    <div className="w-3 h-3 bg-yellow-500 rounded-full"></div>
                    <span className="text-gray-700">
                      <strong>{progress?.concepts_unlocked || 0}</strong> concepts unlocked
                    </span>
                  </div>
                  <div className="flex items-center gap-2">
                    <div className="w-3 h-3 bg-blue-500 rounded-full"></div>
                    <span className="text-gray-700">
                      Elo: <strong>{progress?.elo_rating || 1200}</strong>
                    </span>
                  </div>
                </div>
              </div>

              {/* Progress Bar */}
              <div className="flex-1 max-w-md">
                <div className="flex justify-between text-sm text-gray-600 mb-1">
                  <span>Average Concept Mastery (P_L)</span>
                  <span className="font-semibold">{progress?.mastery_percentage || 0}%</span>
                </div>
                <div className="h-3 bg-gray-200 rounded-full overflow-hidden">
                  <div
                    className="h-full bg-gradient-to-r from-blue-500 to-indigo-500 rounded-full transition-all duration-500"
                    style={{ width: `${progress?.mastery_percentage || 0}%` }}
                  ></div>
                </div>
              </div>

              <button
                onClick={handleContinueLearning}
                className="bg-blue-600 hover:bg-blue-700 text-white font-semibold py-3 px-6 rounded-xl transition-all duration-200 hover:scale-105 active:scale-95 flex items-center gap-2"
              >
                Continue Learning
                <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13 7l5 5m0 0l-5 5m5-5H6" />
                </svg>
              </button>
            </div>
          </div>
        )}

        {/* Start Learning Card (when no mastery state) */}
        {!masteryState && !isLoading && questions.length > 0 && (
          <div className="mb-8 bg-gradient-to-br from-green-50 to-emerald-50 rounded-2xl p-6 border border-green-200 animate-fade-in">
            <div className="flex flex-col md:flex-row md:items-center justify-between gap-4">
              <div>
                <h2 className="text-xl font-bold text-gray-900 mb-2">Ready to Learn?</h2>
                <p className="text-gray-600">
                  Start adaptive learning powered by AI. We'll track your progress and recommend questions based on your skill level.
                </p>
                {bktError && (
                  <p className="text-red-600 text-sm mt-2">{bktError}</p>
                )}
              </div>
              <button
                onClick={handleStartLearning}
                disabled={isInitializing}
                className="bg-green-600 hover:bg-green-700 disabled:bg-green-400 text-white font-semibold py-3 px-6 rounded-xl transition-all duration-200 hover:scale-105 active:scale-95 flex items-center gap-2 whitespace-nowrap"
              >
                {isInitializing ? (
                  <>
                    <svg className="animate-spin h-5 w-5" viewBox="0 0 24 24">
                      <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" fill="none"></circle>
                      <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
                    </svg>
                    Starting...
                  </>
                ) : (
                  <>
                    Start Learning
                    <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13 7l5 5m0 0l-5 5m5-5H6" />
                    </svg>
                  </>
                )}
              </button>
            </div>
          </div>
        )}

        {/* Loading State */}
        {isLoading ? (
          <div className="text-center py-12 animate-fade-in">
            <div className="inline-block animate-spin rounded-full h-12 w-12 border-4 border-gray-300 border-t-blue-600 mb-4"></div>
            <p className="text-gray-600 text-lg">Loading questions...</p>
          </div>
        ) : questions.length > 0 ? (
          <>
            <h2 className="text-xl font-bold text-gray-900 mb-4">All Questions</h2>
            <div className="grid grid-cols-1 lg:grid-cols-2 gap-4 md:gap-6">
              {questions.map((question, index) => (
                <Link
                  key={question.id}
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
                    <div className={`bg-gradient-to-br ${getColorClasses(folderColor).badge} text-white rounded-lg px-4 py-2 font-bold text-sm`}>
                      Question {question.questionNumber}
                    </div>
                    <div className={`${getColorClasses(folderColor).icon} opacity-50 group-hover:opacity-100 transition-opacity duration-200`}>
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
                    <span className={`${getColorClasses(folderColor).icon} font-semibold text-sm md:text-base`}>
                      Start Working →
                    </span>
                  </div>
                </Link>
              ))}
            </div>
          </>
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
