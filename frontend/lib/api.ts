// API client for backend communication

// Toggle between fake and real data
// Set to false when backend is running
export const USE_FAKE_DATA = true

// Backend API base URL
const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000/api'

// Types matching backend models
export type Question = {
  id: string
  pdf_id: string
  user_id: string
  subject_id?: string
  page_number: number
  question_number: number
  text_content: string
  latex_content?: string
  question_type: string
  difficulty_estimate?: string
  cropped_image: string // base64 encoded PNG
  bounding_box: {
    x: number
    y: number
    width: number
    height: number
  }
  extraction_confidence: number
  created_at: string
}

export type PDFUploadResponse = {
  pdf_id: string
  filename: string
  subject_id?: string
  status: string
  message: string
  total_pages: number
  question_count: number
}

export type QuestionsListResponse = {
  questions: Question[]
  total: number
  page: number
  limit: number
}

// Fake data for testing
const FAKE_QUESTIONS: { [key: string]: Question[] } = {
  '1': [
    {
      id: 'q1',
      pdf_id: 'pdf1',
      user_id: 'user1',
      subject_id: '1',
      page_number: 1,
      question_number: 1,
      text_content: 'Find the derivative of f(x) = 3x² + 2x - 5',
      question_type: 'derivative',
      difficulty_estimate: 'medium',
      cropped_image: '',
      bounding_box: { x: 0, y: 0, width: 100, height: 50 },
      extraction_confidence: 0.95,
      created_at: '2026-01-15T10:30:00',
    },
    {
      id: 'q2',
      pdf_id: 'pdf1',
      user_id: 'user1',
      subject_id: '1',
      page_number: 1,
      question_number: 2,
      text_content: 'Evaluate the integral: ∫(4x³ - 2x + 1)dx',
      question_type: 'integral',
      difficulty_estimate: 'medium',
      cropped_image: '',
      bounding_box: { x: 0, y: 60, width: 100, height: 50 },
      extraction_confidence: 0.92,
      created_at: '2026-01-15T10:30:00',
    },
    {
      id: 'q3',
      pdf_id: 'pdf1',
      user_id: 'user1',
      subject_id: '1',
      page_number: 2,
      question_number: 3,
      text_content: 'Using the chain rule, find dy/dx for y = sin(x²)',
      question_type: 'derivative',
      difficulty_estimate: 'hard',
      cropped_image: '',
      bounding_box: { x: 0, y: 0, width: 100, height: 50 },
      extraction_confidence: 0.88,
      created_at: '2026-01-15T10:30:00',
    },
    {
      id: 'q4',
      pdf_id: 'pdf1',
      user_id: 'user1',
      subject_id: '1',
      page_number: 2,
      question_number: 4,
      text_content: 'Find the critical points of f(x) = x³ - 6x² + 9x + 2',
      question_type: 'equation',
      difficulty_estimate: 'hard',
      cropped_image: '',
      bounding_box: { x: 0, y: 60, width: 100, height: 50 },
      extraction_confidence: 0.90,
      created_at: '2026-01-15T10:30:00',
    },
  ],
  '2': [
    {
      id: 'q5',
      pdf_id: 'pdf2',
      user_id: 'user1',
      subject_id: '2',
      page_number: 1,
      question_number: 1,
      text_content: 'A 5kg object is accelerating at 3m/s². What is the net force?',
      question_type: 'word_problem',
      difficulty_estimate: 'easy',
      cropped_image: '',
      bounding_box: { x: 0, y: 0, width: 100, height: 50 },
      extraction_confidence: 0.93,
      created_at: '2026-01-14T14:20:00',
    },
    {
      id: 'q6',
      pdf_id: 'pdf2',
      user_id: 'user1',
      subject_id: '2',
      page_number: 1,
      question_number: 2,
      text_content: 'Calculate the momentum of a 10kg object moving at 15m/s',
      question_type: 'word_problem',
      difficulty_estimate: 'easy',
      cropped_image: '',
      bounding_box: { x: 0, y: 60, width: 100, height: 50 },
      extraction_confidence: 0.91,
      created_at: '2026-01-14T14:20:00',
    },
  ],
}

// API Functions

/**
 * Upload a PDF and extract questions
 */
export async function uploadPDF(
  file: File,
  subjectId: string
): Promise<PDFUploadResponse> {
  if (USE_FAKE_DATA) {
    // Simulate upload delay
    await new Promise(resolve => setTimeout(resolve, 2000))

    return {
      pdf_id: `pdf_${Date.now()}`,
      filename: file.name,
      subject_id: subjectId,
      status: 'completed',
      message: 'Successfully extracted 4 questions from 2 pages (fake data)',
      total_pages: 2,
      question_count: 4,
    }
  }

  // Real API call
  const formData = new FormData()
  formData.append('pdf', file)
  formData.append('subject_id', subjectId)

  const response = await fetch(`${API_BASE_URL}/pdf/upload`, {
    method: 'POST',
    body: formData,
    // Add auth header when ready
    // headers: {
    //   'Authorization': `Bearer ${getAuthToken()}`,
    // },
  })

  if (!response.ok) {
    const error = await response.json()
    throw new Error(error.detail || 'Failed to upload PDF')
  }

  return await response.json()
}

/**
 * Get all questions for a subject (folder)
 */
export async function getSubjectQuestions(
  subjectId: string,
  page: number = 1,
  limit: number = 20
): Promise<QuestionsListResponse> {
  if (USE_FAKE_DATA) {
    // Simulate API delay
    await new Promise(resolve => setTimeout(resolve, 500))

    const questions = FAKE_QUESTIONS[subjectId] || []
    return {
      questions,
      total: questions.length,
      page,
      limit,
    }
  }

  // Real API call
  const response = await fetch(
    `${API_BASE_URL}/pdf/subject/${subjectId}/questions?page=${page}&limit=${limit}`,
    {
      // Add auth header when ready
      // headers: {
      //   'Authorization': `Bearer ${getAuthToken()}`,
      // },
    }
  )

  if (!response.ok) {
    const error = await response.json()
    throw new Error(error.detail || 'Failed to fetch questions')
  }

  return await response.json()
}

/**
 * Get a specific question by ID
 */
export async function getQuestion(
  pdfId: string,
  questionId: string
): Promise<Question> {
  if (USE_FAKE_DATA) {
    // Simulate API delay
    await new Promise(resolve => setTimeout(resolve, 300))

    // Find question in fake data
    for (const questions of Object.values(FAKE_QUESTIONS)) {
      const question = questions.find(q => q.id === questionId)
      if (question) return question
    }
    throw new Error('Question not found')
  }

  // Real API call
  const response = await fetch(
    `${API_BASE_URL}/pdf/${pdfId}/questions/${questionId}`,
    {
      // Add auth header when ready
      // headers: {
      //   'Authorization': `Bearer ${getAuthToken()}`,
      // },
    }
  )

  if (!response.ok) {
    const error = await response.json()
    throw new Error(error.detail || 'Failed to fetch question')
  }

  return await response.json()
}
