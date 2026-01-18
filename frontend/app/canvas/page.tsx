"use client";

import { useRef, useState } from "react";
import dynamic from "next/dynamic";
import type { ReactSketchCanvasRef } from "react-sketch-canvas";
import { BlockMath } from "react-katex";
import "katex/dist/katex.min.css";

// Dynamically import with SSR disabled to avoid hydration mismatch
const ReactSketchCanvas = dynamic(
  () => import("react-sketch-canvas").then((mod) => mod.ReactSketchCanvas),
  { ssr: false }
);

interface AnalysisResult {
  latex_string: string;
  ocr_confidence: number;
  ocr_error: string | null;
  is_correct: boolean | null;
  feedback: string;
  hints: string[];
  error_types: string[];
  analysis_error: string | null;
}

export default function CanvasPage() {
  const canvasRef = useRef<ReactSketchCanvasRef>(null);
  const [exportedImage, setExportedImage] = useState<string | null>(null);
  const [strokeColor, setStrokeColor] = useState("#000000");
  const [strokeWidth, setStrokeWidth] = useState(4);
  
  const [loadingState, setLoadingState] = useState<"idle" | "reading" | "analyzing">("idle");
  const [analysisResult, setAnalysisResult] = useState<AnalysisResult | null>(null);
  const [error, setError] = useState<string | null>(null);

  const handleClear = () => {
    canvasRef.current?.clearCanvas();
    setExportedImage(null);
    setAnalysisResult(null);
    setError(null);
  };

  const handleUndo = () => {
    canvasRef.current?.undo();
  };

  const handleRedo = () => {
    canvasRef.current?.redo();
  };

  const handleExport = async () => {
    if (canvasRef.current) {
      const dataUrl = await canvasRef.current.exportImage("png");
      setExportedImage(dataUrl);
      console.log("Exported image (base64):", dataUrl);
    }
  };

  const handleCheckMyWork = async () => {
    if (!canvasRef.current) return;
    
    try {
      setLoadingState("reading");
      setError(null);
      setAnalysisResult(null);
      
      const dataUrl = await canvasRef.current.exportImage("png");
      
      const response = await fetch(dataUrl);
      const blob = await response.blob();
      
      const formData = new FormData();
      formData.append("image", blob, "canvas.png");
      
      setLoadingState("analyzing");
      
      const apiResponse = await fetch("http://localhost:8000/api/analyze/ocr_first", {
        method: "POST",
        body: formData,
      });
      
      if (!apiResponse.ok) {
        throw new Error(`API error: ${apiResponse.statusText}`);
      }
      
      const result: AnalysisResult = await apiResponse.json();
      setAnalysisResult(result);
      setLoadingState("idle");
      
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to analyze");
      setLoadingState("idle");
    }
  };

  return (
    <div className="min-h-screen bg-gray-100 p-8">
      <div className="max-w-4xl mx-auto">
        <h1 className="text-3xl font-bold mb-6">Math Canvas</h1>

        {/* Controls */}
        <div className="flex gap-4 mb-4 flex-wrap">
          <button
            onClick={handleUndo}
            className="px-4 py-2 bg-gray-500 text-white rounded hover:bg-gray-600 disabled:opacity-50 disabled:cursor-not-allowed"
            disabled={loadingState !== "idle"}
          >
            Undo
          </button>
          <button
            onClick={handleRedo}
            className="px-4 py-2 bg-gray-500 text-white rounded hover:bg-gray-600 disabled:opacity-50 disabled:cursor-not-allowed"
            disabled={loadingState !== "idle"}
          >
            Redo
          </button>
          <button
            onClick={handleClear}
            className="px-4 py-2 bg-red-500 text-white rounded hover:bg-red-600 disabled:opacity-50 disabled:cursor-not-allowed"
            disabled={loadingState !== "idle"}
          >
            Clear
          </button>
          <button
            onClick={handleCheckMyWork}
            className="px-6 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 font-semibold disabled:opacity-50 disabled:cursor-not-allowed"
            disabled={loadingState !== "idle"}
          >
            {loadingState === "reading" && "📖 Reading handwriting..."}
            {loadingState === "analyzing" && "🤔 Analyzing logic..."}
            {loadingState === "idle" && "✓ Check My Work"}
          </button>
          <button
            onClick={handleExport}
            className="px-4 py-2 bg-green-500 text-white rounded hover:bg-green-600"
          >
            Export Image
          </button>

          {/* Stroke controls */}
          <div className="flex items-center gap-2">
            <label className="text-sm">Color:</label>
            <input
              type="color"
              value={strokeColor}
              onChange={(e) => setStrokeColor(e.target.value)}
              className="w-10 h-10 cursor-pointer"
            />
          </div>
          <div className="flex items-center gap-2">
            <label className="text-sm">Width:</label>
            <input
              type="range"
              min="1"
              max="20"
              value={strokeWidth}
              onChange={(e) => setStrokeWidth(Number(e.target.value))}
              className="w-24"
            />
            <span className="text-sm">{strokeWidth}px</span>
          </div>
        </div>

        {/* Canvas */}
        <div className="border-2 border-gray-300 rounded-lg overflow-hidden bg-white">
          <ReactSketchCanvas
            ref={canvasRef}
            width="100%"
            height="500px"
            strokeWidth={strokeWidth}
            strokeColor={strokeColor}
            canvasColor="#ffffff"
          />
        </div>

        {/* Error Display */}
        {error && (
          <div className="mt-6 p-4 bg-red-50 border-2 border-red-300 rounded-lg">
            <h3 className="text-lg font-semibold text-red-700 mb-2">❌ Error</h3>
            <p className="text-red-600">{error}</p>
          </div>
        )}

        {/* Analysis Result - "What AI Saw" Verification UI */}
        {analysisResult && (
          <div className="mt-6 space-y-4">
            {/* OCR Result - What AI Saw */}
            <div className="p-6 bg-blue-50 border-2 border-blue-300 rounded-lg">
              <h3 className="text-lg font-semibold text-blue-900 mb-3">👁️ What AI Saw</h3>
              {analysisResult.ocr_error ? (
                <p className="text-red-600 italic">{analysisResult.ocr_error}</p>
              ) : (
                <div className="space-y-2">
                  <p className="text-sm text-blue-700 mb-2">LaTeX detected:</p>
                  <div className="p-4 bg-white rounded border border-blue-200 font-mono text-sm">
                    {analysisResult.latex_string}
                  </div>
                  <p className="text-sm text-blue-700 mt-3 mb-2">Rendered as:</p>
                  <div className="p-4 bg-white rounded border border-blue-200 text-2xl">
                    <BlockMath math={analysisResult.latex_string} />
                  </div>
                  <p className="text-xs text-blue-600 mt-2">
                    OCR Confidence: {(analysisResult.ocr_confidence * 100).toFixed(0)}%
                  </p>
                </div>
              )}
            </div>

            {/* AI Feedback */}
            {!analysisResult.analysis_error && analysisResult.latex_string && (
              <div className={`p-6 border-2 rounded-lg ${
                analysisResult.is_correct === true 
                  ? "bg-green-50 border-green-300" 
                  : analysisResult.is_correct === false
                  ? "bg-yellow-50 border-yellow-300"
                  : "bg-gray-50 border-gray-300"
              }`}>
                <h3 className="text-lg font-semibold mb-3">
                  {analysisResult.is_correct === true && "✅ Looking Good!"}
                  {analysisResult.is_correct === false && "🤔 Let's Review"}
                  {analysisResult.is_correct === null && "📝 Analysis"}
                </h3>
                <p className="mb-4">{analysisResult.feedback}</p>
                
                {analysisResult.hints.length > 0 && (
                  <div className="mt-4">
                    <h4 className="font-semibold mb-2">💡 Hints:</h4>
                    <ul className="list-disc list-inside space-y-1">
                      {analysisResult.hints.map((hint, idx) => (
                        <li key={idx} className="text-sm">{hint}</li>
                      ))}
                    </ul>
                  </div>
                )}
                
                {analysisResult.error_types.length > 0 && (
                  <div className="mt-4">
                    <h4 className="font-semibold mb-2 text-sm">Error Categories:</h4>
                    <div className="flex flex-wrap gap-2">
                      {analysisResult.error_types.map((type, idx) => (
                        <span key={idx} className="px-2 py-1 bg-yellow-200 text-yellow-800 text-xs rounded">
                          {type}
                        </span>
                      ))}
                    </div>
                  </div>
                )}
              </div>
            )}
          </div>
        )}

        {/* Exported preview */}
        {exportedImage && (
          <div className="mt-6">
            <h2 className="text-xl font-semibold mb-2">Exported Image:</h2>
            <img
              src={exportedImage}
              alt="Exported canvas"
              className="border border-gray-300 rounded max-w-full"
            />
          </div>
        )}
      </div>
    </div>
  );
}
