'use client'

import { useState, useEffect, useLayoutEffect, useRef } from 'react'
import Link from 'next/link'
import { useParams } from 'next/navigation'
import { getKnowledgeGraph, getMasteryState, getConceptMistakes, getProgress, type KnowledgeGraph, type ConceptMastery, type MistakeHistory, type ProgressSummary } from '@/lib/api'

const FOLDER_NAMES: { [key: string]: string } = {
  '1': 'Calculus',
  '2': 'Physics',
  'algebra_basics': 'Basic Algebra',
}

// Map folder IDs to subject IDs (for now they're the same, but this allows flexibility)
const FOLDER_TO_SUBJECT: { [key: string]: string } = {
  '1': '1',
  '2': '2',
  'algebra_basics': 'algebra_basics',
}

// Temporary user ID until auth is implemented (must match study mode!)
const TEMP_USER_ID = 'demo_user'

export default function ProgressPage() {
  const params = useParams()
  const folderId = params.folderId as string
  const subjectId = FOLDER_TO_SUBJECT[folderId] || folderId

  const [knowledgeGraph, setKnowledgeGraph] = useState<KnowledgeGraph | null>(null)
  const [masteryData, setMasteryData] = useState<ConceptMastery[]>([])
  const [progressSummary, setProgressSummary] = useState<ProgressSummary | null>(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const [connections, setConnections] = useState<Array<{ x1: number; y1: number; x2: number; y2: number }>>([])
  const [selectedConcept, setSelectedConcept] = useState<string | null>(null)
  const [mistakeHistory, setMistakeHistory] = useState<MistakeHistory | null>(null)
  const [loadingMistakes, setLoadingMistakes] = useState(false)
  const containerRef = useRef<HTMLDivElement | null>(null)
  const nodeRefs = useRef<Record<string, HTMLDivElement | null>>({})

  const folderName = FOLDER_NAMES[folderId] || 'Unknown Subject'

  useEffect(() => {
    async function loadProgressData() {
      try {
        setLoading(true)
        setError(null)

        // Fetch knowledge graph
        const graph = await getKnowledgeGraph(subjectId)
        setKnowledgeGraph(graph)

        // Fetch progress summary
        try {
          const summary = await getProgress(TEMP_USER_ID, subjectId)
          setProgressSummary(summary)
        } catch (err) {
          // No progress yet
        }

        // Try to fetch user mastery (will fail if not initialized yet)
        try {
          const masteryState = await getMasteryState(TEMP_USER_ID, subjectId)
          console.log('📊 Mastery State Loaded:', masteryState)
          console.log('📋 Unlocked Concepts:', masteryState.unlocked_concepts)
          console.log('🎯 Mastered Concepts:', masteryState.mastered_concepts)
          
          // Convert concepts object to array with proper typing
          const conceptsArray: ConceptMastery[] = Object.entries(masteryState.concepts).map(([conceptId, data]) => ({
            concept_id: conceptId,
            P_L: data.P_L,
            P_T: data.P_T,
            P_G: data.P_G,
            P_S: data.P_S,
            mastery_status: data.mastery_status,
            observations: data.observations,
            correct_count: data.correct_count,
            unlocked_at: data.unlocked_at,
            mastered_at: data.mastered_at,
            is_unlocked: masteryState.unlocked_concepts.includes(conceptId),
            is_mastered: masteryState.mastered_concepts.includes(conceptId)
          }))
          
          console.log('✅ Concepts Array:', conceptsArray)
          console.log('🔍 First concept detail:', conceptsArray[0])
          setMasteryData(conceptsArray)
        } catch (err) {
          console.error('⚠️ Failed to load mastery state:', err)
          // No mastery data yet - show all locked except root concepts
          if (graph.nodes && Array.isArray(graph.nodes)) {
            const initialMastery: ConceptMastery[] = graph.nodes.map(node => ({
              concept_id: node.id,
              P_L: node.bkt_params.P_L0,
              P_T: node.bkt_params.P_T,
              P_G: node.bkt_params.P_G,
              P_S: node.bkt_params.P_S,
              mastery_status: 'locked' as const,
              observations: 0,
              correct_count: 0,
              is_unlocked: graph.root_concepts.includes(node.id),
              is_mastered: false,
            }))
            setMasteryData(initialMastery)
          }
        }
      } catch (err) {
        console.error('Error loading progress data:', err)
        setError(err instanceof Error ? err.message : 'Failed to load progress data')
      } finally {
        setLoading(false)
      }
    }

    loadProgressData()
  }, [subjectId])

  const getMasteryForConcept = (conceptId: string): ConceptMastery | undefined => {
    return masteryData.find(m => m.concept_id === conceptId)
  }

  const getNodeId = (node: { id?: string; concept_id?: string }) => {
    return node.id ?? node.concept_id ?? ''
  }

  const getNodePrereqs = (node: { prerequisites?: string[]; parents?: string[] }) => {
    return node.prerequisites ?? node.parents ?? []
  }

  const getConceptColor = (mastery?: ConceptMastery) => {
    if (!mastery || !mastery.is_unlocked) {
      return {
        bg: 'from-gray-50 to-gray-100',
        border: 'border-gray-200',
        text: 'text-gray-700',
        progress: 'bg-gray-400',
        badge: 'bg-gray-100 text-gray-600'
      }
    }
    if (mastery.is_mastered || mastery.P_L >= 0.90) {
      return {
        bg: 'from-green-50 to-green-100',
        border: 'border-green-200',
        text: 'text-green-800',
        progress: 'bg-green-500',
        badge: 'bg-green-100 text-green-700'
      }
    }
    if (mastery.P_L >= 0.40) {
      return {
        bg: 'from-yellow-50 to-yellow-100',
        border: 'border-yellow-200',
        text: 'text-yellow-800',
        progress: 'bg-yellow-500',
        badge: 'bg-yellow-100 text-yellow-700'
      }
    }
    return {
      bg: 'from-blue-50 to-blue-100',
      border: 'border-blue-200',
      text: 'text-blue-800',
      progress: 'bg-blue-500',
      badge: 'bg-blue-100 text-blue-700'
    }
  }

  const getMasteryLabel = (mastery?: ConceptMastery) => {
    if (!mastery || !mastery.is_unlocked) return 'Locked'
    if (mastery.is_mastered || mastery.P_L >= 0.90) return 'Mastered'
    if (mastery.P_L >= 0.40) return 'Learning'
    return 'Unlocked'
  }

  const handleViewMistakes = async (conceptId: string) => {
    setSelectedConcept(conceptId)
    setLoadingMistakes(true)
    try {
      const mistakes = await getConceptMistakes(TEMP_USER_ID, subjectId, conceptId, 20)
      setMistakeHistory(mistakes)
    } catch (err) {
      console.error('Failed to load mistakes:', err)
      setMistakeHistory(null)
    } finally {
      setLoadingMistakes(false)
    }
  }

  const closeMistakeModal = () => {
    setSelectedConcept(null)
    setMistakeHistory(null)
  }

  useLayoutEffect(() => {
    if (!knowledgeGraph || !Array.isArray(knowledgeGraph.nodes)) {
      setConnections([])
      return
    }

    let frameId: number | null = null

    const updateConnections = () => {
      const container = containerRef.current
      if (!container) return

      const containerRect = container.getBoundingClientRect()
      const nextConnections: Array<{ x1: number; y1: number; x2: number; y2: number }> = []

      knowledgeGraph.nodes.forEach(node => {
        const nodeId = getNodeId(node)
        if (!nodeId) return
        const childEl = nodeRefs.current[nodeId]
        if (!childEl) return

        const childRect = childEl.getBoundingClientRect()
        const x2 = childRect.left + childRect.width / 2 - containerRect.left
        const y2 = childRect.top - containerRect.top

        const prerequisites = getNodePrereqs(node)
        prerequisites.forEach(prereqId => {
          const parentEl = nodeRefs.current[prereqId]
          if (!parentEl) return

          const parentRect = parentEl.getBoundingClientRect()
          const x1 = parentRect.left + parentRect.width / 2 - containerRect.left
          const y1 = parentRect.bottom - containerRect.top

          nextConnections.push({ x1, y1, x2, y2 })
        })
      })

      setConnections(nextConnections)
    }

    const scheduleUpdate = () => {
      if (frameId !== null) {
        cancelAnimationFrame(frameId)
      }
      frameId = requestAnimationFrame(updateConnections)
    }

    scheduleUpdate()
    window.addEventListener('resize', scheduleUpdate)
    const resizeObserver = new ResizeObserver(scheduleUpdate)
    if (containerRef.current) {
      resizeObserver.observe(containerRef.current)
    }

    return () => {
      window.removeEventListener('resize', scheduleUpdate)
      resizeObserver.disconnect()
      if (frameId !== null) {
        cancelAnimationFrame(frameId)
      }
    }
  }, [knowledgeGraph, masteryData])

  if (loading) {
    return (
      <div className="paper min-h-screen flex items-center justify-center">
        <div className="text-center">
          <div className="animate-spin rounded-full h-16 w-16 border-b-4 border-blue-600 mx-auto mb-4"></div>
          <p className="text-gray-600 text-lg">Loading your progress...</p>
        </div>
      </div>
    )
  }

  if (error || !knowledgeGraph) {
    return (
      <div className="paper min-h-screen flex items-center justify-center">
        <div className="text-center">
          <div className="bg-red-100 text-red-700 px-6 py-4 rounded-lg mb-4">
            <p className="font-semibold">Error loading progress</p>
            <p className="text-sm">{error || 'Knowledge graph not found'}</p>
          </div>
          <Link href={`/dashboard/${folderId}`} className="text-blue-600 hover:text-blue-700 font-semibold">
            ← Back to {folderName}
          </Link>
        </div>
      </div>
    )
  }

  // Sort nodes by depth for top-to-bottom display
  const sortedNodes = Array.isArray(knowledgeGraph.nodes)
    ? [...knowledgeGraph.nodes].sort((a, b) => a.depth - b.depth)
    : []

  // Group nodes by depth level
  const nodesByDepth: { [depth: number]: typeof sortedNodes } = {}
  sortedNodes.forEach(node => {
    if (!nodesByDepth[node.depth]) {
      nodesByDepth[node.depth] = []
    }
    nodesByDepth[node.depth].push(node)
  })

  return (
    <div className="paper min-h-screen">
      {/* Header */}
      <div className="relative z-10 bg-white border-b border-gray-200" style={{ boxShadow: "0 2px 8px rgba(0,0,0,0.04)" }}>
        <div className="w-full px-4 sm:px-6 lg:px-8 py-6">
          <div className="flex items-center justify-between mb-4">
            <Link
              href={`/dashboard/${folderId}`}
              className="inline-flex items-center text-blue-600 hover:text-blue-700 font-semibold transition-all duration-200 hover:gap-3 gap-2 group"
            >
              <svg className="w-5 h-5 transition-transform duration-200 group-hover:-translate-x-1" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15 19l-7-7 7-7" />
              </svg>
              Back to {folderName}
            </Link>
          </div>

          <div className="flex items-center gap-3">
            <div className="p-3 rounded-xl bg-gradient-to-br from-purple-50 to-purple-100">
              <svg className="w-10 h-10 text-purple-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 19v-6a2 2 0 00-2-2H5a2 2 0 00-2 2v6a2 2 0 002 2h2a2 2 0 002-2zm0 0V9a2 2 0 012-2h2a2 2 0 012 2v10m-6 0a2 2 0 002 2h2a2 2 0 002-2m0 0V5a2 2 0 012-2h2a2 2 0 012 2v14a2 2 0 01-2 2h-2a2 2 0 01-2-2z" />
              </svg>
            </div>
            <div>
              <h1 className="text-3xl md:text-4xl font-bold text-gray-900">
                {knowledgeGraph.name}
              </h1>
              <p className="text-sm md:text-base text-gray-600">
                {knowledgeGraph.description}
              </p>
            </div>
          </div>

          {/* Progress Summary */}
          <div className="mt-6 grid grid-cols-2 md:grid-cols-4 gap-4">
            <div className="bg-white/80 backdrop-blur-sm rounded-xl p-4 border border-gray-200">
              <p className="text-xs text-gray-500 font-semibold uppercase tracking-wide">Total Concepts</p>
              <p className="text-2xl font-bold text-gray-900 mt-1">{knowledgeGraph.nodes.length}</p>
            </div>
            <div className="bg-white/80 backdrop-blur-sm rounded-xl p-4 border border-gray-200">
              <p className="text-xs text-gray-500 font-semibold uppercase tracking-wide">Problems Solved</p>
              <p className="text-2xl font-bold text-purple-600 mt-1">
                {progressSummary?.total_solved_questions || 0}
              </p>
            </div>
            <div className="bg-white/80 backdrop-blur-sm rounded-xl p-4 border border-gray-200">
              <p className="text-xs text-gray-500 font-semibold uppercase tracking-wide">Unlocked</p>
              <p className="text-2xl font-bold text-blue-600 mt-1">
                {masteryData.filter(m => m.is_unlocked).length}
              </p>
            </div>
            <div className="bg-white/80 backdrop-blur-sm rounded-xl p-4 border border-gray-200">
              <p className="text-xs text-gray-500 font-semibold uppercase tracking-wide">Learning</p>
              <p className="text-2xl font-bold text-yellow-600 mt-1">
                {masteryData.filter(m => m.is_unlocked && m.P_L >= 0.40 && m.P_L < 0.90).length}
              </p>
            </div>
            <div className="bg-white/80 backdrop-blur-sm rounded-xl p-4 border border-gray-200">
              <p className="text-xs text-gray-500 font-semibold uppercase tracking-wide">Mastered</p>
              <p className="text-2xl font-bold text-green-600 mt-1">
                {masteryData.filter(m => m.is_mastered || m.P_L >= 0.90).length}
              </p>
            </div>
          </div>
        </div>
      </div>

      {/* Knowledge Graph Visualization */}
      <div className="relative z-10 w-full px-4 sm:px-6 lg:px-8 py-8">
        <div className="max-w-4xl mx-auto">
          {/* Legend */}
          <div className="mb-8 bg-white/80 backdrop-blur-sm rounded-xl p-5 border border-gray-200">
            <p className="text-sm font-semibold text-gray-700 mb-3">Progress Legend:</p>
            <div className="flex flex-wrap gap-4">
              <div className="flex items-center gap-2">
                <div className="w-5 h-5 rounded-lg bg-gradient-to-br from-gray-50 to-gray-100 border border-gray-200"></div>
                <span className="text-sm text-gray-700">Locked</span>
              </div>
              <div className="flex items-center gap-2">
                <div className="w-5 h-5 rounded-lg bg-gradient-to-br from-blue-50 to-blue-100 border border-blue-200"></div>
                <span className="text-sm text-gray-700">Starting (&lt;40%)</span>
              </div>
              <div className="flex items-center gap-2">
                <div className="w-5 h-5 rounded-lg bg-gradient-to-br from-yellow-50 to-yellow-100 border border-yellow-200"></div>
                <span className="text-sm text-gray-700">Learning (40-90%)</span>
              </div>
              <div className="flex items-center gap-2">
                <div className="w-5 h-5 rounded-lg bg-gradient-to-br from-green-50 to-green-100 border border-green-200"></div>
                <span className="text-sm text-gray-700">Mastered (≥90%)</span>
              </div>
            </div>
          </div>

          {/* Tree Visualization */}
          <div className="space-y-0 relative" ref={containerRef}>
            {/* Connection lines (node-to-node) */}
            <svg className="absolute inset-0 w-full h-full pointer-events-none" style={{ zIndex: 0 }}>
              <defs>
                <marker id="arrowhead" markerWidth="10" markerHeight="7" refX="9" refY="3.5" orient="auto">
                  <polygon points="0 0, 10 3.5, 0 7" fill="#9CA3AF" />
                </marker>
              </defs>
              {connections.map((line, index) => (
                <line
                  key={`${line.x1}-${line.y1}-${line.x2}-${line.y2}-${index}`}
                  x1={line.x1}
                  y1={line.y1}
                  x2={line.x2}
                  y2={line.y2}
                  stroke="#9CA3AF"
                  strokeWidth="2.5"
                  markerEnd="url(#arrowhead)"
                />
              ))}
            </svg>
            {Object.keys(nodesByDepth).sort((a, b) => Number(a) - Number(b)).map((depthStr, levelIndex) => {
              const depth = Number(depthStr)
              const nodesAtDepth = nodesByDepth[depth]

              return (
                <div key={depth} className={levelIndex === Object.keys(nodesByDepth).length - 1 ? '' : 'mb-20'}>
                  {/* Nodes at this depth */}
                  <div className="grid gap-8 relative" style={{
                    gridTemplateColumns: `repeat(${nodesAtDepth.length}, minmax(0, 1fr))`,
                    zIndex: 1
                  }}>
                    {nodesAtDepth.map((node) => {
                      const nodeId = getNodeId(node)
                      const mastery = nodeId ? getMasteryForConcept(nodeId) : undefined
                      const colors = getConceptColor(mastery)
                      const label = getMasteryLabel(mastery)
                      const percentage = mastery ? Math.round(mastery.P_L * 100) : 0

                      return (
                        <div
                          key={nodeId}
                          className="relative flex flex-col items-center animate-fade-in group"
                          ref={(el) => {
                            if (nodeId) {
                              nodeRefs.current[nodeId] = el
                            }
                          }}
                        >
                          {/* Hover tooltip */}
                          {node.description && (
                            <div
                              className="pointer-events-none absolute -top-2 left-1/2 z-20 w-64 -translate-x-1/2 -translate-y-full rounded-lg border border-gray-200 bg-white px-3 py-2 text-xs text-gray-700 opacity-0 shadow-lg transition-opacity duration-150 group-hover:opacity-100"
                              role="tooltip"
                            >
                              {node.description}
                            </div>
                          )}
                          {/* Concept Card */}
                          <div className={`w-full max-w-xs bg-gradient-to-br ${colors.bg} border ${colors.border} rounded-xl p-6 transition-all duration-300 hover:scale-105`}>
                            {/* Node Header */}
                            <div className="flex items-start justify-between mb-3">
                              <h3 className={`font-bold text-lg ${colors.text} leading-tight`}>
                              {node.name}
                              </h3>
                              <span className={`text-xs font-semibold px-3 py-1 rounded-full ${colors.badge}`}>
                                {label}
                              </span>
                            </div>

                            {/* Progress Bar */}
                            {mastery && mastery.is_unlocked && (
                              <div className="space-y-2">
                                <div className="flex justify-between items-center">
                                  <span className="text-xs font-semibold text-gray-600">Mastery</span>
                                  <span className="text-xs font-bold text-gray-800">{percentage}%</span>
                                </div>
                                <div className="w-full bg-white/70 rounded-full h-3 overflow-hidden border border-gray-200">
                                  <div
                                    className={`h-full ${colors.progress} transition-all duration-500 rounded-full`}
                                    style={{ width: `${percentage}%` }}
                                  ></div>
                                </div>
                                
                                {/* Observations and Accuracy */}
                                <div className="mt-3 pt-3 border-t border-gray-200/50 space-y-1">
                                  <div className="flex justify-between items-center">
                                    <span className="text-xs text-gray-600">Questions Practiced</span>
                                    <span className="text-xs font-semibold text-gray-800">{mastery.observations}</span>
                                  </div>
                                  {mastery.observations > 0 && (
                                    <div className="flex justify-between items-center">
                                      <span className="text-xs text-gray-600">Accuracy</span>
                                      <span className="text-xs font-semibold text-gray-800">
                                        {mastery.correct_count}/{mastery.observations} ({Math.round((mastery.correct_count / mastery.observations) * 100)}%)
                                      </span>
                                    </div>
                                  )}
                                  
                                  {/* View Mistakes Button */}
                                  {mastery.observations > 0 && mastery.observations > mastery.correct_count && (
                                    <button
                                      onClick={() => handleViewMistakes(nodeId)}
                                      className="w-full mt-2 px-3 py-1.5 text-xs font-medium text-red-700 bg-red-50 hover:bg-red-100 rounded-lg transition-colors"
                                    >
                                      View Mistakes ({mastery.observations - mastery.correct_count})
                                    </button>
                                  )}
                                </div>
                              </div>
                            )}
                            
                            {/* BKT Parameters - Always show if mastery data exists */}
                            {mastery && mastery.P_L !== undefined && (
                              <div className="mt-3 pt-3 border-t border-gray-200/50">
                                <p className="text-xs font-semibold text-gray-700 mb-2">BKT Parameters</p>
                                <div className="grid grid-cols-2 gap-x-3 gap-y-2">
                                  <div className="flex justify-between">
                                    <span className="text-xs text-gray-500">P(L)</span>
                                    <span className="text-xs font-mono font-semibold text-blue-600">{(mastery.P_L || 0).toFixed(3)}</span>
                                  </div>
                                  <div className="flex justify-between">
                                    <span className="text-xs text-gray-500">P(T)</span>
                                    <span className="text-xs font-mono font-semibold text-purple-600">{(mastery.P_T || 0).toFixed(3)}</span>
                                  </div>
                                  <div className="flex justify-between">
                                    <span className="text-xs text-gray-500">P(G)</span>
                                    <span className="text-xs font-mono font-semibold text-orange-600">{(mastery.P_G || 0).toFixed(3)}</span>
                                  </div>
                                  <div className="flex justify-between">
                                    <span className="text-xs text-gray-500">P(S)</span>
                                    <span className="text-xs font-mono font-semibold text-red-600">{(mastery.P_S || 0).toFixed(3)}</span>
                                  </div>
                                </div>
                                <div className="mt-2 text-xs text-gray-500">
                                  Status: {mastery.mastery_status} | Unlocked: {mastery.is_unlocked ? 'Yes' : 'No'}
                                </div>
                              </div>
                            )}

                            {/* Locked Icon */}
                            {(!mastery || !mastery.is_unlocked) && (
                              <div className="flex items-center justify-center mt-2">
                                <svg className="w-8 h-8 text-gray-600" fill="currentColor" viewBox="0 0 20 20">
                                  <path fillRule="evenodd" d="M5 9V7a5 5 0 0110 0v2a2 2 0 012 2v5a2 2 0 01-2 2H5a2 2 0 01-2-2v-5a2 2 0 012-2zm8-2v2H7V7a3 3 0 016 0z" clipRule="evenodd" />
                                </svg>
                              </div>
                            )}
                          </div>

                          {/* Prerequisites Info */}
                          {getNodePrereqs(node).length > 0 && (
                            <p className="text-xs text-gray-500 mt-2 text-center">
                              Requires: {getNodePrereqs(node).map(prereqId => {
                                const prereqNode = knowledgeGraph.nodes.find(n => getNodeId(n) === prereqId)
                                return prereqNode?.name || prereqId
                              }).join(', ')}
                            </p>
                          )}
                        </div>
                      )
                    })}
                  </div>
                </div>
              )
            })}
          </div>
        </div>
      </div>

      {/* Mistake History Modal */}
      {selectedConcept && (
        <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/50" onClick={closeMistakeModal}>
          <div className="bg-white rounded-2xl shadow-2xl max-w-2xl w-full max-h-[80vh] overflow-hidden" onClick={(e) => e.stopPropagation()}>
            {/* Modal Header */}
            <div className="bg-gradient-to-r from-red-50 to-red-100 px-6 py-4 border-b border-red-200">
              <div className="flex items-center justify-between">
                <h2 className="text-xl font-bold text-red-900">Mistake History</h2>
                <button
                  onClick={closeMistakeModal}
                  className="text-red-600 hover:text-red-800 transition-colors"
                >
                  <svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
                  </svg>
                </button>
              </div>
              {knowledgeGraph?.nodes && (
                <p className="text-sm text-red-700 mt-1">
                  {Array.isArray(knowledgeGraph.nodes) 
                    ? knowledgeGraph.nodes.find((n: any) => (n.id ?? n.concept_id) === selectedConcept)?.name 
                    : Object.values(knowledgeGraph.nodes).find((n: any) => (n.id ?? n.concept_id) === selectedConcept)?.name
                  }
                </p>
              )}
            </div>

            {/* Modal Content */}
            <div className="p-6 overflow-y-auto max-h-[calc(80vh-120px)]">
              {loadingMistakes ? (
                <div className="flex items-center justify-center py-12">
                  <div className="animate-spin rounded-full h-12 w-12 border-b-4 border-red-600"></div>
                </div>
              ) : mistakeHistory ? (
                <div className="space-y-4">
                  {/* Summary */}
                  <div className="bg-red-50 rounded-lg p-4 border border-red-200">
                    <div className="grid grid-cols-3 gap-4 text-center">
                      <div>
                        <p className="text-xs text-red-600 font-semibold">Total Attempts</p>
                        <p className="text-2xl font-bold text-red-900">{mistakeHistory.total_attempts}</p>
                      </div>
                      <div>
                        <p className="text-xs text-red-600 font-semibold">Mistakes</p>
                        <p className="text-2xl font-bold text-red-900">{mistakeHistory.mistakes.length}</p>
                      </div>
                      <div>
                        <p className="text-xs text-red-600 font-semibold">Accuracy</p>
                        <p className="text-2xl font-bold text-red-900">{mistakeHistory.accuracy_percentage}%</p>
                      </div>
                    </div>
                  </div>

                  {/* Mistake List */}
                  {mistakeHistory.mistakes.length > 0 ? (
                    <div className="space-y-3">
                      <h3 className="font-semibold text-gray-900">Recent Mistakes</h3>
                      {mistakeHistory.mistakes.map((mistake, idx) => (
                        <div key={idx} className="bg-gray-50 rounded-lg p-4 border border-gray-200">
                          <div className="flex justify-between items-start mb-2">
                            <span className="text-xs text-gray-500">
                              {new Date(mistake.timestamp).toLocaleString()}
                            </span>
                            <span className={`text-xs font-semibold px-2 py-1 rounded ${
                              mistake.mastery_change < 0 ? 'bg-red-100 text-red-700' : 'bg-yellow-100 text-yellow-700'
                            }`}>
                              {mistake.mastery_change > 0 ? '+' : ''}{(mistake.mastery_change * 100).toFixed(1)}% mastery
                            </span>
                          </div>
                          <div className="grid grid-cols-2 gap-2 text-xs">
                            <div>
                              <span className="text-gray-600">P(L) Before:</span>
                              <span className="ml-1 font-semibold">{(mistake.P_L_before * 100).toFixed(1)}%</span>
                            </div>
                            <div>
                              <span className="text-gray-600">P(L) After:</span>
                              <span className="ml-1 font-semibold">{(mistake.P_L_after * 100).toFixed(1)}%</span>
                            </div>
                          </div>
                        </div>
                      ))}
                    </div>
                  ) : (
                    <p className="text-center text-gray-500 py-8">No mistakes yet - great job!</p>
                  )}
                </div>
              ) : (
                <p className="text-center text-gray-500 py-8">Failed to load mistake history</p>
              )}
            </div>
          </div>
        </div>
      )}

      <style jsx>{`
        @keyframes fade-in {
          from {
            opacity: 0;
            transform: translateY(10px);
          }
          to {
            opacity: 1;
            transform: translateY(0);
          }
        }

        .animate-fade-in {
          animation: fade-in 0.5s ease-out;
        }
      `}</style>
    </div>
  )
}
