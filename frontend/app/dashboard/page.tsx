"use client";

import { useState, useEffect } from "react";
import Link from "next/link";
import {
  uploadPDF,
  getSubjects,
  createSubject,
  getSubjectQuestions,
  Subject,
  Question,
} from "@/lib/api";

// Type definitions
type Folder = Subject & {
  pdfCount: number;
  color: string;
};

type PDF = {
  id: string;
  name: string;
  folderId: string;
  created_at: string;
  thumbnail: string;
};

// Available folder colors - built-in palette
const FOLDER_COLORS = [
  {
    name: "Blue",
    bg: "from-blue-50 to-blue-100",
    icon: "text-blue-500",
    mutedIcon: "text-blue-400",
    badge: "bg-blue-600",
  },
  {
    name: "Purple",
    bg: "from-purple-50 to-purple-100",
    icon: "text-purple-500",
    mutedIcon: "text-purple-400",
    badge: "bg-purple-600",
  },
  {
    name: "Green",
    bg: "from-green-50 to-green-100",
    icon: "text-green-500",
    mutedIcon: "text-green-400",
    badge: "bg-green-600",
  },
  {
    name: "Orange",
    bg: "from-orange-50 to-orange-100",
    icon: "text-orange-500",
    mutedIcon: "text-orange-400",
    badge: "bg-orange-600",
  },
  {
    name: "Pink",
    bg: "from-pink-50 to-pink-100",
    icon: "text-pink-500",
    mutedIcon: "text-pink-400",
    badge: "bg-pink-600",
  },
  {
    name: "Indigo",
    bg: "from-indigo-50 to-indigo-100",
    icon: "text-indigo-500",
    mutedIcon: "text-indigo-400",
    badge: "bg-indigo-600",
  },
];

// Available folder colors
const getRandomColor = () => {
  const colors = ["Blue", "Purple", "Green", "Orange", "Pink", "Indigo"];
  return colors[Math.floor(Math.random() * colors.length)];
};

