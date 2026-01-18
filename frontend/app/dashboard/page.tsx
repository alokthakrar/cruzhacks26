'use client'

import { useState } from 'react'
import Link from 'next/link'
import { uploadPDF } from '@/lib/api'

// Type definitions
type Folder = {
  id: string
  name: string
  created_at: string
  pdfCount: number
  color: string
}

type PDF = {
  id: string
  name: string
  folderId: string
  created_at: string
  thumbnail: string
}

// Available folder colors
const FOLDER_COLORS = [
  { name: 'Blue', bg: 'from-blue-50 to-blue-100', icon: 'text-blue-500', badge: 'bg-blue-600' },
  { name: 'Purple', bg: 'from-purple-50 to-purple-100', icon: 'text-purple-500', badge: 'bg-purple-600' },
  { name: 'Green', bg: 'from-green-50 to-green-100', icon: 'text-green-500', badge: 'bg-green-600' },
  { name: 'Orange', bg: 'from-orange-50 to-orange-100', icon: 'text-orange-500', badge: 'bg-orange-600' },
  { name: 'Pink', bg: 'from-pink-50 to-pink-100', icon: 'text-pink-500', badge: 'bg-pink-600' },
  { name: 'Indigo', bg: 'from-indigo-50 to-indigo-100', icon: 'text-indigo-500', badge: 'bg-indigo-600' },
]

// Fake data - pretending these came from the backend
const FAKE_FOLDERS: Folder[] = [
  {
    id: '1',
    name: 'Calculus',
    created_at: '2026-01-15T10:30:00',
    pdfCount: 3,
    color: 'Blue',
  },
  {
    id: '2',
    name: 'Physics',
    created_at: '2026-01-14T14:20:00',
    pdfCount: 2,
    color: 'Purple',
  },
]

