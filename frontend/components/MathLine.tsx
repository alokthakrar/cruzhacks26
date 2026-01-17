"use client";

import { useRef, useState, useEffect } from "react";
import dynamic from "next/dynamic";
import type { ReactSketchCanvasRef } from "react-sketch-canvas";
import { useOCR } from "@/hooks/useOCR";

const ReactSketchCanvas = dynamic(
    () => import("react-sketch-canvas").then((mod) => mod.ReactSketchCanvas),
    { ssr: false }
);

interface ValidationResult {
    is_valid: boolean;
    error: string | null;
    explanation: string;
}

interface MathLineProps {
    lineNumber: number;
    strokeColor: string;
    strokeWidth: number;
    onStrokeEnd?: () => void;
    onTextChange?: (lineNumber: number, text: string) => void;
    validationResult?: ValidationResult | null;
}

export default function MathLine({
    lineNumber,
    strokeColor,
    strokeWidth,
    onStrokeEnd,
    onTextChange,
    validationResult,
}: MathLineProps) {
    const canvasRef = useRef<ReactSketchCanvasRef>(null);
    const [latex, setLatex] = useState<string>("");
    const [isEditing, setIsEditing] = useState(false);
    const { performOCR, error } = useOCR();
    const debounceTimerRef = useRef<NodeJS.Timeout | null>(null);

    // Notify parent when text changes
    useEffect(() => {
        onTextChange?.(lineNumber, latex);
    }, [latex, lineNumber, onTextChange]);

    const checkOCR = async () => {
        if (!canvasRef.current) return;

        try {
            const dataUrl = await canvasRef.current.exportImage("png");
            const response = await fetch(dataUrl);
            const blob = await response.blob();

            const result = await performOCR(blob);
            setLatex(result);
        } catch (err) {
            console.error("OCR check failed:", err);
        }
    };

    const handleStroke = () => {
        // Clear existing timer
        if (debounceTimerRef.current) {
            clearTimeout(debounceTimerRef.current);
        }

        // Set new timer for 2 seconds
        debounceTimerRef.current = setTimeout(() => {
            checkOCR();
        }, 2000);

        onStrokeEnd?.();
    };

    const handleClear = () => {
        canvasRef.current?.clearCanvas();
        setLatex("");
        
        // Clear debounce timer
        if (debounceTimerRef.current) {
            clearTimeout(debounceTimerRef.current);
        }
    };

    // Cleanup timer on unmount
    useEffect(() => {
        return () => {
            if (debounceTimerRef.current) {
                clearTimeout(debounceTimerRef.current);
            }
        };
    }, []);

    // Determine border color based on validation
    const getBorderColor = () => {
        if (validationResult === null || validationResult === undefined) {
            return "border-gray-300";
        }
        return validationResult.is_valid ? "border-green-500" : "border-red-500";
    };

    return (
        <div className={`relative border-2 ${getBorderColor()} rounded-lg bg-white overflow-visible mb-4`}>
            {/* Line number indicator */}
            <div className="absolute -left-8 top-1/2 -translate-y-1/2 text-gray-400 font-mono text-sm">
                {lineNumber}
            </div>

            {/* OCR Result Display with Edit */}
            {latex && (
                <div className="absolute top-2 right-16 bg-blue-50 border border-blue-300 rounded px-3 py-1 shadow-md z-10 max-w-md flex items-center gap-2">
                    {isEditing ? (
                        <input
                            type="text"
                            value={latex}
                            onChange={(e) => setLatex(e.target.value)}
                            onBlur={() => setIsEditing(false)}
                            onKeyDown={(e) => {
                                if (e.key === 'Enter') {
                                    setIsEditing(false);
                                }
                            }}
                            autoFocus
                            className="text-sm border px-2 py-1 rounded w-48"
                        />
                    ) : (
                        <>
                            <div className="text-sm font-mono">
                                {latex}
                            </div>
                            <button
                                onClick={() => setIsEditing(true)}
                                className="px-2 py-1 bg-blue-600 text-white text-xs rounded hover:bg-blue-700"
                            >
                                Edit
                            </button>
                        </>
                    )}
                </div>
            )}

            {/* Validation Result */}
            {validationResult && !validationResult.is_valid && (
                <div className="absolute top-12 right-16 bg-red-50 border border-red-300 rounded px-3 py-2 shadow-md z-10 max-w-md">
                    <div className="text-xs font-semibold text-red-700 mb-1">❌ Invalid Step</div>
                    <div className="text-xs text-red-600">{validationResult.error || validationResult.explanation}</div>
                </div>
            )}

            {/* OCR Error Display */}
            {error && (
                <div className="absolute top-2 right-16 bg-red-50 border border-red-300 rounded px-3 py-1 shadow-md z-10 max-w-md">
                    <div className="text-xs text-red-600">{error}</div>
                </div>
            )}

            {/* Canvas Container */}
            <div className="flex items-center">
                <div className="flex-1">
                    <ReactSketchCanvas
                        ref={canvasRef}
                        width="100%"
                        height="100px"
                        strokeWidth={strokeWidth}
                        strokeColor={strokeColor}
                        canvasColor="#ffffff"
                        onStroke={handleStroke}
                    />
                </div>

                {/* Clear Button on the right */}
                <div className="flex flex-col gap-1 p-2 border-l border-gray-300">
                    <button
                        onClick={handleClear}
                        className="px-3 py-2 bg-gray-200 text-gray-700 text-sm rounded hover:bg-gray-300 whitespace-nowrap"
                        title="Clear this line"
                    >
                        ×
                    </button>
                </div>
            </div>
        </div>
    );
}
