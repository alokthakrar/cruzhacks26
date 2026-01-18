// API client for backend communication

// Toggle between fake and real data
// Set to false when backend is running
export const USE_FAKE_DATA = false

// Backend API base URL
const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000/api'

// Types matching backend models
export type Question = {
  _id: string  // MongoDB uses _id
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

export type Subject = {
  id: string
  name: string
  color: string
  user_id: string
  created_at: string
  last_accessed: string
}

export type SubjectCreate = {
  name: string
  color?: string
}

export type SubjectUpdate = {
  name?: string
  color?: string
}

// Fake data for testing
const FAKE_QUESTIONS: { [key: string]: Question[] } = {
  '1': [
    {
      _id: 'q1',
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
      _id: 'q2',
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
      _id: 'q3',
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
      _id: 'q4',
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
      _id: 'q5',
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
      _id: 'q6',
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
      const question = questions.find(q => q._id === questionId)
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

/**
 * Get a specific question by its ID only (no pdf_id required)
 */
export async function getQuestionById(questionId: string): Promise<Question> {
  if (USE_FAKE_DATA) {
    await new Promise(resolve => setTimeout(resolve, 300))
    for (const questions of Object.values(FAKE_QUESTIONS)) {
      const question = questions.find(q => q._id === questionId)
      if (question) return question
    }
    throw new Error('Question not found')
  }

  const response = await fetch(`${API_BASE_URL}/pdf/question/${questionId}`)

  if (!response.ok) {
    const error = await response.json()
    throw new Error(error.detail || 'Failed to fetch question')
  }

  return await response.json()
}

// ===== Subjects (Folders) API =====

/**
 * Get all subjects (folders) for the current user
 */
export async function getSubjects(): Promise<Subject[]> {
  const response = await fetch(`${API_BASE_URL}/subjects`, {
    // TODO: Add auth header when ready
    // headers: {
    //   'Authorization': `Bearer ${getAuthToken()}`,
    // },
  })

  if (!response.ok) {
    const error = await response.json()
    throw new Error(error.detail || 'Failed to fetch subjects')
  }

  return await response.json()
}

/**
 * Create a new subject (folder)
 */
export async function createSubject(data: SubjectCreate): Promise<Subject> {
  const response = await fetch(`${API_BASE_URL}/subjects`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
      // TODO: Add auth header when ready
      // 'Authorization': `Bearer ${getAuthToken()}`,
    },
    body: JSON.stringify(data),
  })

  if (!response.ok) {
    const error = await response.json()
    throw new Error(error.detail || 'Failed to create subject')
  }

  return await response.json()
}

/**
 * Update a subject (folder)
 */
export async function updateSubject(subjectId: string, data: SubjectUpdate): Promise<Subject> {
  const response = await fetch(`${API_BASE_URL}/subjects/${subjectId}`, {
    method: 'PATCH',
    headers: {
      'Content-Type': 'application/json',
      // TODO: Add auth header when ready
      // 'Authorization': `Bearer ${getAuthToken()}`,
    },
    body: JSON.stringify(data),
  })

  if (!response.ok) {
    const error = await response.json()
    throw new Error(error.detail || 'Failed to update subject')
  }

  return await response.json()
}

/**
 * Delete a subject (folder)
 */
export async function deleteSubject(subjectId: string): Promise<void> {
  const response = await fetch(`${API_BASE_URL}/subjects/${subjectId}`, {
    method: 'DELETE',
    // TODO: Add auth header when ready
    // headers: {
    //   'Authorization': `Bearer ${getAuthToken()}`,
    // },
  })

  if (!response.ok) {
    const error = await response.json()
    throw new Error(error.detail || 'Failed to delete subject')
  }
}

// BKT Types
export type ConceptMastery = {
  concept_id: string
  P_L: number
  P_T: number
  P_G: number
  P_S: number
  mastery_status: 'locked' | 'learning' | 'mastered'
  observations: number
  correct_count: number
  unlocked_at?: string
  mastered_at?: string
  is_unlocked?: boolean
  is_mastered?: boolean
  // Frontend helper fields
  concept_name?: string
  accuracy?: number
  solved_count?: number
}

export type MasteryState = {
  _id: string
  user_id: string
  subject_id: string
  elo_rating: number
  concepts: Record<string, ConceptMastery>
  unlocked_concepts: string[]
  mastered_concepts: string[]
  current_focus?: string
  total_questions_answered: number
  created_at: string
  last_updated: string
}

export type ProgressSummary = {
  total_questions_answered: number
  total_solved_questions: number
  elo_rating: number
  concepts_attempted: number
  concepts_mastered: number
  concepts_unlocked: number
  average_mastery: number
  mastery_percentage: number
  questions_by_concept: Array<{
    concept_id: string
    concept_name: string
    count: number
  }>
  recent_submissions: Array<{
    timestamp: string
    concept_id: string
    is_correct: boolean
    mastery_change: number
  }>
}

export type KnowledgeGraphNode = {
  concept_id: string
  name: string
  description: string
  parents: string[]
  children: string[]
  depth: number
}

export type KnowledgeGraph = {
  _id: string
  subject_id: string
  nodes: Record<string, KnowledgeGraphNode>
  root_concepts: string[]
}

export type BKTQuestion = {
  id: string
  subject_id: string
  concept_id: string
  concept_name?: string
  question_text: string
  question_image?: string
  elo_rating: number
  difficulty_label: string
  success_rate?: number
  times_attempted?: number
}

export type RecommendationResponse = {
  question: BKTQuestion | null
  reasoning: string
  target_concept: string | null
  concept_name?: string
}

export type MistakeRecord = {
  step_number: number
  error_type: 'arithmetic' | 'algebraic' | 'notation' | 'conceptual' | 'unknown'
  error_message?: string
  from_expr?: string
  to_expr?: string
}

export type AnswerSubmission = {
  question_id: string
  is_correct: boolean
  user_answer?: string
  time_taken_seconds?: number
  mistake_count?: number
  mistakes?: MistakeRecord[]
}

export type AnswerResult = {
  submission_id: string
  is_correct: boolean
  mastery_change: number
  elo_change: number
  new_mastery_probability: number
  new_mastery_status: string
  new_student_elo: number
  unlocked_concepts: string[]
  concept_mastered: boolean
  feedback_message: string
  recommended_next_concept?: string
}

export type MasteryStatusResponse = {
  concept_id: string
  mastery_status: 'locked' | 'learning' | 'mastered'
  mastery_probability: number
  observations: number
  correct_count: number
  unlocked_at?: string
  mastered_at?: string
  is_unlocked?: boolean
  is_mastered?: boolean
}

export type ProgressSummary = {
  total_questions_answered: number
  elo_rating: number
  concepts_attempted: number
  concepts_mastered: number
  concepts_unlocked: number
  average_mastery: number
  mastery_percentage: number
  recent_submissions: {
    timestamp: string
    concept_id: string
    is_correct: boolean
    mastery_change: number
  }[]
}

export type KnowledgeGraphNode = {
  concept_id: string
  name: string
  description: string
  parents: string[]
  children: string[]
  depth: number
}

export type KnowledgeGraph = {
  _id: string
  subject_id: string
  name?: string
  description?: string
  nodes: Record<string, KnowledgeGraphNode>
  root_concepts: string[]
}

/**
 * Initialize BKT mastery tracking for a user in a subject.
 * Call this once when user starts a new subject.
 */
export async function initializeBKT(
  userId: string,
  subjectId: string
): Promise<{ mastery_id: string; message: string }> {
  const response = await fetch(
    `${API_BASE_URL}/bkt/initialize?user_id=${encodeURIComponent(userId)}&subject_id=${encodeURIComponent(subjectId)}`,
    {
      method: 'POST',
    }
  )

  if (!response.ok) {
    const error = await response.json()
    throw new Error(error.detail || 'Failed to initialize BKT')
  }

  return await response.json()
}

/**
 * Get the next recommended question for a user based on BKT algorithm.
 */
export async function getNextQuestion(
  userId: string,
  subjectId: string
): Promise<RecommendationResponse> {
  const response = await fetch(
    `${API_BASE_URL}/bkt/recommend/${encodeURIComponent(userId)}/${encodeURIComponent(subjectId)}`
  )

  if (!response.ok) {
    const error = await response.json()
    throw new Error(error.detail || 'Failed to get recommendation')
  }

  return await response.json()
}

/**
 * Submit an answer and update BKT + Elo ratings.
 */
export async function submitAnswer(
  userId: string,
  subjectId: string,
  submission: AnswerSubmission
): Promise<AnswerResult> {
  const response = await fetch(
    `${API_BASE_URL}/bkt/submit?user_id=${encodeURIComponent(userId)}&subject_id=${encodeURIComponent(subjectId)}`,
    {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify(submission),
    }
  )

  if (!response.ok) {
    const error = await response.json()
    throw new Error(error.detail || 'Failed to submit answer')
  }

  return await response.json()
}

/**
 * Get complete mastery state for a user in a subject.
 */
export async function getMasteryState(
  userId: string,
  subjectId: string
): Promise<MasteryState> {
  const response = await fetch(
    `${API_BASE_URL}/bkt/mastery/${encodeURIComponent(userId)}/${encodeURIComponent(subjectId)}`
  )

  if (!response.ok) {
    const error = await response.json()
    throw new Error(error.detail || 'Failed to get mastery state')
  }

  return await response.json()
}

/**
 * Get mastery status for all concepts in a subject.
 */
export async function getConceptMastery(
  userId: string,
  subjectId: string
): Promise<{ concepts: MasteryStatusResponse[] }> {
  const response = await fetch(
    `${API_BASE_URL}/bkt/mastery/${encodeURIComponent(userId)}/${encodeURIComponent(subjectId)}/concepts`
  )

  if (!response.ok) {
    const error = await response.json()
    throw new Error(error.detail || 'Failed to get concept mastery')
  }

  return await response.json()
}

/**
 * Get high-level progress summary for visualization.
 */
export async function getProgress(
  userId: string,
  subjectId: string
): Promise<ProgressSummary> {
  const response = await fetch(
    `${API_BASE_URL}/bkt/progress/${encodeURIComponent(userId)}/${encodeURIComponent(subjectId)}`
  )

  if (!response.ok) {
    const error = await response.json()
    throw new Error(error.detail || 'Failed to get progress')
  }

  return await response.json()
}

/**
 * Get the knowledge graph structure for a subject.
 */
export async function getKnowledgeGraph(
  subjectId: string
): Promise<KnowledgeGraph> {
  const response = await fetch(
    `${API_BASE_URL}/bkt/graph/${encodeURIComponent(subjectId)}`
  )

  if (!response.ok) {
    const error = await response.json()
    throw new Error(error.detail || 'Failed to get knowledge graph')
  }

  return await response.json()
}

export type MistakeHistory = {
  concept_id: string
  total_attempts: number
  mistakes: {
    timestamp: string
    question_id?: string
    user_answer?: string
    P_L_before: number
    P_L_after: number
    mastery_change: number
    student_elo_before: number
    student_elo_after: number
  }[]
  correct_attempts: number
  accuracy: number
  accuracy_percentage: number
}

/**
 * Get mistake history for a specific concept.
 */
export async function getConceptMistakes(
  userId: string,
  subjectId: string,
  conceptId: string,
  limit: number = 20
): Promise<MistakeHistory> {
  const response = await fetch(
    `${API_BASE_URL}/bkt/mistakes/${encodeURIComponent(userId)}/${encodeURIComponent(subjectId)}/${encodeURIComponent(conceptId)}?limit=${limit}`
  )

  if (!response.ok) {
    const error = await response.json()
    throw new Error(error.detail || 'Failed to get mistake history')
  }

  return await response.json()
}

/**
 * Reset mastery state for a user (for testing/debugging).
 */
export async function resetMastery(
  userId: string,
  subjectId: string
): Promise<{ message: string }> {
  const response = await fetch(
    `${API_BASE_URL}/bkt/mastery/${encodeURIComponent(userId)}/${encodeURIComponent(subjectId)}`,
    {
      method: 'DELETE',
    }
  )

  if (!response.ok) {
    const error = await response.json()
    throw new Error(error.detail || 'Failed to reset mastery')
  }

  return await response.json()
}
