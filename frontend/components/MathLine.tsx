"use client";

import { useRef, useState, useEffect } from "react";
import dynamic from "next/dynamic";
import type { ReactSketchCanvasRef } from "react-sketch-canvas";
import { useOCR } from "@/hooks/useOCR";
import { AlertCircle, Lightbulb } from "lucide-react";

const ReactSketchCanvas = dynamic(
    () => import("react-sketch-canvas").then((mod) => mod.ReactSketchCanvas),
    { ssr: false }
);

interface ValidationResult {
    is_valid: boolean;
    error: string | null;
    explanation: string;
    warning?: string | null;
}

interface MathLineProps {
    lineNumber: number;
    strokeColor: string;
    strokeWidth: number;
    onStrokeEnd?: () => void;
    onTextChange?: (lineNumber: number, text: string) => void;
    validationResult?: ValidationResult | null;
    onClearValidation?: (lineNumber: number) => void;
    onOcrStatusChange?: (lineNumber: number, isProcessing: boolean) => void;
    onWritingStatusChange?: (lineNumber: number, isWriting: boolean) => void;
}

export default function MathLine({
    lineNumber,
    strokeColor,
    strokeWidth,
    onStrokeEnd,
    onTextChange,
    validationResult,
    onClearValidation,
    onOcrStatusChange,
    onWritingStatusChange,
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
            onOcrStatusChange?.(lineNumber, true);
            const dataUrl = await canvasRef.current.exportImage("png");
            const response = await fetch(dataUrl);
            const blob = await response.blob();

            const result = await performOCR(blob);
            setLatex(result);
        } catch (err) {
            console.error("OCR check failed:", err);
        } finally {
            onOcrStatusChange?.(lineNumber, false);
        }
    };

    const handleStroke = () => {
        // Mark as writing in progress
        onWritingStatusChange?.(lineNumber, true);

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

        // Clear writing and OCR status
        onWritingStatusChange?.(lineNumber, false);
        onOcrStatusChange?.(lineNumber, false);

        // Clear validation result
        onClearValidation?.(lineNumber);
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
            return "border-l-blue-400";
        }
        if (validationResult.warning) {
            return "border-l-yellow-500";
        }
        return validationResult.is_valid ? "border-l-green-500" : "border-l-red-500";
    };

    const getBgColor = () => {
        if (validationResult === null || validationResult === undefined) {
            return "";
        }
        if (validationResult.warning) {
            return "bg-yellow-50";
        }
        return validationResult.is_valid ? "bg-green-50" : "bg-red-50";
    };

    return (
        <div className={`relative flex border-b border-gray-200 hover:bg-gray-50 transition-colors ${getBgColor()}`}>
            {/* Left border indicator */}
            <div className={`w-1 border-l-4 ${getBorderColor()}`}></div>

            {/* Line number */}
            <div className="w-12 flex-shrink-0 flex items-center justify-center text-sm text-gray-400">
                {lineNumber}
            </div>

            {/* Canvas area */}
            <div className="flex-1 relative h-24 bg-white">
                <ReactSketchCanvas
                    ref={canvasRef}
                    width="100%"
                    height="100%"
                    strokeWidth={strokeWidth}
                    strokeColor={strokeColor}
                    canvasColor="white"
                    onStroke={handleStroke}
                    style={{ position: "absolute", inset: 0 }}
                />

                {/* OCR Result Display - click to edit */}
                {latex && !isEditing && (
                    <span
                        onClick={() => setIsEditing(true)}
                        className="absolute top-2 right-2 text-sm font-mono text-gray-800 cursor-default max-w-[60%] truncate"
                    >
                        {latex}
                    </span>
                )}

                {/* Editing mode */}
                {isEditing && (
                    <div className="absolute inset-0 flex items-center px-4 bg-white/95 z-10">
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
                            className="flex-1 text-sm border border-blue-300 px-2 py-1 rounded font-mono"
                        />
                    </div>
                )}

                {/* Validation icons with hover tooltip */}
                {validationResult && !validationResult.is_valid && (
                    <div className="absolute top-2 left-2 group z-10">
                        <AlertCircle className="w-6 h-6 text-red-500 cursor-help animate-pulse drop-shadow-lg" />
                        <div className="hidden group-hover:block absolute top-full left-0 mt-1 bg-red-50 border-2 border-red-300 px-4 py-3 shadow-xl min-w-[250px] max-w-sm whitespace-normal z-20">
                            <div className="text-sm font-semibold text-red-700 mb-1">Incorrect transformation</div>
                            <div className="text-sm text-red-600">{validationResult.error || validationResult.explanation}</div>
                        </div>
                    </div>
                )}

                {validationResult && validationResult.is_valid && validationResult.warning && (
                    <div className="absolute top-2 left-2 group z-10">
                        <Lightbulb className="w-6 h-6 text-yellow-500 cursor-help animate-pulse drop-shadow-lg" />
                        <div className="hidden group-hover:block absolute top-full left-0 mt-1 bg-yellow-50 border-2 border-yellow-300 px-4 py-3 shadow-xl min-w-[250px] max-w-sm whitespace-normal z-20">
                            <div className="text-sm font-semibold text-yellow-700 mb-1">Hint</div>
                            <div className="text-sm text-yellow-700">{validationResult.warning}</div>
                        </div>
                    </div>
                )}

                {/* OCR Error Display */}
                {error && (
                    <div className="absolute top-2 right-16 bg-red-50 border border-red-300 rounded px-3 py-1 shadow-md z-10 max-w-md">
                        <div className="text-xs text-red-600">{error}</div>
                    </div>
                )}
            </div>

            {/* Clear button */}
            <div className="w-16 flex-shrink-0 flex items-center justify-center border-l border-gray-200 bg-white">
                <button
                    onClick={handleClear}
                    className="w-full h-full flex items-center justify-center text-gray-400 hover:bg-gray-100 hover:text-red-500 transition-colors"
                    title="Clear this line"
                >
                    <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M6 18L18 6M6 6l12 12" />
                    </svg>
                </button>
            </div>
        </div>
    );
}
