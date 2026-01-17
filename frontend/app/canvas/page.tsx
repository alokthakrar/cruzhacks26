"use client";

import { useState, useCallback } from "react";
import MathLine from "@/components/MathLine";
import ProblemInput from "@/components/ProblemInput";

interface ValidationResult {
  is_valid: boolean;
  error: string | null;
  explanation: string;
  warning?: string | null;
}

export default function CanvasPage() {
  const [lines, setLines] = useState<number[]>([1]);
  const [strokeColor] = useState("#000000");
  const [strokeWidth] = useState(4);
  const [problemText, setProblemText] = useState("2x + 5 = 13");
  const [lineTexts, setLineTexts] = useState<Map<number, string>>(new Map());
  const [validationResults, setValidationResults] = useState<Map<number, ValidationResult>>(new Map());
  const [isValidating, setIsValidating] = useState(false);
  const [finalResult, setFinalResult] = useState<{correct: boolean, message: string} | null>(null);

  const handleStrokeEnd = (lineNumber: number) => {
    // If writing on the last line, add a new line
    if (lineNumber === lines[lines.length - 1]) {
      setLines([...lines, lineNumber + 1]);
    }
  };

  const handleTextChange = useCallback((lineNumber: number, text: string) => {
    setLineTexts(prev => {
      const newMap = new Map(prev);
      if (text) {
        newMap.set(lineNumber, text);
      } else {
        newMap.delete(lineNumber);
      }
      return newMap;
    });
  }, []);

  const handleValidateAll = async () => {
    setIsValidating(true);
    setValidationResults(new Map());
    setFinalResult(null);

    try {
      // Get all expressions in order, including the problem as the first expression
      const userExpressions = lines
        .map(lineNum => lineTexts.get(lineNum) || "")
        .filter(text => text.trim() !== "");

      if (userExpressions.length < 1) {
        alert("Write at least one step to validate");
        setIsValidating(false);
        return;
      }

      // Include problem text as the starting point
      const expressions = [problemText.replace(/\s+/g, ''), ...userExpressions];

      const response = await fetch("http://localhost:8000/api/analyze/validate_sequence", {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify({ expressions }),
      });

      if (!response.ok) {
        throw new Error(`Validation failed: ${response.statusText}`);
      }

      const data = await response.json();
      
      // Map results to line numbers
      // result.step_number 1 = transition from problem to line 1
      // result.step_number 2 = transition from line 1 to line 2, etc.
      const resultsMap = new Map<number, ValidationResult>();
      data.results.forEach((result: any) => {
        // step_number indicates the transition, so we apply it to the target line
        const lineNumber = result.step_number;
        resultsMap.set(lineNumber, {
          is_valid: result.is_valid,
          error: result.error,
          explanation: result.explanation,
          warning: result.warning,
        });
      });

      setValidationResults(resultsMap);

      // Check if all steps are valid and they reached a final answer
      const allValid = data.all_valid;
      const lastExpression = userExpressions[userExpressions.length - 1];
      
      // Check if the last line is a solution (e.g., x=4, y=5, etc.)
      const isFinalAnswer = /^[a-zA-Z]\s*=\s*-?\d+(\.\d+)?$/.test(lastExpression);
      
      if (allValid && isFinalAnswer) {
        setFinalResult({
          correct: true,
          message: "🎉 Correct! You solved it!"
        });
      } else if (allValid && !isFinalAnswer) {
        setFinalResult({
          correct: false,
          message: "All steps are valid, but keep going to find the final answer!"
        });
      } else {
        setFinalResult({
          correct: false,
          message: "Fix the errors above to continue"
        });
      }
    } catch (err) {
      console.error("Validation error:", err);
      alert(err instanceof Error ? err.message : "Failed to validate");
    } finally {
      setIsValidating(false);
    }
  };

  return (
    <div className="min-h-screen bg-gray-100 p-8">
      <div className="max-w-4xl mx-auto">
        <h1 className="text-3xl font-bold mb-6">Math Canvas</h1>

        <ProblemInput value={problemText} onChange={setProblemText} />

        <div className="space-y-0 pl-10">
          {lines.map((lineNumber) => (
            <MathLine
              key={lineNumber}
              lineNumber={lineNumber}
              strokeColor={strokeColor}
              strokeWidth={strokeWidth}
              onStrokeEnd={() => handleStrokeEnd(lineNumber)}
              onTextChange={handleTextChange}
              validationResult={validationResults.get(lineNumber)}
            />
          ))}
        </div>

        <div className="mt-6 flex flex-col items-center gap-4">
          <button
            onClick={handleValidateAll}
            disabled={isValidating}
            className="px-8 py-3 bg-blue-600 text-white rounded-lg hover:bg-blue-700 font-semibold disabled:opacity-50 disabled:cursor-not-allowed text-lg"
          >
            {isValidating ? "⏳ Checking..." : "Submit"}
          </button>

          {/* Final Result Message */}
          {finalResult && (
            <div className={`px-6 py-4 rounded-lg border-2 font-semibold text-lg ${
              finalResult.correct 
                ? "bg-green-50 border-green-500 text-green-700" 
                : "bg-yellow-50 border-yellow-500 text-yellow-700"
            }`}>
              {finalResult.message}
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
