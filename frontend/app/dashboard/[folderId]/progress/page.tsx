'use client'

import { useState, useEffect } from 'react'
import Link from 'next/link'
import { useParams } from 'next/navigation'
import { getKnowledgeGraph, getUserMastery, type KnowledgeGraph, type ConceptMastery } from '@/lib/api'

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

export default function ProgressPage() {
  const params = useParams()
  const folderId = params.folderId as string
  const subjectId = FOLDER_TO_SUBJECT[folderId] || folderId

  const [knowledgeGraph, setKnowledgeGraph] = useState<KnowledgeGraph | null>(null)
  const [masteryData, setMasteryData] = useState<ConceptMastery[]>([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)

  const folderName = FOLDER_NAMES[folderId] || 'Unknown Subject'

  useEffect(() => {
    async function loadProgressData() {
      try {
        setLoading(true)
        setError(null)

        // Fetch knowledge graph
        const graph = await getKnowledgeGraph(subjectId)
        setKnowledgeGraph(graph)

        // Try to fetch user mastery (will fail if not initialized yet)
        try {
          const mastery = await getUserMastery('dev_user_123', subjectId)
          setMasteryData(mastery.concepts)
        } catch (err) {
          // No mastery data yet - show all locked except root concepts
          const initialMastery: ConceptMastery[] = graph.nodes.map(node => ({
            concept_id: node.id,
            P_L: node.bkt_params.P_L0,
            is_unlocked: graph.root_concepts.includes(node.id),
            is_mastered: false,
          }))
          setMasteryData(initialMastery)
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

  const getConceptColor = (mastery?: ConceptMastery) => {
    if (!mastery || !mastery.is_unlocked) {
      return {
        bg: 'from-gray-300 to-gray-400',
        border: 'border-gray-500',
        text: 'text-gray-700',
        progress: 'bg-gray-400'
      }
    }
    if (mastery.is_mastered || mastery.P_L >= 0.90) {
      return {
        bg: 'from-green-400 to-green-500',
        border: 'border-green-600',
        text: 'text-green-900',
        progress: 'bg-green-600'
      }
    }
    if (mastery.P_L >= 0.40) {
      return {
        bg: 'from-yellow-300 to-yellow-400',
        border: 'border-yellow-600',
        text: 'text-yellow-900',
        progress: 'bg-yellow-600'
      }
    }
    return {
      bg: 'from-red-300 to-red-400',
      border: 'border-red-600',
      text: 'text-red-900',
      progress: 'bg-red-600'
    }
  }

  const getMasteryLabel = (mastery?: ConceptMastery) => {
    if (!mastery || !mastery.is_unlocked) return 'Locked'
    if (mastery.is_mastered || mastery.P_L >= 0.90) return 'Mastered'
    if (mastery.P_L >= 0.40) return 'Learning'
    return 'Unlocked'
  }

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
  const sortedNodes = [...knowledgeGraph.nodes].sort((a, b) => a.depth - b.depth)

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
            <div className="bg-white rounded-lg p-4 border border-gray-200 shadow-sm">
              <p className="text-xs text-gray-500 font-semibold uppercase">Total Concepts</p>
              <p className="text-2xl font-bold text-gray-900">{knowledgeGraph.nodes.length}</p>
            </div>
            <div className="bg-white rounded-lg p-4 border border-gray-200 shadow-sm">
              <p className="text-xs text-gray-500 font-semibold uppercase">Unlocked</p>
              <p className="text-2xl font-bold text-blue-600">
                {masteryData.filter(m => m.is_unlocked).length}
              </p>
            </div>
            <div className="bg-white rounded-lg p-4 border border-gray-200 shadow-sm">
              <p className="text-xs text-gray-500 font-semibold uppercase">Learning</p>
              <p className="text-2xl font-bold text-yellow-600">
                {masteryData.filter(m => m.is_unlocked && m.P_L >= 0.40 && m.P_L < 0.90).length}
              </p>
            </div>
            <div className="bg-white rounded-lg p-4 border border-gray-200 shadow-sm">
              <p className="text-xs text-gray-500 font-semibold uppercase">Mastered</p>
              <p className="text-2xl font-bold text-green-600">
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
          <div className="mb-8 bg-white rounded-lg p-4 border border-gray-200 shadow-sm">
            <p className="text-sm font-semibold text-gray-700 mb-3">Progress Legend:</p>
            <div className="flex flex-wrap gap-4">
              <div className="flex items-center gap-2">
                <div className="w-4 h-4 rounded bg-gradient-to-br from-gray-300 to-gray-400 border-2 border-gray-500"></div>
                <span className="text-sm text-gray-700">Locked</span>
              </div>
              <div className="flex items-center gap-2">
                <div className="w-4 h-4 rounded bg-gradient-to-br from-red-300 to-red-400 border-2 border-red-600"></div>
                <span className="text-sm text-gray-700">Unlocked (&lt;40%)</span>
              </div>
              <div className="flex items-center gap-2">
                <div className="w-4 h-4 rounded bg-gradient-to-br from-yellow-300 to-yellow-400 border-2 border-yellow-600"></div>
                <span className="text-sm text-gray-700">Learning (40-90%)</span>
              </div>
              <div className="flex items-center gap-2">
                <div className="w-4 h-4 rounded bg-gradient-to-br from-green-400 to-green-500 border-2 border-green-600"></div>
                <span className="text-sm text-gray-700">Mastered (≥90%)</span>
              </div>
            </div>
          </div>

          {/* Tree Visualization */}
          <div className="space-y-8">
            {Object.keys(nodesByDepth).sort((a, b) => Number(a) - Number(b)).map((depthStr, levelIndex) => {
              const depth = Number(depthStr)
              const nodesAtDepth = nodesByDepth[depth]

              return (
                <div key={depth}>
                  {/* Connecting Lines (if not first level) */}
                  {levelIndex > 0 && (
                    <div className="flex justify-center mb-4">
                      <div className="w-0.5 h-8 bg-gray-300"></div>
                    </div>
                  )}

                  {/* Nodes at this depth */}
                  <div className="grid gap-6" style={{
                    gridTemplateColumns: `repeat(${nodesAtDepth.length}, minmax(0, 1fr))`
                  }}>
                    {nodesAtDepth.map((node) => {
                      const mastery = getMasteryForConcept(node.id)
                      const colors = getConceptColor(mastery)
                      const label = getMasteryLabel(mastery)
                      const percentage = mastery ? Math.round(mastery.P_L * 100) : 0

                      return (
                        <div
                          key={node.id}
                          className="relative flex flex-col items-center animate-fade-in"
                        >
                          {/* Concept Card */}
                          <div className={`w-full max-w-xs bg-gradient-to-br ${colors.bg} border-2 ${colors.border} rounded-xl p-5 shadow-lg transition-all duration-300 hover:scale-105`}>
                            {/* Node Header */}
                            <div className="flex items-start justify-between mb-3">
                              <h3 className={`font-bold text-lg ${colors.text} leading-tight`}>
                                {node.name}
                              </h3>
                              <span className={`text-xs font-bold px-2 py-1 rounded ${colors.text} bg-white/50`}>
                                {label}
                              </span>
                            </div>

                            {/* Description */}
                            <p className="text-sm text-gray-800 mb-4">
                              {node.description}
                            </p>

                            {/* Progress Bar */}
                            {mastery && mastery.is_unlocked && (
                              <div className="space-y-2">
                                <div className="flex justify-between items-center">
                                  <span className="text-xs font-semibold text-gray-700">Mastery</span>
                                  <span className="text-xs font-bold text-gray-900">{percentage}%</span>
                                </div>
                                <div className="w-full bg-white/70 rounded-full h-3 overflow-hidden border border-gray-400">
                                  <div
                                    className={`h-full ${colors.progress} transition-all duration-500 rounded-full`}
                                    style={{ width: `${percentage}%` }}
                                  ></div>
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
                          {node.prerequisites.length > 0 && (
                            <p className="text-xs text-gray-500 mt-2 text-center">
                              Requires: {node.prerequisites.map(prereqId => {
                                const prereqNode = knowledgeGraph.nodes.find(n => n.id === prereqId)
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