export default function DashboardPage() {
  const [folders, setFolders] = useState<Folder[]>(FAKE_FOLDERS)
  const [isDragging, setIsDragging] = useState(false)
  const [showCreateFolder, setShowCreateFolder] = useState(false)
  const [newFolderName, setNewFolderName] = useState('')
  const [selectedFolder, setSelectedFolder] = useState<string>('')
  const [selectedColor, setSelectedColor] = useState('Blue')
  const [isUploading, setIsUploading] = useState(false)
  const [uploadError, setUploadError] = useState<string | null>(null)

  // Handle creating a new folder
  const handleCreateFolder = () => {
    if (!newFolderName.trim()) return

    const newFolder: Folder = {
      id: Date.now().toString(),
      name: newFolderName,
      created_at: new Date().toISOString(),
      pdfCount: 0,
      color: selectedColor,
    }

    setFolders([newFolder, ...folders])
    setNewFolderName('')
    setSelectedColor('Blue')
    setShowCreateFolder(false)
  }

  // Handle file upload - calls real API or uses fake data
  const handleFileUpload = async (file: File, folderId: string) => {
    setIsUploading(true)
    setUploadError(null)

    try {
      // Call API (will use fake data if USE_FAKE_DATA = true)
      const result = await uploadPDF(file, folderId)

      console.log('Upload result:', result)

      // Update the folder's PDF count based on API response
      setFolders(folders.map(folder =>
        folder.id === folderId
          ? { ...folder, pdfCount: folder.pdfCount + result.question_count }
          : folder
      ))

      // Reset selection
      setSelectedFolder('')

      // Show success message
      alert(`Success! Extracted ${result.question_count} questions from ${result.total_pages} pages.`)
    } catch (error) {
      console.error('Upload error:', error)
      setUploadError(error instanceof Error ? error.message : 'Upload failed')
      alert(`Upload failed: ${error instanceof Error ? error.message : 'Unknown error'}`)
    } finally {
      setIsUploading(false)
    }
  }

  // Handle drag and drop
  const handleDrop = (e: React.DragEvent) => {
    e.preventDefault()
    setIsDragging(false)

    const files = Array.from(e.dataTransfer.files)
    const pdfFile = files.find(file => file.type === 'application/pdf')

    if (pdfFile) {
      if (selectedFolder) {
        handleFileUpload(pdfFile, selectedFolder)
      } else {
        alert('Please select a folder first')
      }
    } else {
      alert('Please upload a PDF file')
    }
  }

  const handleDragOver = (e: React.DragEvent) => {
    e.preventDefault()
    setIsDragging(true)
  }

  const handleDragLeave = () => {
    setIsDragging(false)
  }

  // Handle click to upload
  const handleFileInput = (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0]
    if (file && selectedFolder) {
      handleFileUpload(file, selectedFolder)
    } else if (file && !selectedFolder) {
      alert('Please select a folder first')
    }
  }

  // Format date nicely
  const formatDate = (dateString: string) => {
    const date = new Date(dateString)
    return date.toLocaleDateString('en-US', {
      month: 'short',
      day: 'numeric',
      year: 'numeric'
    })
  }

  // Get color classes for a folder
  const getColorClasses = (colorName: string) => {
    return FOLDER_COLORS.find(c => c.name === colorName) || FOLDER_COLORS[0]
  }

  return (
    <div className="min-h-screen bg-[#fefdfb] relative">
      {/* Graph paper texture overlay */}
      <div
        className="absolute inset-0 opacity-[0.25] pointer-events-none"
        style={{
          backgroundImage: `
            repeating-linear-gradient(
              0deg,
              transparent,
              transparent 19px,
              #9ca3af 19px,
              #9ca3af 20px
            ),
            repeating-linear-gradient(
              90deg,
              transparent,
              transparent 19px,
              #9ca3af 19px,
              #9ca3af 20px
            )
          `
        }}
      />

      {/* Main content */}
      <div className="relative z-10 w-full px-4 sm:px-6 lg:px-8 py-12">
        {/* Header */}
        <div className="mb-8 flex justify-between items-center">
          <div>
            <h1 className="text-4xl font-bold text-gray-900 mb-2">
              Welcome back!
            </h1>
            <p className="text-gray-600">
              Organize your problem sets by subject
            </p>
          </div>
          <button
            onClick={() => setShowCreateFolder(true)}
            className="bg-blue-600 hover:bg-blue-700 text-white font-semibold py-3 px-6 rounded-lg transition-all duration-200 flex items-center gap-2 hover:scale-105 hover:shadow-lg active:scale-95"
          >
            <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 4v16m8-8H4" />
            </svg>
            Create New Folder
          </button>
        </div>

        {/* Create Folder Modal */}
        {showCreateFolder && (
          <div className="fixed inset-0 backdrop-blur-sm bg-white/30 flex items-center justify-center z-50 animate-fade-in">
            <div className="bg-white/90 backdrop-blur-md rounded-2xl p-8 max-w-md w-full mx-4 shadow-2xl border border-gray-200/50 animate-scale-in">
              <h2 className="text-2xl font-bold text-gray-900 mb-4">Create New Folder</h2>
              <input
                type="text"
                value={newFolderName}
                onChange={(e) => setNewFolderName(e.target.value)}
                placeholder="Enter folder name (e.g., Calculus)"
                className="w-full px-4 py-2 border border-gray-300 rounded-lg mb-4 focus:outline-none focus:ring-2 focus:ring-blue-500 transition-all"
                onKeyPress={(e) => e.key === 'Enter' && handleCreateFolder()}
                autoFocus
              />

              {/* Color picker */}
              <div className="mb-6">
                <label className="block text-sm font-semibold text-gray-700 mb-3">Choose a color:</label>
                <div className="grid grid-cols-6 gap-2">
                  {FOLDER_COLORS.map((color) => (
                    <button
                      key={color.name}
                      onClick={() => setSelectedColor(color.name)}
                      className={`h-10 rounded-lg transition-all duration-200 ${
                        selectedColor === color.name
                          ? 'ring-2 ring-offset-2 ring-gray-900 scale-110'
                          : 'hover:scale-105'
                      } bg-gradient-to-br ${color.bg}`}
                      title={color.name}
                    />
                  ))}
                </div>
              </div>

              <div className="flex gap-3">
                <button
                  onClick={handleCreateFolder}
                  className="flex-1 bg-blue-600 hover:bg-blue-700 text-white font-semibold py-2 px-4 rounded-lg transition-all duration-200 hover:scale-105 active:scale-95"
                >
                  Create
                </button>
                <button
                  onClick={() => {
                    setShowCreateFolder(false)
                    setNewFolderName('')
                    setSelectedColor('Blue')
                  }}
                  className="flex-1 bg-gray-200 hover:bg-gray-300 text-gray-800 font-semibold py-2 px-4 rounded-lg transition-all duration-200 hover:scale-105 active:scale-95"
                >
                  Cancel
                </button>
              </div>
            </div>
          </div>
        )}

        {/* Upload Area */}
        <div className="mb-12">
          <div className="mb-4">
            <label className="block text-sm font-semibold text-gray-700 mb-2">
              Select folder for upload:
            </label>
            <select
              value={selectedFolder}
              onChange={(e) => setSelectedFolder(e.target.value)}
              className="w-full md:w-64 px-4 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500 transition-all"
            >
              <option value="">Choose a folder...</option>
              {folders.map(folder => (
                <option key={folder.id} value={folder.id}>{folder.name}</option>
              ))}
            </select>
          </div>

          <div
            onDrop={handleDrop}
            onDragOver={handleDragOver}
            onDragLeave={handleDragLeave}
            className={`
              border-2 border-dashed rounded-xl p-12 text-center
              transition-all duration-300
              ${isDragging
                ? 'border-blue-500 bg-blue-50 scale-105 shadow-lg'
                : 'border-gray-300 bg-white/50 backdrop-blur-sm hover:border-gray-400 hover:shadow-md'
              }
              ${!selectedFolder ? 'cursor-not-allowed' : 'cursor-pointer'}
            `}
          >
            <input
              type="file"
              accept=".pdf"
              onChange={handleFileInput}
              className="hidden"
              id="file-upload"
              disabled={!selectedFolder}
            />
            <label htmlFor="file-upload" className={selectedFolder && !isUploading ? 'cursor-pointer' : 'cursor-not-allowed'}>
              <div className="flex flex-col items-center">
                {isUploading ? (
                  <>
                    <div className="w-16 h-16 mb-4">
                      <svg className="animate-spin h-16 w-16 text-blue-500" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24">
                        <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4"></circle>
                        <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
                      </svg>
                    </div>
                    <p className="text-xl font-semibold text-blue-600 mb-2">
                      Uploading and extracting questions...
                    </p>
                    <p className="text-sm text-gray-500">
                      This may take a moment
                    </p>
                  </>
                ) : (
                  <>
                    <svg
                      className={`w-16 h-16 mb-4 transition-all duration-300 ${
                        isDragging ? 'text-blue-500 scale-110' : 'text-gray-400'
                      }`}
                      fill="none"
                      stroke="currentColor"
                      viewBox="0 0 24 24"
                    >
                      <path
                        strokeLinecap="round"
                        strokeLinejoin="round"
                        strokeWidth={2}
                        d="M7 16a4 4 0 01-.88-7.903A5 5 0 1115.9 6L16 6a5 5 0 011 9.9M15 13l-3-3m0 0l-3 3m3-3v12"
                      />
                    </svg>
                    <p className="text-xl font-semibold text-gray-700 mb-2">
                      {selectedFolder ? 'Drop your PDF here or click to upload' : 'Select a folder first'}
                    </p>
                    <p className="text-sm text-gray-500">
                      Upload problem sets to your selected folder
                    </p>
                  </>
                )}
              </div>
            </label>
          </div>
        </div>

        {/* Folders Grid */}
        {folders.length > 0 ? (
          <>
            <h2 className="text-2xl font-bold text-gray-900 mb-6">
              Your Folders
            </h2>
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
              {folders.map((folder, index) => {
                const colorClasses = getColorClasses(folder.color)
                return (
                  <Link
                    key={folder.id}
                    href={`/dashboard/${folder.id}`}
                    className="bg-white/70 backdrop-blur-sm rounded-lg shadow-md overflow-hidden hover:shadow-2xl transition-all duration-300 border border-gray-200/50 cursor-pointer hover:-translate-y-2 group"
                    style={{
                      animation: `fadeInUp 0.5s ease-out ${index * 0.1}s both`
                    }}
                  >
                    {/* Folder Icon */}
                    <div className={`h-48 bg-gradient-to-br ${colorClasses.bg} relative flex items-center justify-center transition-all duration-300 group-hover:scale-105`}>
                      <svg
                        className={`w-32 h-32 ${colorClasses.icon} transition-all duration-300 group-hover:scale-110`}
                        fill="currentColor"
                        viewBox="0 0 20 20"
                      >
                        <path d="M2 6a2 2 0 012-2h5l2 2h5a2 2 0 012 2v6a2 2 0 01-2 2H4a2 2 0 01-2-2V6z" />
                      </svg>
                      {/* PDF count badge */}
                      <div className={`absolute top-4 right-4 ${colorClasses.badge} text-white rounded-full w-10 h-10 flex items-center justify-center font-bold transition-all duration-300 group-hover:scale-110`}>
                        {folder.pdfCount}
                      </div>
                    </div>

                    {/* Card Content */}
                    <div className="p-5">
                      <h3 className="font-bold text-lg text-gray-900 mb-2 truncate">
                        {folder.name}
                      </h3>
                      <p className="text-sm text-gray-500 mb-1">
                        {folder.pdfCount} {folder.pdfCount === 1 ? 'PDF' : 'PDFs'}
                      </p>
                      <p className="text-sm text-gray-400">
                        Created {formatDate(folder.created_at)}
                      </p>
                    </div>
                  </Link>
                )
              })}
            </div>
          </>
        ) : (
          <div className="text-center py-12 animate-fade-in">
            <p className="text-gray-500 text-lg">
              No folders yet. Create your first folder to get started!
            </p>
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

        @keyframes scale-in {
          from {
            opacity: 0;
            transform: scale(0.9);
          }
          to {
            opacity: 1;
            transform: scale(1);
          }
        }

        .animate-fade-in {
          animation: fade-in 0.3s ease-out;
        }

        .animate-scale-in {
          animation: scale-in 0.3s ease-out;
        }
      `}</style>
    </div>
  )
}
