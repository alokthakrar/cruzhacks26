"use client";

import { useState, useEffect, useCallback } from "react";
import Link from "next/link";
import Image from "next/image";
import { useParams, useRouter } from "next/navigation";
import MathLine from "@/components/MathLine";
import ScratchPaper from "@/components/ScratchPaper";
import {
  getQuestionById,
  getSubjectQuestions,
  Question,
  submitAnswer,
  MistakeRecord,
} from "@/lib/api";

interface ValidationResult {
  is_valid: boolean;
  error: string | null;
  explanation: string;
  warning?: string | null;
  is_final_answer?: boolean;
}

export default function QuestionCanvasPage() {
  const params = useParams();
  const router = useRouter();
  const folderId = params.folderId as string;
  const questionId = params.questionId as string;

  // Question state
  const [question, setQuestion] = useState<Question | null>(null);
  const [allQuestions, setAllQuestions] = useState<Question[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  // Canvas state
  const [lines, setLines] = useState<number[]>([1])
  const [strokeColor, setStrokeColor] = useState('#000000')
  const [strokeWidth, setStrokeWidth] = useState(4)
  const [lineTexts, setLineTexts] = useState<Map<number, string>>(new Map())
  const [validationResults, setValidationResults] = useState<Map<number, ValidationResult>>(new Map())
  const [showVisualFeedback, setShowVisualFeedback] = useState(true)
  const [isEraser, setIsEraser] = useState(false)
  const [useLLMFeedback, setUseLLMFeedback] = useState(true)
  
  // Scratch paper state
  const [isScratchPaperOpen, setIsScratchPaperOpen] = useState(false);
  const [scratchPaperPaths, setScratchPaperPaths] = useState<string>("");

  // Solved state
  const [isSolved, setIsSolved] = useState(false);
  const [isNavigating, setIsNavigating] = useState(false);

  // Mistake tracking for BKT
  const [mistakes, setMistakes] = useState<MistakeRecord[]>([]);
  const [hasSubmittedBKT, setHasSubmittedBKT] = useState(false);
  const [startTime] = useState<number>(Date.now());

  // Fetch question and all questions in subject on mount
  useEffect(() => {
    const fetchData = async () => {
      setIsLoading(true);
      try {
        const [q, questionsResponse] = await Promise.all([
          getQuestionById(questionId),
          getSubjectQuestions(folderId, 1, 100),
        ]);
        setQuestion(q);
        setAllQuestions(questionsResponse.questions);
        setError(null);
      } catch (err) {
        console.error("Failed to fetch question:", err);
        setError(
          err instanceof Error ? err.message : "Failed to load question",
        );
      } finally {
        setIsLoading(false);
      }
    };
    fetchData();
  }, [questionId, folderId]);

  const handleStrokeEnd = (lineNumber: number) => {
    if (lineNumber === lines[lines.length - 1]) {
      setLines([...lines, lineNumber + 1]);
    }
  };

  const handleTextChange = useCallback((lineNumber: number, text: string) => {
    setLineTexts((prev) => {
      const newMap = new Map(prev);
      if (text) {
        newMap.set(lineNumber, text);
      } else {
        newMap.delete(lineNumber);
      }
      return newMap;
    });
  }, []);

  const handleClearValidation = useCallback((lineNumber: number) => {
    setValidationResults((prev) => {
      const newMap = new Map(prev);
      newMap.delete(lineNumber);
      return newMap;
    });
  }, []);

  // Get problem text from question
  const problemText = question?.text_content || "";

  // Automatic validation whenever line texts change
  useEffect(() => {
    if (!problemText) return;

    const validateSequence = async () => {
      const userExpressions = lines
        .map((lineNum) => lineTexts.get(lineNum) || "")
        .filter((text) => text.trim() !== "");

      if (userExpressions.length < 1) {
        setValidationResults(new Map());
        setIsSolved(false);
        return;
      }

      try {
        const expressions = [
          problemText.replace(/\s+/g, ""),
          ...userExpressions,
        ];

        const response = await fetch(
          "http://localhost:8000/api/analyze/validate_sequence",
          {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ expressions }),
          },
        );

        if (!response.ok) {
          console.error("Validation failed:", response.statusText);
          return;
        }

        const data = await response.json();
        const resultsMap = new Map<number, ValidationResult>();
        const newMistakes: MistakeRecord[] = [];

        let allValid = true;
        let hasFinalAnswer = false;

        // eslint-disable-next-line @typescript-eslint/no-explicit-any
        data.results.forEach((result: any) => {
          resultsMap.set(result.step_number, {
            is_valid: result.is_valid,
            error: result.error,
            explanation: result.explanation,
            warning: result.warning,
            is_final_answer: result.is_final_answer,
          });

          if (!result.is_valid) {
            // Check if the expression looks incomplete (still being typed)
            const toExpr = (result.to_expr || "").trim();
            const isIncomplete =
              // Ends with an operator
              /[+\-*/=^(]$/.test(toExpr) ||
              // Unbalanced parentheses
              (toExpr.match(/\(/g) || []).length >
                (toExpr.match(/\)/g) || []).length ||
              // Very short (likely just started typing)
              toExpr.length < 2 ||
              // Empty
              toExpr === "";

            // Only count as invalid and track mistake if expression looks complete
            if (isIncomplete) {
              // Skip - expression is still being typed, don't mark as error
              return;
            }

            allValid = false;

            // Track this mistake if it's a new one we haven't recorded yet
            const existingMistake = mistakes.find(
              (m) =>
                m.step_number === result.step_number &&
                m.from_expr === result.from_expr &&
                m.to_expr === result.to_expr,
            );
            if (!existingMistake) {
              // Classify the error type based on error message
              let errorType: MistakeRecord["error_type"] = "unknown";
              const errorLower = (result.error || "").toLowerCase();
              if (
                errorLower.includes("arithmetic") ||
                errorLower.includes("calculation")
              ) {
                errorType = "arithmetic";
              } else if (
                errorLower.includes("algebraic") ||
                errorLower.includes("transformation")
              ) {
                errorType = "algebraic";
              } else if (
                errorLower.includes("parse") ||
                errorLower.includes("notation")
              ) {
                errorType = "notation";
              } else if (
                errorLower.includes("concept") ||
                errorLower.includes("prerequisite")
              ) {
                errorType = "conceptual";
              }

              newMistakes.push({
                step_number: result.step_number,
                error_type: errorType,
                error_message: result.error,
                from_expr: result.from_expr,
                to_expr: result.to_expr,
              });
            }
          }
          if (result.is_final_answer) {
            hasFinalAnswer = true;
          }
        });

        // Add new mistakes to state
        if (newMistakes.length > 0) {
          setMistakes((prev) => [...prev, ...newMistakes]);
        }

        setValidationResults(resultsMap);

        // Check if problem is solved: backend returns is_complete when all valid + final answer reached
        console.log(`🔍 Validation: allValid=${allValid}, hasFinalAnswer=${hasFinalAnswer}, is_complete=${data.is_complete}`)
        setIsSolved(data.is_complete === true)
      } catch (err) {
        console.error("Validation error:", err);
      }
    };

    const timer = setTimeout(validateSequence, 500);
    return () => clearTimeout(timer);
  }, [lineTexts, lines, problemText, mistakes]);

  // Submit to BKT when problem is solved
  useEffect(() => {
    if (!isSolved || hasSubmittedBKT || !question) return;

    const submitToBKT = async () => {
      try {
        // Calculate time taken
        const timeTakenSeconds = Math.floor((Date.now() - startTime) / 1000);

        // Get the final answer from the last line
        const lastLineWithText = Array.from(lineTexts.entries())
          .filter(([_, text]) => text.trim() !== "")
          .sort(([a], [b]) => b - a)[0];
        const userAnswer = lastLineWithText ? lastLineWithText[1] : undefined;

        // For now, use a placeholder user ID - in production this would come from auth
        const userId = "demo_user";

        await submitAnswer(userId, folderId, {
          question_id: questionId,
          is_correct: true, // Problem is solved, so final answer is correct
          user_answer: userAnswer,
          time_taken_seconds: timeTakenSeconds,
          mistake_count: mistakes.length,
          mistakes: mistakes,
        });

        setHasSubmittedBKT(true);
        console.log(`BKT submitted: ${mistakes.length} mistakes recorded`);
      } catch (err) {
        // Log but don't block - BKT is enhancement, not critical path
        console.error("Failed to submit to BKT:", err);
      }
    };

    submitToBKT();
  }, [
    isSolved,
    hasSubmittedBKT,
    question,
    questionId,
    folderId,
    mistakes,
    lineTexts,
    startTime,
  ]);

  // Navigate to next random question
  const handleNextQuestion = () => {
    if (!isSolved || isNavigating) return;

    setIsNavigating(true);

    // Filter out current question and pick a random one
    const otherQuestions = allQuestions.filter((q) => q._id !== questionId);

    if (otherQuestions.length === 0) {
      // No more questions, go back to dashboard
      router.push(`/dashboard/${folderId}`);
      return;
    }

    const randomIndex = Math.floor(Math.random() * otherQuestions.length);
    const nextQuestion = otherQuestions[randomIndex];

    router.push(`/dashboard/${folderId}/question/${nextQuestion._id}`);
  };

  if (isLoading) {
    return (
      <div className="min-h-screen bg-[#fefdfb] flex items-center justify-center">
        <div className="text-center">
          <div className="w-8 h-8 border-4 border-blue-600 border-t-transparent rounded-full animate-spin mx-auto mb-4"></div>
          <p className="text-gray-600">Loading question...</p>
        </div>
      </div>
    );
  }

  if (error || !question) {
    return (
      <div className="min-h-screen bg-[#fefdfb] flex items-center justify-center">
        <div className="text-center">
          <p className="text-red-600 text-lg mb-4">
            {error || "Question not found"}
          </p>
          <Link
            href={`/dashboard/${folderId}`}
            className="text-blue-600 hover:text-blue-700 font-semibold"
          >
            ← Back to questions
          </Link>
        </div>
      </div>
    );
  }

  return (
    <div
      className="min-h-screen relative"
      style={{
        backgroundImage: `linear-gradient(rgba(180,180,180,0.2) 1px, transparent 1px), linear-gradient(90deg, rgba(180,180,180,0.2) 1px, transparent 1px)`,
        backgroundSize: "20px 20px",
        backgroundColor: "#fafafa",
        backgroundAttachment: "fixed",
      }}
    >
      {/* Grain overlay */}
      <div
        style={{
          position: "absolute",
          inset: 0,
          pointerEvents: "none",
          backgroundImage: `url("data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' width='180' height='180'%3E%3Cfilter id='n'%3E%3CfeTurbulence type='fractalNoise' baseFrequency='.9' numOctaves='3' stitchTiles='stitch'/%3E%3C/filter%3E%3Crect width='180' height='180' filter='url(%23n)' opacity='.3'/%3E%3C/svg%3E")`,
          backgroundRepeat: "repeat",
          opacity: 0.7,
          mixBlendMode: "multiply",
        }}
      />

      {/* Owl sticker bottom-left */}
      <div className="absolute bottom-4 left-4 pointer-events-none select-none z-20">
        <Image
          src="/owlsticker.png"
          alt="Perch owl"
          width={160}
          height={160}
          style={{ transform: "scaleX(-1)" }}
          priority={false}
        />
      </div>

      <div className="max-w-4xl mx-auto p-8 relative z-10">
        {/* Header with back button and progress */}
        <div className="mb-6 flex items-center justify-between">
          <Link
            href={`/dashboard/${folderId}`}
            className="inline-flex items-center text-blue-600 hover:text-blue-700 font-semibold transition-all duration-200 hover:gap-2 gap-1 group text-sm"
          >
            <svg
              className="w-4 h-4 transition-transform duration-200 group-hover:-translate-x-1"
              fill="none"
              stroke="currentColor"
              viewBox="0 0 24 24"
            >
              <path
                strokeLinecap="round"
                strokeLinejoin="round"
                strokeWidth={2}
                d="M15 19l-7-7 7-7"
              />
            </svg>
            Back to questions
          </Link>

          <span className="text-sm text-gray-500">
            {allQuestions.length > 0 &&
              `${allQuestions.findIndex((q) => q._id === questionId) + 1} of ${allQuestions.length}`}
          </span>
        </div>

        {/* Problem Card */}
        <div
          className="bg-white border border-gray-200 rounded-xl shadow-sm p-6 mb-6"
          style={{ border: "1px solid rgba(0, 0, 0, 0.8)" }}
        >
          <div className="flex items-center justify-between mb-4">
            <div className="flex items-center gap-3">
              <span className="bg-blue-100 text-blue-700 px-3 py-1 rounded-full text-sm font-semibold">
                Question {question.question_number}
              </span>
              {question.difficulty_estimate && (
                <span className="bg-gray-100 text-gray-600 px-3 py-1 rounded-full text-sm">
                  {question.difficulty_estimate}
                </span>
              )}
              {isSolved && (
                <span className="bg-green-100 text-green-700 px-3 py-1 rounded-full text-sm font-semibold flex items-center gap-1">
                  <svg
                    className="w-4 h-4"
                    fill="none"
                    stroke="currentColor"
                    viewBox="0 0 24 24"
                  >
                    <path
                      strokeLinecap="round"
                      strokeLinejoin="round"
                      strokeWidth={2}
                      d="M5 13l4 4L19 7"
                    />
                  </svg>
                  Solved!
                </span>
              )}
            </div>

            <button
              onClick={() => setIsScratchPaperOpen(true)}
              className="inline-flex items-center gap-2 px-3 py-1.5 bg-gray-100 hover:bg-gray-200 text-gray-700 rounded-lg text-sm font-medium transition-colors"
              title="Open scratch paper for rough work"
            >
              <svg
                className="w-4 h-4"
                fill="none"
                stroke="currentColor"
                viewBox="0 0 24 24"
              >
                <path
                  strokeLinecap="round"
                  strokeLinejoin="round"
                  strokeWidth={2}
                  d="M11 5H6a2 2 0 00-2 2v11a2 2 0 002 2h11a2 2 0 002-2v-5m-1.414-9.414a2 2 0 112.828 2.828L11.828 15H9v-2.828l8.586-8.586z"
                />
              </svg>
              Scratch paper
            </button>
          </div>
          <div className="bg-gradient-to-br from-blue-50 to-blue-100 rounded-xl p-4 border border-blue-200">
            <p className="text-gray-800 text-lg font-medium leading-relaxed">
              {question.text_content}
            </p>
            {/* LaTeX content subtitle - COMMENTED OUT */}
            {/* {question.latex_content && (
              <p className="text-gray-600 text-sm mt-2 font-mono">
                {question.latex_content}
              </p>
            )} */}
          </div>
        </div>

        {/* Work Section */}
        <div
          className="bg-white border border-gray-200 rounded-xl shadow-sm overflow-hidden mb-6"
          style={{ border: "1px solid rgba(0, 0, 0, 0.8)" }}
        >
          <div className="px-6 py-3 border-b border-gray-200 flex items-center justify-between flex-wrap gap-4">
            {/* Drawing Tools */}
            <div className="flex items-center gap-6">
              {/* Eraser Toggle */}
              <button
                onClick={() => setIsEraser(!isEraser)}
                className={`px-3 py-1.5 rounded-lg text-xs font-medium transition-colors ${
                  isEraser
                    ? 'bg-red-100 text-red-700 hover:bg-red-200'
                    : 'bg-gray-100 text-gray-600 hover:bg-gray-200'
                }`}
                title={isEraser ? 'Switch to pen' : 'Switch to eraser'}
              >
                {isEraser ? '🧹 Eraser' : '✏️ Pen'}
              </button>

              {/* Color Picker */}
              <div className="flex items-center gap-2">
                <span className="text-sm font-medium text-gray-700">
                  Color:
                </span>
                <div className="flex gap-1.5">
                  {[
                    "#000000",
                    "#EF4444",
                    "#3B82F6",
                    "#10B981",
                    "#F59E0B",
                    "#8B5CF6",
                  ].map((color) => (
                    <button
                      key={color}
                      onClick={() => {
                        setStrokeColor(color)
                        setIsEraser(false)
                      }}
                      className={`w-7 h-7 rounded-full border-2 transition-all ${
                        strokeColor === color
                          ? "border-gray-900 scale-110"
                          : "border-gray-300 hover:scale-105"
                      }`}
                      style={{ backgroundColor: color }}
                      title={color}
                    />
                  ))}
                </div>
              </div>

              {/* Stroke Width */}
              <div className="flex items-center gap-2">
                <span className="text-sm font-medium text-gray-700">Size:</span>
                <div className="flex gap-1.5">
                  {[2, 4, 6, 8].map((width) => (
                    <button
                      key={width}
                      onClick={() => setStrokeWidth(width)}
                      className={`px-3 py-1 rounded text-xs font-medium transition-colors ${
                        strokeWidth === width
                          ? "bg-gray-900 text-white"
                          : "bg-gray-100 text-gray-600 hover:bg-gray-200"
                      }`}
                    >
                      {width}px
                    </button>
                  ))}
                </div>
              </div>
            </div>

            {/* LLM Feedback Toggle */}
            <button
              onClick={() => setUseLLMFeedback(!useLLMFeedback)}
              className={`px-3 py-1.5 rounded-lg text-xs font-medium transition-colors ${
                useLLMFeedback
                  ? 'bg-purple-100 text-purple-700 hover:bg-purple-200'
                  : 'bg-gray-100 text-gray-600 hover:bg-gray-200'
              }`}
              title={useLLMFeedback ? 'Using AI-enhanced feedback' : 'Using SymPy-only validation'}
            >
              {useLLMFeedback ? '🤖 AI Feedback' : '📐 SymPy Only'}
            </button>
          </div>

          <div>
            {lines.map((lineNumber) => {
              const previousStep =
                lineNumber === 1
                  ? problemText
                  : lineTexts.get(lineNumber - 1) || "";

              return (
                <MathLine
                  key={lineNumber}
                  lineNumber={lineNumber}
                  strokeColor={isEraser ? '#FFFFFF' : strokeColor}
                  strokeWidth={isEraser ? strokeWidth * 3 : strokeWidth}
                  onStrokeEnd={() => handleStrokeEnd(lineNumber)}
                  onTextChange={handleTextChange}
                  validationResult={validationResults.get(lineNumber)}
                  onClearValidation={handleClearValidation}
                  showVisualFeedback={useLLMFeedback}
                  problemContext={problemText}
                  previousStep={previousStep}
                />
              );
            })}
          </div>
        </div>

        {/* Bottom Bar with AI Status, Mistake Count, and Next Button */}
        <div
          className="bg-white/80 backdrop-blur-md border border-gray-200 rounded-xl px-6 py-4 flex items-center justify-between"
          style={{ border: "1px solid rgba(0, 0, 0, 0.8)" }}
        >
          <div className="flex items-center gap-4 flex-1">
            <div className="flex items-center gap-2 text-sm text-gray-600">
              <div
                className={`w-2 h-2 rounded-full animate-pulse ${isSolved ? "bg-green-500" : "bg-blue-500"}`}
              ></div>
              <span className="font-medium">
                {isSolved
                  ? "Problem solved!"
                  : "Perch is monitoring your work..."}
              </span>
            </div>
            {/* Mistake count - COMMENTED OUT */}
            {/* {mistakes.length > 0 && (
              <div className="flex items-center gap-1.5 text-sm text-amber-600 bg-amber-50 px-2.5 py-1 rounded-lg">
                <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z" />
                </svg>
                <span className="font-medium">{mistakes.length} mistake{mistakes.length !== 1 ? 's' : ''}</span>
              </div>
            )}
          </div>

          {/* Next Question Button */}
          <button
            onClick={handleNextQuestion}
            disabled={!isSolved || isNavigating}
            className={`ml-auto px-6 py-2.5 rounded-xl font-semibold transition-all duration-300 flex items-center gap-2 ${
              isSolved
                ? "bg-gradient-to-r from-green-500 to-green-600 text-white hover:from-green-600 hover:to-green-700 shadow-lg hover:shadow-xl hover:-translate-y-0.5"
                : "bg-gray-200 text-gray-400 cursor-not-allowed"
            }`}
          >
            {isNavigating ? (
              <>
                <div className="w-4 h-4 border-2 border-white border-t-transparent rounded-full animate-spin"></div>
                Loading...
              </>
            ) : (
              <>
                Next question
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
                    d="M9 5l7 7-7 7"
                  />
                </svg>
              </>
            )}
          </button>
        </div>
      </div>

      {/* Scratch Paper Modal */}
      <ScratchPaper
        isOpen={isScratchPaperOpen}
        onClose={() => setIsScratchPaperOpen(false)}
        strokeColor={strokeColor}
        strokeWidth={strokeWidth}
        savedPaths={scratchPaperPaths}
        onSavePaths={setScratchPaperPaths}
      />

      {/* End main wrapper div */}
    </div>
    </div>
  );
}
