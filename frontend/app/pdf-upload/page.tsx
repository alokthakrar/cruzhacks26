"use client";

import { useState, useRef, useEffect } from "react";
import { BlockMath } from "react-katex";
import "katex/dist/katex.min.css";

interface BoundingBox {
  x: number;
  y: number;
  width: number;
  height: number;
}

interface Question {
  _id: string;
  pdf_id: string;
  subject_id: string | null;
  page_number: number;
  question_number: number;
  text_content: string;
  latex_content: string | null;
  question_type: string;
  difficulty_estimate: string | null;
  bounding_box: BoundingBox;
  cropped_image: string;
  extraction_confidence: number;
}

interface Subject {
  _id: string;
  name: string;
}

interface UploadResponse {
  pdf_id: string;
  filename: string;
  subject_id: string | null;
  status: string;
  message: string;
  total_pages: number;
  question_count: number;
}

interface QuestionsResponse {
  questions: Question[];
  total: number;
  page: number;
  limit: number;
}

type LoadingState = "idle" | "uploading" | "processing" | "loading_questions";

export default function PDFUploadPage() {
  const fileInputRef = useRef<HTMLInputElement>(null);
  const [loadingState, setLoadingState] = useState<LoadingState>("idle");
  const [uploadResult, setUploadResult] = useState<UploadResponse | null>(null);
  const [questions, setQuestions] = useState<Question[]>([]);
  const [error, setError] = useState<string | null>(null);
  const [dragActive, setDragActive] = useState(false);
  const [selectedQuestion, setSelectedQuestion] = useState<Question | null>(null);
  const [subjects, setSubjects] = useState<Subject[]>([]);
  const [selectedSubjectId, setSelectedSubjectId] = useState<string>("");

  // Fetch subjects on mount
  useEffect(() => {
    const fetchSubjects = async () => {
      try {
        const response = await fetch("http://localhost:8000/api/subjects");
        if (response.ok) {
          const data = await response.json();
          setSubjects(data);
        }
      } catch (err) {
        console.error("Failed to fetch subjects:", err);
      }
    };
    fetchSubjects();
  }, []);

  const handleDrag = (e: React.DragEvent) => {
    e.preventDefault();
    e.stopPropagation();
    if (e.type === "dragenter" || e.type === "dragover") {
      setDragActive(true);
    } else if (e.type === "dragleave") {
      setDragActive(false);
    }
  };

  const handleDrop = (e: React.DragEvent) => {
    e.preventDefault();
    e.stopPropagation();
    setDragActive(false);

    if (e.dataTransfer.files && e.dataTransfer.files[0]) {
      handleFile(e.dataTransfer.files[0]);
    }
  };

  const handleFileInput = (e: React.ChangeEvent<HTMLInputElement>) => {
    if (e.target.files && e.target.files[0]) {
      handleFile(e.target.files[0]);
    }
  };

  const handleFile = async (file: File) => {
    if (file.type !== "application/pdf") {
      setError("Please upload a PDF file");
      return;
    }

    try {
      setLoadingState("uploading");
      setError(null);
      setUploadResult(null);
      setQuestions([]);
      setSelectedQuestion(null);

      const formData = new FormData();
      formData.append("pdf", file);
      if (selectedSubjectId) {
        formData.append("subject_id", selectedSubjectId);
      }

      setLoadingState("processing");

      const response = await fetch("http://localhost:8000/api/pdf/upload", {
        method: "POST",
        body: formData,
      });

      if (!response.ok) {
        const errorData = await response.json();
        throw new Error(errorData.detail || `Upload failed: ${response.statusText}`);
      }

      const result: UploadResponse = await response.json();
      setUploadResult(result);

      if (result.status === "completed" && result.question_count > 0) {
        await fetchQuestions(result.pdf_id);
      }

      setLoadingState("idle");
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to upload PDF");
      setLoadingState("idle");
    }
  };

  const fetchQuestions = async (pdfId: string) => {
    try {
      setLoadingState("loading_questions");

      const response = await fetch(
        `http://localhost:8000/api/pdf/${pdfId}/questions?limit=100`
      );

      if (!response.ok) {
        throw new Error("Failed to fetch questions");
      }

      const data: QuestionsResponse = await response.json();
      setQuestions(data.questions);
      setLoadingState("idle");
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to load questions");
      setLoadingState("idle");
    }
  };

  const handleReset = () => {
    setUploadResult(null);
    setQuestions([]);
    setError(null);
    setSelectedQuestion(null);
    if (fileInputRef.current) {
      fileInputRef.current.value = "";
    }
  };

  const getDifficultyColor = (difficulty: string | null) => {
    switch (difficulty) {
      case "easy":
        return "bg-green-100 text-green-800";
      case "medium":
        return "bg-yellow-100 text-yellow-800";
      case "hard":
        return "bg-red-100 text-red-800";
      default:
        return "bg-gray-100 text-gray-800";
    }
  };

  const getTypeColor = (type: string) => {
    const colors: Record<string, string> = {
      integral: "bg-purple-100 text-purple-800",
      derivative: "bg-blue-100 text-blue-800",
      equation: "bg-indigo-100 text-indigo-800",
      limit: "bg-cyan-100 text-cyan-800",
      series: "bg-teal-100 text-teal-800",
      word_problem: "bg-orange-100 text-orange-800",
    };
    return colors[type] || "bg-gray-100 text-gray-800";
  };

  return (
    <div className="min-h-screen bg-gray-100 p-8">
      <div className="max-w-6xl mx-auto">
        <h1 className="text-3xl font-bold mb-2">PDF Question Extractor</h1>
        <p className="text-gray-600 mb-6">
          Upload a PDF with math problems and AI will extract each question
        </p>

        {/* Subject Selector */}
        {!uploadResult && subjects.length > 0 && (
          <div className="mb-6 p-4 bg-white border-2 border-gray-200 rounded-lg">
            <label className="block text-sm font-medium text-gray-700 mb-2">
              Associate with Subject (optional)
            </label>
            <select
              value={selectedSubjectId}
              onChange={(e) => setSelectedSubjectId(e.target.value)}
              className="w-full md:w-64 px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
            >
              <option value="">No subject</option>
              {subjects.map((subject) => (
                <option key={subject._id} value={subject._id}>
                  {subject.name}
                </option>
              ))}
            </select>
            <p className="mt-1 text-sm text-gray-500">
              Questions will be pooled together under the selected subject
            </p>
          </div>
        )}

        {/* Upload Area */}
        {!uploadResult && (
          <div
            className={`border-2 border-dashed rounded-lg p-12 text-center transition-colors ${
              dragActive
                ? "border-blue-500 bg-blue-50"
                : "border-gray-300 bg-white hover:border-gray-400"
            }`}
            onDragEnter={handleDrag}
            onDragLeave={handleDrag}
            onDragOver={handleDrag}
            onDrop={handleDrop}
          >
            {loadingState === "idle" ? (
              <>
                <div className="text-6xl mb-4">📄</div>
                <p className="text-xl mb-2">Drag and drop a PDF here</p>
                <p className="text-gray-500 mb-4">or</p>
                <label className="px-6 py-3 bg-blue-600 text-white rounded-lg cursor-pointer hover:bg-blue-700 font-semibold">
                  Choose File
                  <input
                    ref={fileInputRef}
                    type="file"
                    accept="application/pdf"
                    onChange={handleFileInput}
                    className="hidden"
                  />
                </label>
              </>
            ) : (
              <div className="space-y-4">
                <div className="animate-spin text-6xl">⚙️</div>
                <p className="text-xl">
                  {loadingState === "uploading" && "Uploading PDF..."}
                  {loadingState === "processing" && "Processing pages with AI..."}
                  {loadingState === "loading_questions" && "Loading questions..."}
                </p>
                <p className="text-gray-500">This may take a moment</p>
              </div>
            )}
          </div>
        )}

        {/* Error Display */}
        {error && (
          <div className="mt-6 p-4 bg-red-50 border-2 border-red-300 rounded-lg">
            <h3 className="text-lg font-semibold text-red-700 mb-2">Error</h3>
            <p className="text-red-600">{error}</p>
          </div>
        )}

        {/* Upload Result Summary */}
        {uploadResult && (
          <div className="mt-6 p-6 bg-white border-2 border-gray-200 rounded-lg">
            <div className="flex justify-between items-start">
              <div>
                <h3 className="text-lg font-semibold mb-2">
                  {uploadResult.status === "completed" ? "✅" : "⚠️"}{" "}
                  {uploadResult.filename}
                </h3>
                <p className="text-gray-600">{uploadResult.message}</p>
                <div className="flex flex-wrap gap-2 mt-3 text-sm">
                  <span className="px-3 py-1 bg-blue-100 text-blue-800 rounded">
                    {uploadResult.total_pages} pages
                  </span>
                  <span className="px-3 py-1 bg-green-100 text-green-800 rounded">
                    {uploadResult.question_count} questions extracted
                  </span>
                  {uploadResult.subject_id && (
                    <span className="px-3 py-1 bg-purple-100 text-purple-800 rounded">
                      Subject: {subjects.find(s => s._id === uploadResult.subject_id)?.name || "Unknown"}
                    </span>
                  )}
                </div>
              </div>
              <button
                onClick={handleReset}
                className="px-4 py-2 bg-gray-500 text-white rounded hover:bg-gray-600"
              >
                Upload Another
              </button>
            </div>
          </div>
        )}

        {/* Questions Grid */}
        {questions.length > 0 && (
          <div className="mt-8">
            <h2 className="text-2xl font-bold mb-4">
              Extracted Questions ({questions.length})
            </h2>
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
              {questions.map((question) => (
                <div
                  key={question._id}
                  onClick={() => setSelectedQuestion(question)}
                  className="bg-white border-2 border-gray-200 rounded-lg p-4 cursor-pointer hover:border-blue-400 hover:shadow-md transition-all"
                >
                  {/* Question Image */}
                  <div className="bg-gray-50 rounded mb-3 p-2 flex items-center justify-center min-h-[100px]">
                    <img
                      src={question.cropped_image}
                      alt={`Question ${question.question_number}`}
                      className="max-w-full max-h-[150px] object-contain"
                    />
                  </div>

                  {/* Question Info */}
                  <div className="space-y-2">
                    <div className="flex items-center justify-between">
                      <span className="text-sm text-gray-500">
                        Page {question.page_number}, Q{question.question_number}
                      </span>
                      <span className="text-xs text-gray-400">
                        {(question.extraction_confidence * 100).toFixed(0)}% conf
                      </span>
                    </div>

                    <div className="flex flex-wrap gap-1">
                      <span
                        className={`px-2 py-0.5 text-xs rounded ${getTypeColor(
                          question.question_type
                        )}`}
                      >
                        {question.question_type}
                      </span>
                      {question.difficulty_estimate && (
                        <span
                          className={`px-2 py-0.5 text-xs rounded ${getDifficultyColor(
                            question.difficulty_estimate
                          )}`}
                        >
                          {question.difficulty_estimate}
                        </span>
                      )}
                    </div>

                    {/* LaTeX Preview */}
                    {question.latex_content && (
                      <div className="text-sm bg-gray-50 p-2 rounded overflow-hidden">
                        <BlockMath math={question.latex_content} />
                      </div>
                    )}
                  </div>
                </div>
              ))}
            </div>
          </div>
        )}

        {/* Question Detail Modal */}
        {selectedQuestion && (
          <div
            className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center p-4 z-50"
            onClick={() => setSelectedQuestion(null)}
          >
            <div
              className="bg-white rounded-lg max-w-2xl w-full max-h-[90vh] overflow-y-auto p-6"
              onClick={(e) => e.stopPropagation()}
            >
              <div className="flex justify-between items-start mb-4">
                <h3 className="text-xl font-bold">
                  Page {selectedQuestion.page_number}, Question{" "}
                  {selectedQuestion.question_number}
                </h3>
                <button
                  onClick={() => setSelectedQuestion(null)}
                  className="text-gray-500 hover:text-gray-700 text-2xl"
                >
                  &times;
                </button>
              </div>

              {/* Full Question Image */}
              <div className="bg-gray-50 rounded-lg p-4 mb-4">
                <img
                  src={selectedQuestion.cropped_image}
                  alt="Question"
                  className="max-w-full mx-auto"
                />
              </div>

              {/* Question Details */}
              <div className="space-y-4">
                <div>
                  <h4 className="font-semibold text-gray-700 mb-1">Text Content</h4>
                  <p className="bg-gray-50 p-3 rounded">{selectedQuestion.text_content}</p>
                </div>

                {selectedQuestion.latex_content && (
                  <div>
                    <h4 className="font-semibold text-gray-700 mb-1">LaTeX</h4>
                    <div className="bg-gray-50 p-3 rounded font-mono text-sm mb-2">
                      {selectedQuestion.latex_content}
                    </div>
                    <div className="bg-white border p-4 rounded text-xl">
                      <BlockMath math={selectedQuestion.latex_content} />
                    </div>
                  </div>
                )}

                <div className="flex flex-wrap gap-2">
                  <span
                    className={`px-3 py-1 rounded ${getTypeColor(
                      selectedQuestion.question_type
                    )}`}
                  >
                    Type: {selectedQuestion.question_type}
                  </span>
                  {selectedQuestion.difficulty_estimate && (
                    <span
                      className={`px-3 py-1 rounded ${getDifficultyColor(
                        selectedQuestion.difficulty_estimate
                      )}`}
                    >
                      Difficulty: {selectedQuestion.difficulty_estimate}
                    </span>
                  )}
                  <span className="px-3 py-1 bg-gray-100 text-gray-800 rounded">
                    Confidence: {(selectedQuestion.extraction_confidence * 100).toFixed(0)}%
                  </span>
                </div>

                <div className="text-sm text-gray-500">
                  Bounding Box: x={selectedQuestion.bounding_box.x}, y=
                  {selectedQuestion.bounding_box.y}, {selectedQuestion.bounding_box.width}x
                  {selectedQuestion.bounding_box.height}px
                </div>
              </div>
            </div>
          </div>
        )}
      </div>
    </div>
  );
}
