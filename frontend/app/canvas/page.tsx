"use client";

import { useRef, useState, useEffect } from "react";
import dynamic from "next/dynamic";
import type { ReactSketchCanvasRef } from "react-sketch-canvas";

// Dynamically import with SSR disabled to avoid hydration mismatch
const ReactSketchCanvas = dynamic(
  () => import("react-sketch-canvas").then((mod) => mod.ReactSketchCanvas),
  { ssr: false }
);

export default function CanvasPage() {
  const canvasRef = useRef<ReactSketchCanvasRef>(null);
  const [exportedImage, setExportedImage] = useState<string | null>(null);
  const [strokeColor, setStrokeColor] = useState("#000000");
  const [strokeWidth, setStrokeWidth] = useState(4);

  const handleClear = () => {
    canvasRef.current?.clearCanvas();
    setExportedImage(null);
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

  const handleExportBase64Only = async () => {
    if (canvasRef.current) {
      const dataUrl = await canvasRef.current.exportImage("png");
      // Strip the data:image/png;base64, prefix
      const base64 = dataUrl.replace(/^data:image\/png;base64,/, "");
      navigator.clipboard.writeText(base64);
      alert("Base64 copied to clipboard!");
      console.log("Base64 (no prefix):", base64);
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
            className="px-4 py-2 bg-gray-500 text-white rounded hover:bg-gray-600"
          >
            Undo
          </button>
          <button
            onClick={handleRedo}
            className="px-4 py-2 bg-gray-500 text-white rounded hover:bg-gray-600"
          >
            Redo
          </button>
          <button
            onClick={handleClear}
            className="px-4 py-2 bg-red-500 text-white rounded hover:bg-red-600"
          >
            Clear
          </button>
          <button
            onClick={handleExport}
            className="px-4 py-2 bg-blue-500 text-white rounded hover:bg-blue-600"
          >
            Export Image
          </button>
          <button
            onClick={handleExportBase64Only}
            className="px-4 py-2 bg-green-500 text-white rounded hover:bg-green-600"
          >
            Copy Base64
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
