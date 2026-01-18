"use client";

import { useRef, useState, useEffect } from "react";
import { ReactSketchCanvas, ReactSketchCanvasRef } from "react-sketch-canvas";

interface ScratchPaperProps {
  isOpen: boolean;
  onClose: () => void;
  strokeColor?: string;
  strokeWidth?: number;
  savedPaths?: string;
  onSavePaths?: (paths: string) => void;
}

export default function ScratchPaper({
  isOpen,
  onClose,
  strokeColor = "#000000",
  strokeWidth = 4,
  savedPaths,
  onSavePaths,
}: ScratchPaperProps) {
  const canvasRef = useRef<ReactSketchCanvasRef>(null);
  const [localStrokeColor, setLocalStrokeColor] = useState(strokeColor);
  const [localStrokeWidth, setLocalStrokeWidth] = useState(strokeWidth);

  // Restore saved paths when opening
  useEffect(() => {
    if (isOpen && savedPaths && canvasRef.current) {
      try {
        canvasRef.current.loadPaths(JSON.parse(savedPaths));
      } catch (err) {
        console.error("Failed to restore scratch paper:", err);
      }
    }
  }, [isOpen, savedPaths]);

  const handleClose = async () => {
    // Save paths before closing
    if (canvasRef.current && onSavePaths) {
      try {
        const paths = await canvasRef.current.exportPaths();
        onSavePaths(JSON.stringify(paths));
      } catch (err) {
        console.error("Failed to save scratch paper:", err);
      }
    }
    onClose();
  };

  const handleClear = () => {
    canvasRef.current?.clearCanvas();
  };

  if (!isOpen) return null;

  return (
    <div className="fixed inset-0 bg-black/50 z-50 flex items-center justify-center p-4">
      <div className="bg-white rounded-xl shadow-2xl w-full max-w-4xl max-h-[90vh] flex flex-col">
        {/* Header */}
        <div className="flex items-center justify-between px-6 py-4 border-b border-gray-200">
          <div className="flex items-center gap-3">
            <h2 className="text-xl font-semibold text-gray-800">Scratch Paper</h2>
            <span className="text-sm text-gray-500">Rough work area</span>
          </div>
          <button
            onClick={handleClose}
            className="text-gray-400 hover:text-gray-600 transition-colors"
            title="Close scratch paper"
          >
            <svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
            </svg>
          </button>
        </div>

        {/* Tools */}
        <div className="px-6 py-3 border-b border-gray-200 flex items-center justify-between">
          <div className="flex items-center gap-6">
            {/* Color Picker */}
            <div className="flex items-center gap-2">
              <span className="text-sm font-medium text-gray-700">Color:</span>
              <div className="flex gap-1.5">
                {['#000000', '#EF4444', '#3B82F6', '#10B981', '#F59E0B', '#8B5CF6'].map((color) => (
                  <button
                    key={color}
                    onClick={() => setLocalStrokeColor(color)}
                    className={`w-7 h-7 rounded-full border-2 transition-all ${
                      localStrokeColor === color ? 'border-gray-900 scale-110' : 'border-gray-300 hover:scale-105'
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
                    onClick={() => setLocalStrokeWidth(width)}
                    className={`px-3 py-1 rounded text-xs font-medium transition-colors ${
                      localStrokeWidth === width
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

          {/* Clear Button */}
          <button
            onClick={handleClear}
            className="px-4 py-2 bg-red-50 text-red-600 hover:bg-red-100 rounded-lg text-sm font-medium transition-colors flex items-center gap-2"
          >
            <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 7l-.867 12.142A2 2 0 0116.138 21H7.862a2 2 0 01-1.995-1.858L5 7m5 4v6m4-6v6m1-10V4a1 1 0 00-1-1h-4a1 1 0 00-1 1v3M4 7h16" />
            </svg>
            Clear All
          </button>
        </div>

        {/* Canvas Area */}
        <div className="flex-1 relative bg-white min-h-[500px]">
          <ReactSketchCanvas
            ref={canvasRef}
            width="100%"
            height="100%"
            strokeWidth={localStrokeWidth}
            strokeColor={localStrokeColor}
            canvasColor="white"
            style={{ position: "absolute", inset: 0 }}
          />
        </div>
      </div>
    </div>
  );
}