export default function DashboardPage() {
  const [folders, setFolders] = useState<Folder[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [isDragging, setIsDragging] = useState(false);
  const [showCreateFolder, setShowCreateFolder] = useState(false);
  const [newFolderName, setNewFolderName] = useState("");
  const [selectedFolder, setSelectedFolder] = useState<string>("");
  const [selectedColor, setSelectedColor] = useState("Blue");
  const [isUploading, setIsUploading] = useState(false);
  const [uploadError, setUploadError] = useState<string | null>(null);
  const [showQuestionsModal, setShowQuestionsModal] = useState(false);
  const [extractedQuestions, setExtractedQuestions] = useState<Question[]>([]);
  const [uploadedPdfName, setUploadedPdfName] = useState("");

  // Load subjects from backend on mount
  useEffect(() => {
    loadSubjects();
  }, []);

  const loadSubjects = async () => {
    setIsLoading(true);
    try {
      const subjects = await getSubjects();
      // Convert subjects to folders with colors and PDF count
      const foldersWithMeta = await Promise.all(
        subjects.map(async (s) => {
          // Fetch question count for each subject
          try {
            const questionsResponse = await getSubjectQuestions(s.id, 1, 1);
            return {
              ...s,
              pdfCount: questionsResponse.total,
              color: getRandomColor(),
            };
          } catch (error) {
            console.error(`Failed to load question count for ${s.name}:`, error);
            return {
              ...s,
              pdfCount: 0,
              color: getRandomColor(),
            };
          }
        })
      );
      setFolders(foldersWithMeta);
    } catch (error) {
      console.error("Failed to load subjects:", error);
      alert("Failed to load folders. Please refresh the page.");
    } finally {
      setIsLoading(false);
    }
  };

  // Handle creating a new folder
  const handleCreateFolder = async () => {
    if (!newFolderName.trim()) return;

    try {
      const newSubject = await createSubject({ name: newFolderName });
      const newFolder: Folder = {
        ...newSubject,
        pdfCount: 0,
        color: selectedColor,
      };
      setFolders([newFolder, ...folders]);
      setNewFolderName("");
      setSelectedColor("Blue");
      setShowCreateFolder(false);
    } catch (error) {
      console.error("Failed to create folder:", error);
      alert(
        `Failed to create folder: ${error instanceof Error ? error.message : "Unknown error"}`,
      );
    }
  };

  // Handle file upload - calls real API or uses fake data
  const handleFileUpload = async (file: File, folderId: string) => {
    setIsUploading(true);
    setUploadError(null);

    try {
      // Call API (will use fake data if USE_FAKE_DATA = true)
      const result = await uploadPDF(file, folderId);

      console.log("Upload result:", result);

      // Update the folder's PDF count based on API response
      setFolders(
        folders.map((folder) =>
          folder.id === folderId
            ? { ...folder, pdfCount: folder.pdfCount + result.question_count }
            : folder,
        ),
      );

      // Fetch the extracted questions to show in modal
      const questionsResponse = await getSubjectQuestions(folderId, 1, 20);
      setExtractedQuestions(questionsResponse.questions);
      setUploadedPdfName(result.filename);
      setShowQuestionsModal(true);

      // Reset selection
      setSelectedFolder("");
    } catch (error) {
      console.error("Upload error:", error);
      setUploadError(error instanceof Error ? error.message : "Upload failed");
      alert(
        `Upload failed: ${error instanceof Error ? error.message : "Unknown error"}`,
      );
    } finally {
      setIsUploading(false);
    }
  };

  // Handle drag and drop
  const handleDrop = (e: React.DragEvent) => {
    e.preventDefault();
    setIsDragging(false);

    const files = Array.from(e.dataTransfer.files);
    const pdfFile = files.find((file) => file.type === "application/pdf");

    if (pdfFile) {
      if (selectedFolder) {
        handleFileUpload(pdfFile, selectedFolder);
      } else {
        alert("Please select a folder first");
      }
    } else {
      alert("Please upload a PDF file");
    }
  };

  const handleDragOver = (e: React.DragEvent) => {
    e.preventDefault();
    setIsDragging(true);
  };

  const handleDragLeave = () => {
    setIsDragging(false);
  };

  // Handle click to upload
  const handleFileInput = (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (file && selectedFolder) {
      handleFileUpload(file, selectedFolder);
    } else if (file && !selectedFolder) {
      alert("Please select a folder first");
    }
  };

  // Format date nicely
  const formatDate = (dateString: string) => {
    const date = new Date(dateString);
    return date.toLocaleDateString("en-US", {
      month: "short",
      day: "numeric",
      year: "numeric",
    });
  };

  // Get color classes for a folder
  const getColorClasses = (colorName: string) => {
    return FOLDER_COLORS.find((c) => c.name === colorName) || FOLDER_COLORS[0];
  };

  return (
    <div className="paper min-h-screen">
      {/* Main content */}
      <div className="relative z-10 w-full px-4 sm:px-6 lg:px-8 py-12">
        {/* Header */}
        <div className="mb-8 flex justify-between items-center">
          <div>
            <h1 className="text-4xl font-bold text-gray-900 mb-2">
              Your workspace
            </h1>
            <p className="text-gray-600">Work through problems by subject</p>
          </div>
        </div>

        {/* Create Folder Modal */}
        {showCreateFolder && (
          <div className="fixed inset-0 backdrop-blur-sm bg-white/30 flex items-center justify-center z-50 animate-fade-in">
            <div
              className="bg-white rounded-2xl p-8 max-w-md w-full mx-4 border border-gray-200 animate-scale-in"
              style={{ boxShadow: "0 12px 24px rgba(0,0,0,0.08)" }}
            >
              <h2 className="text-2xl font-bold text-gray-900 mb-4">
                Create New Folder
              </h2>
              <input
                type="text"
                value={newFolderName}
                onChange={(e) => setNewFolderName(e.target.value)}
                placeholder="Enter folder name (e.g., Calculus)"
                className="w-full px-4 py-2 border border-gray-300 rounded-lg mb-4 focus:outline-none focus:ring-2 focus:ring-blue-500 transition-all"
                onKeyPress={(e) => e.key === "Enter" && handleCreateFolder()}
                autoFocus
              />

              {/* Color picker */}
              <div className="mb-6">
                <label className="block text-sm font-semibold text-gray-700 mb-3">
                  Choose a color:
                </label>
                <div className="grid grid-cols-6 gap-2">
                  {FOLDER_COLORS.map((color) => (
                    <button
                      key={color.name}
                      onClick={() => setSelectedColor(color.name)}
                      className={`h-10 rounded-lg transition-all duration-200 ${
                        selectedColor === color.name
                          ? "ring-2 ring-offset-2 ring-gray-900 scale-110"
                          : "hover:scale-105"
                      } bg-gradient-to-br ${color.bg}`}
                      title={color.name}
                    />
                  ))}
                </div>
              </div>

              <div className="flex gap-3">
                <button
                  onClick={handleCreateFolder}
                  style={{
                    flex: 1,
                    padding: "10px 20px",
                    fontSize: 16,
                    fontWeight: 500,
                    backgroundColor: "#000",
                    color: "#fff",
                    border: "1px solid #000",
                    borderRadius: 999,
                    cursor: "pointer",
                    transition: "all 0.2s ease",
                  }}
                  onMouseEnter={(e) => {
                    e.currentTarget.style.backgroundColor =
                      "rgba(0, 0, 0, 0.8)";
                  }}
                  onMouseLeave={(e) => {
                    e.currentTarget.style.backgroundColor = "#000";
                  }}
                >
                  Create
                </button>
                <button
                  onClick={() => {
                    setShowCreateFolder(false);
                    setNewFolderName("");
                    setSelectedColor("Blue");
                  }}
                  style={{
                    flex: 1,
                    padding: "10px 20px",
                    fontSize: 16,
                    fontWeight: 500,
                    backgroundColor: "transparent",
                    color: "rgba(0, 0, 0, 0.7)",
                    border: "1px solid rgba(0, 0, 0, 0.3)",
                    borderRadius: 999,
                    cursor: "pointer",
                    transition: "all 0.2s ease",
                  }}
                  onMouseEnter={(e) => {
                    e.currentTarget.style.borderColor = "rgba(0, 0, 0, 0.5)";
                    e.currentTarget.style.backgroundColor =
                      "rgba(0, 0, 0, 0.05)";
                  }}
                  onMouseLeave={(e) => {
                    e.currentTarget.style.borderColor = "rgba(0, 0, 0, 0.3)";
                    e.currentTarget.style.backgroundColor = "transparent";
                  }}
                >
                  Cancel
                </button>
              </div>
            </div>
          </div>
        )}

        {/* Questions Preview Modal */}
        {showQuestionsModal && (
          <div className="fixed inset-0 backdrop-blur-sm bg-white/30 flex items-center justify-center z-50 p-4 animate-fade-in">
            <div className="bg-white/90 backdrop-blur-md rounded-2xl p-6 md:p-8 max-w-3xl w-full max-h-[80vh] shadow-2xl border border-gray-200/50 animate-scale-in flex flex-col">
              {/* Header */}
              <div className="flex items-center justify-between mb-6">
                <div>
                  <h2 className="text-2xl font-bold text-gray-900">
                    Questions Extracted
                  </h2>
                  <p className="text-sm text-gray-600 mt-1">
                    {uploadedPdfName} • {extractedQuestions.length}{" "}
                    {extractedQuestions.length === 1 ? "question" : "questions"}
                  </p>
                </div>
                <button
                  onClick={() => setShowQuestionsModal(false)}
                  className="text-gray-400 hover:text-gray-600 transition-colors p-2 hover:bg-gray-100 rounded-lg"
                >
                  <svg
                    className="w-6 h-6"
                    fill="none"
                    stroke="currentColor"
                    viewBox="0 0 24 24"
                  >
                    <path
                      strokeLinecap="round"
                      strokeLinejoin="round"
                      strokeWidth={2}
                      d="M6 18L18 6M6 6l12 12"
                    />
                  </svg>
                </button>
              </div>

              {/* Scrollable Questions List */}
              <div className="flex-1 overflow-y-auto pr-2 space-y-3 custom-scrollbar">
                {extractedQuestions.map((question, index) => (
                  <div
                    key={question.id}
                    className="bg-white/70 backdrop-blur-sm rounded-xl p-4 border border-gray-200 hover:shadow-lg transition-all duration-200"
                  >
                    <div className="flex items-start gap-3">
                      {/* Question Number Badge */}
                      <div className="bg-gradient-to-br from-blue-500 to-blue-600 text-white rounded-lg px-3 py-1 font-bold text-sm flex-shrink-0">
                        Q{question.question_number}
                      </div>

                      {/* Question Content */}
                      <div className="flex-1 min-w-0">
                        <p className="text-gray-800 leading-relaxed break-words">
                          {question.text_content}
                        </p>

                        {/* Metadata */}
                        <div className="flex items-center gap-3 mt-2 text-xs text-gray-500">
                          <span>Page {question.page_number}</span>
                          {question.difficulty_estimate && (
                            <>
                              <span>•</span>
                              <span
                                className={`font-semibold ${
                                  question.difficulty_estimate === "easy"
                                    ? "text-green-600"
                                    : question.difficulty_estimate === "medium"
                                      ? "text-yellow-600"
                                      : "text-red-600"
                                }`}
                              >
                                {question.difficulty_estimate.toUpperCase()}
                              </span>
                            </>
                          )}
                          {question.extraction_confidence && (
                            <>
                              <span>•</span>
                              <span>
                                Confidence:{" "}
                                {(question.extraction_confidence * 100).toFixed(
                                  0,
                                )}
                                %
                              </span>
                            </>
                          )}
                        </div>
                      </div>
                    </div>
                  </div>
                ))}
              </div>

              {/* Footer */}
              <div className="mt-6 flex gap-3">
                <button
                  onClick={() => setShowQuestionsModal(false)}
                  className="flex-1 bg-blue-600 hover:bg-blue-700 text-white font-semibold py-3 px-6 rounded-lg transition-all duration-200 hover:scale-105 active:scale-95"
                >
                  Start Working on Questions
                </button>
              </div>
            </div>
          </div>
        )}

        {/* Upload Area */}
        <div className="mb-12">
          <div className="mb-6">
            <div className="flex flex-col md:flex-row md:items-center md:justify-between gap-3 md:gap-4">
              <div className="flex-1">
                <h3 className="text-2xl font-bold text-gray-900 mb-3 md:mb-4">
                  Choose a folder to begin
                </h3>
                <select
                  value={selectedFolder}
                  onChange={(e) => setSelectedFolder(e.target.value)}
                  className="w-full px-4 py-3 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500 transition-all text-base"
                  style={{
                    borderColor: "rgba(0, 0, 0, 0.8)",
                  }}
                >
                  <option value="">Select a folder...</option>
                  {folders.map((folder) => (
                    <option key={folder.id} value={folder.id}>
                      {folder.name}
                    </option>
                  ))}
                </select>
              </div>
              <button
                onClick={() => setShowCreateFolder(true)}
                style={{
                  padding: "10px 20px",
                  fontSize: 16,
                  fontWeight: 500,
                  backgroundColor: "transparent",
                  color: "rgba(0, 0, 0, 0.7)",
                  border: "1px solid rgba(0, 0, 0, 0.8)",
                  borderRadius: 999,
                  cursor: "pointer",
                  transition: "all 0.2s ease",
                  whiteSpace: "nowrap",
                  marginTop: "50px",
                }}
                onMouseEnter={(e) => {
                  e.currentTarget.style.borderColor = "rgba(0, 0, 0, 0.9)";
                  e.currentTarget.style.backgroundColor = "rgba(0, 0, 0, 0.08)";
                }}
                onMouseLeave={(e) => {
                  e.currentTarget.style.borderColor = "rgba(0, 0, 0, 0.8)";
                  e.currentTarget.style.backgroundColor = "transparent";
                }}
                className="flex items-center gap-2 md:mb-1"
              >
                <svg
                  className="w-5 h-5"
                  fill="none"
                  stroke="currentColor"
                  viewBox="0 0 24 24"
                >
                  <path
                    strokeLinecap="round"
                    strokeLinejoin="round"
                    strokeWidth={2}
                    d="M12 4v16m8-8H4"
                  />
                </svg>
                Create new folder
              </button>
            </div>
          </div>

          <div
            onDrop={handleDrop}
            onDragOver={handleDragOver}
            onDragLeave={handleDragLeave}
            className={`
              border-2 border-dashed rounded-xl p-12 text-center
              transition-all duration-300
              ${
                isDragging
                  ? "bg-blue-50 scale-105 shadow-lg"
                  : selectedFolder
                    ? "bg-white/50 backdrop-blur-sm hover:shadow-md"
                    : "bg-gray-50"
              }
              ${!selectedFolder ? "cursor-not-allowed" : "cursor-pointer"}
            `}
            style={{
              borderColor: isDragging
                ? "#3b82f6"
                : selectedFolder
                  ? "rgba(0, 0, 0, 0.8)"
                  : "rgba(0, 0, 0, 0.2)",
              transition:
                "border-color 0.25s ease, background-color 0.25s ease",
            }}
          >
            <input
              type="file"
              accept=".pdf"
              onChange={handleFileInput}
              className="hidden"
              id="file-upload"
              disabled={!selectedFolder}
            />
            <label
              htmlFor="file-upload"
              className={
                selectedFolder && !isUploading
                  ? "cursor-pointer"
                  : "cursor-not-allowed"
              }
            >
              <div
                className="flex flex-col items-center justify-center transition-all duration-300 h-full"
                style={{ minHeight: "150px" }}
              >
                {isUploading ? (
                  <>
                    <div className="w-16 h-16 mb-4">
                      <svg
                        className="animate-spin h-16 w-16 text-blue-500"
                        xmlns="http://www.w3.org/2000/svg"
                        fill="none"
                        viewBox="0 0 24 24"
                      >
                        <circle
                          className="opacity-25"
                          cx="12"
                          cy="12"
                          r="10"
                          stroke="currentColor"
                          strokeWidth="4"
                        ></circle>
                        <path
                          className="opacity-75"
                          fill="currentColor"
                          d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"
                        ></path>
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
                        isDragging
                          ? "text-blue-500 scale-110"
                          : selectedFolder
                            ? "text-gray-700"
                            : "text-gray-400"
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
                    <p
                      className={`text-xl font-semibold mb-2 transition-all duration-300 ${
                        selectedFolder ? "text-gray-900" : "text-gray-500"
                      }`}
                    >
                      {selectedFolder
                        ? "Drop your PDF here or click to upload"
                        : "Select a folder first"}
                    </p>
                    {selectedFolder && (
                      <p className="text-sm text-gray-700 transition-opacity duration-300 opacity-100">
                        Upload problem sets to your selected folder
                      </p>
                    )}
                  </>
                )}
              </div>
            </label>
          </div>
        </div>

        {/* Loading State */}
        {isLoading ? (
          <div className="text-center py-12 animate-fade-in">
            <div className="inline-block animate-spin rounded-full h-12 w-12 border-4 border-gray-300 border-t-blue-600 mb-4"></div>
            <p className="text-gray-600 text-lg">Loading your folders...</p>
          </div>
        ) : folders.length > 0 ? (
          <>
            <h2 className="text-2xl font-bold text-gray-900 mb-6">
              Your folders
            </h2>
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
              {folders.map((folder, index) => {
                const colorClasses = getColorClasses(folder.color);
                return (
                  <div
                    key={folder.id}
                    className="bg-white rounded hover:-translate-y-0.5 group flex flex-col transition-all duration-200"
                    style={{
                      animation: `fadeInUp 0.5s ease-out ${index * 0.1}s both`,
                      boxShadow: "0 2px 4px rgba(0,0,0,0.04)",
                      border: "1px solid rgba(0, 0, 0, 0.8)",
                    }}
                    onMouseEnter={(e) => {
                      e.currentTarget.style.boxShadow =
                        "0 4px 8px rgba(0,0,0,0.05)";
                    }}
                    onMouseLeave={(e) => {
                      e.currentTarget.style.boxShadow =
                        "0 2px 4px rgba(0,0,0,0.04)";
                    }}
                  >
                    <Link href={`/dashboard/${folder.id}`} className="cursor-pointer">
                      {/* Top Row: Folder Icon + Title */}
                      <div className="flex-1 flex items-center gap-4 px-5 py-5 transition-all duration-200">
                        <svg
                          className={`w-12 h-12 flex-shrink-0 ${colorClasses.mutedIcon} transition-all duration-200`}
                          fill="currentColor"
                          stroke="currentColor"
                          strokeWidth="0.5"
                          viewBox="0 0 20 20"
                        >
                          <path d="M2 6a2 2 0 012-2h5l2 2h5a2 2 0 012 2v6a2 2 0 01-2 2H4a2 2 0 01-2-2V6z" />
                        </svg>
                        <h3 className="font-bold text-base text-gray-900 truncate">
                          {folder.name}
                        </h3>
                      </div>

                      {/* Bottom Row: Problem Count + Start Solving */}
                      <div className="flex-1 px-5 py-5 flex items-center justify-between border-t border-gray-100">
                        <span className="text-xs font-semibold text-gray-600">
                          {folder.pdfCount}{" "}
                          {folder.pdfCount === 1 ? "problem" : "problems"}
                        </span>
                        <span className="text-xs font-semibold text-gray-700 hover:text-gray-900 flex items-center gap-1 group-hover:gap-2 transition-all border-b border-gray-300 hover:border-gray-700">
                          Open →
                        </span>
                      </div>
                    </Link>

                    {/* View Progress Button */}
                    <div className="px-5 pb-4 border-t border-gray-100">
                      <Link
                        href={`/dashboard/${folder.id}/progress`}
                        className="block w-full text-center py-2 px-4 mt-3 bg-gradient-to-r from-purple-500 to-purple-600 hover:from-purple-600 hover:to-purple-700 text-white text-xs font-semibold rounded transition-all duration-200"
                      >
                        <span className="flex items-center justify-center gap-2">
                          <svg className="w-3 h-3" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 19v-6a2 2 0 00-2-2H5a2 2 0 00-2 2v6a2 2 0 002 2h2a2 2 0 002-2zm0 0V9a2 2 0 012-2h2a2 2 0 012 2v10m-6 0a2 2 0 002 2h2a2 2 0 002-2m0 0V5a2 2 0 012-2h2a2 2 0 012 2v14a2 2 0 01-2 2h-2a2 2 0 01-2-2z" />
                          </svg>
                          View Progress
                        </span>
                      </Link>
                    </div>
                  </div>
                );
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

      {/* Add keyframe animations and custom scrollbar */}
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

        .custom-scrollbar::-webkit-scrollbar {
          width: 8px;
        }

        .custom-scrollbar::-webkit-scrollbar-track {
          background: rgba(229, 231, 235, 0.5);
          border-radius: 4px;
        }

        .custom-scrollbar::-webkit-scrollbar-thumb {
          background: rgba(156, 163, 175, 0.8);
          border-radius: 4px;
        }

        .custom-scrollbar::-webkit-scrollbar-thumb:hover {
          background: rgba(107, 114, 128, 0.9);
        }
      `}</style>
    </div>
  );
}
