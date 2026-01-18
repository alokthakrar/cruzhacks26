"use client";

import { useState, useCallback, useEffect } from "react";
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
  const [strokeColor, setStrokeColor] = useState("#000000");
  const [strokeWidth, setStrokeWidth] = useState(4);
  const [problemText, setProblemText] = useState("2x + 5 = 13");
  const [lineTexts, setLineTexts] = useState<Map<number, string>>(new Map());
  const [validationResults, setValidationResults] = useState<Map<number, ValidationResult>>(new Map());
  const [showVisualFeedback, setShowVisualFeedback] = useState(true);

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

  const handleClearValidation = useCallback((lineNumber: number) => {
    setValidationResults(prev => {
      const newMap = new Map(prev);
      newMap.delete(lineNumber);
      return newMap;
    });
  }, []);

  // Automatic validation whenever line texts change
  useEffect(() => {
    const validateSequence = async () => {
      const userExpressions = lines
        .map(lineNum => lineTexts.get(lineNum) || "")
        .filter(text => text.trim() !== "");

      if (userExpressions.length < 1) {
        setValidationResults(new Map());
        return;
      }

      try {
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
          console.error("Validation failed:", response.statusText);
          return;
        }

        const data = await response.json();

        // Map results to line numbers
        const resultsMap = new Map<number, ValidationResult>();

        // eslint-disable-next-line @typescript-eslint/no-explicit-any
        data.results.forEach((result: any) => {
          const lineNumber = result.step_number;
          resultsMap.set(lineNumber, {
            is_valid: result.is_valid,
            error: result.error,
            explanation: result.explanation,
            warning: result.warning,
          });
        });

        setValidationResults(resultsMap);
      } catch (err) {
        console.error("Validation error:", err);
      }
    };

    // Debounce validation to avoid too many requests
    const timer = setTimeout(validateSequence, 500);
    return () => clearTimeout(timer);
  }, [lineTexts, lines, problemText]);

  return (
    <div 
      className="min-h-screen p-8 relative"
      style={{
        backgroundImage: `linear-gradient(rgba(200,200,200,0.1) 1px, transparent 1px), linear-gradient(90deg, rgba(200,200,200,0.1) 1px, transparent 1px)`,
        backgroundSize: '20px 20px',
        backgroundColor: '#fafafa',
        backgroundAttachment: 'fixed'
      }}
    >
      {/* Grain overlay */}
      <div
        style={{
          position: 'absolute',
          inset: 0,
          pointerEvents: 'none',
          backgroundImage: `url("data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' width='180' height='180'%3E%3Cfilter id='n'%3E%3CfeTurbulence type='fractalNoise' baseFrequency='.9' numOctaves='3' stitchTiles='stitch'/%3E%3C/filter%3E%3Crect width='180' height='180' filter='url(%23n)' opacity='.3'/%3E%3C/svg%3E")`,
          backgroundRepeat: 'repeat',
          opacity: 0.9,
          mixBlendMode: 'multiply'
        }}
      />
      <div className="max-w-4xl mx-auto relative z-10">
        {/* Problem Card */}
        <div className="bg-white border border-gray-200 rounded-xl shadow-sm p-6 mb-6">
          <ProblemInput value={problemText} onChange={setProblemText} />
        </div>

        {/* Work Section */}
        <div className="bg-white border border-gray-200 rounded-xl shadow-sm overflow-visible mb-6">
          <div className="px-6 py-3 border-b border-gray-200 flex items-center justify-between">
            {/* Drawing Tools */}
            <div className="flex items-center gap-6">
              {/* Color Picker */}
              <div className="flex items-center gap-2">
                <span className="text-sm font-medium text-gray-700">Color:</span>
                <div className="flex gap-1.5">
                  {['#000000', '#EF4444', '#3B82F6', '#10B981', '#F59E0B', '#8B5CF6'].map((color) => (
                    <button
                      key={color}
                      onClick={() => setStrokeColor(color)}
                      className={`w-7 h-7 rounded-full border-2 transition-all ${
                        strokeColor === color ? 'border-gray-900 scale-110' : 'border-gray-300 hover:scale-105'
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
                          ? 'bg-gray-900 text-white'
                          : 'bg-gray-100 text-gray-600 hover:bg-gray-200'
                      }`}
                    >
                      {width}px
                    </button>
                  ))}
                </div>
              </div>
            </div>

            {/* Visual Feedback Toggle */}
            <button
              onClick={() => setShowVisualFeedback(!showVisualFeedback)}
              className={`px-3 py-1.5 rounded-lg text-xs font-medium transition-colors ${
                showVisualFeedback
                  ? "bg-blue-100 text-blue-700 hover:bg-blue-200"
                  : "bg-gray-100 text-gray-600 hover:bg-gray-200"
              }`}
              title={showVisualFeedback ? "Hide detailed error highlighting" : "Show detailed error highlighting"}
            >
              {showVisualFeedback ? "📍 Detailed Feedback" : "✓ Simple Feedback"}
            </button>
          </div>

          <div>
            {lines.map((lineNumber) => {
              // Get previous line text: problem text for line 1, or previous line's result
              const previousStep = lineNumber === 1 
                ? problemText 
                : lineTexts.get(lineNumber - 1) || "";
              
              return (
                <MathLine
                  key={lineNumber}
                  lineNumber={lineNumber}
                  strokeColor={strokeColor}
                  strokeWidth={strokeWidth}
                  onStrokeEnd={() => handleStrokeEnd(lineNumber)}
                  onTextChange={handleTextChange}
                  validationResult={validationResults.get(lineNumber)}
                  onClearValidation={handleClearValidation}
                  showVisualFeedback={showVisualFeedback}
                  problemContext={problemText}
                  previousStep={previousStep}
                />
              );
            })}
          </div>
        </div>
      </div>
    </div>
  );
}
