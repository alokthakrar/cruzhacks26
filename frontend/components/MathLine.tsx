"use client";

import { useRef, useState, useEffect } from "react";
import dynamic from "next/dynamic";
import type { ReactSketchCanvasRef } from "react-sketch-canvas";
import { useOCR } from "@/hooks/useOCR";
import {
    AlertCircle,
    Lightbulb
} from "lucide-react";

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

interface VisualFeedback {
    bounding_box: number[] | null; // [ymin, xmin, ymax, xmax] 0-1000
    visual_feedback: string | null;
    correct_answer: string | null;
}

interface MathLineProps {
    lineNumber: number;
    strokeColor: string;
    strokeWidth: number;
    onStrokeEnd?: () => void;
    onTextChange?: (lineNumber: number, text: string) => void;
    validationResult?: ValidationResult | null;
    onClearValidation?: (lineNumber: number) => void;
    showVisualFeedback?: boolean;
    problemContext?: string;
    previousStep?: string;
}

export default function MathLine({
    lineNumber,
    strokeColor,
    strokeWidth,
    onStrokeEnd,
    onTextChange,
    validationResult,
    onClearValidation,
    showVisualFeedback = true,
    problemContext,
    previousStep,
}: MathLineProps) {
    const canvasRef = useRef<ReactSketchCanvasRef>(null);
    const [latex, setLatex] = useState<string>("");
    const [isEditing, setIsEditing] = useState(false);
    const { performOCR, error } = useOCR();
    const debounceTimerRef = useRef<NodeJS.Timeout | null>(null);
    const [visualFeedback, setVisualFeedback] = useState<VisualFeedback | null>(null);
    const [showHint, setShowHint] = useState(false);
    const [hintMessage, setHintMessage] = useState<string | null>(null);
    const [canvasHeight, setCanvasHeight] = useState(96); // h-24 = 96px
    const [isResizing, setIsResizing] = useState(false);
    const resizeStartY = useRef(0);
    const resizeStartHeight = useRef(0);

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

            const result = await performOCR(blob, problemContext, previousStep);
            if (result) {
                const extractedText = result.latex.toLowerCase().trim();

                // Check if user is requesting a hint by writing "hint"
                if (extractedText === "hint" || extractedText === "hint?" || extractedText.includes("hint")) {
                    console.log('💡 [HINT] User requested a hint, fetching from LLM...');
                    // Don't set latex to avoid triggering sympy validation
                    setShowHint(true);
                    setHintMessage("Loading hint...");
                    setVisualFeedback(null); // Clear any error feedback

                    // Make a second call to get the actual hint from the LLM
                    const hintResult = await performOCR(blob, problemContext, previousStep, true);
                    if (hintResult?.visualFeedback?.visual_feedback) {
                        console.log('💡 [HINT] Got hint from LLM:', hintResult.visualFeedback.visual_feedback);
                        setHintMessage(hintResult.visualFeedback.visual_feedback);
                    } else {
                        setHintMessage("Try thinking about what operation would help isolate the variable.");
                    }
                    // Don't call onTextChange - bypass sympy validation entirely
                    return;
                } else {
                    setLatex(result.latex);
                    // Set visual feedback if Gemini detected an error
                    console.log('📍 [OCR] Visual Feedback from Gemini:', result.visualFeedback);
                    console.log('📍 [OCR] Setting visual feedback state');
                    setVisualFeedback(result.visualFeedback);
                    setShowHint(false);
                }
            }
        } catch (err) {
            console.error("OCR check failed:", err);
        }
    };

    const handleStroke = () => {
        // Clear visual feedback and hints while writing
        console.log('✏️ [STROKE] Clearing visual feedback and hints');
        setVisualFeedback(null);
        setShowHint(false);
        setHintMessage(null);

        // Clear validation result while writing
        onClearValidation?.(lineNumber);

        // Clear existing timer
        if (debounceTimerRef.current) {
            clearTimeout(debounceTimerRef.current);
        }

        // Set new timer for 2.7 seconds
        debounceTimerRef.current = setTimeout(() => {
            checkOCR();
        }, 2700);

        onStrokeEnd?.();
    };

    const handleClear = () => {
        canvasRef.current?.clearCanvas();
        setLatex("");
        console.log('🧹 [CLEAR] Clearing visual feedback and hints');
        setVisualFeedback(null);
        setShowHint(false);
        setHintMessage(null);

        // Clear debounce timer
        if (debounceTimerRef.current) {
            clearTimeout(debounceTimerRef.current);
        }

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

    // Handle resize drag
    useEffect(() => {
        const handleMouseMove = (e: MouseEvent) => {
            if (isResizing) {
                const deltaY = e.clientY - resizeStartY.current;
                const newHeight = Math.max(60, Math.min(500, resizeStartHeight.current + deltaY));
                setCanvasHeight(newHeight);
            }
        };

        const handleMouseUp = () => {
            setIsResizing(false);
        };

        if (isResizing) {
            document.addEventListener('mousemove', handleMouseMove);
            document.addEventListener('mouseup', handleMouseUp);
            document.body.style.cursor = 'ns-resize';
            document.body.style.userSelect = 'none';
        }

        return () => {
            document.removeEventListener('mousemove', handleMouseMove);
            document.removeEventListener('mouseup', handleMouseUp);
            document.body.style.cursor = '';
            document.body.style.userSelect = '';
        };
    }, [isResizing]);

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
        <>
            <div className={`relative flex border-b border-gray-200 hover:bg-gray-50 transition-colors ${getBgColor()}`}>
                {/* Left border indicator */}
                <div className={`w-1 border-l-4 ${getBorderColor()}`}></div>

                {/* Line number */}
                <div className="w-12 shrink-0 flex items-center justify-center text-sm text-gray-400">
                    {lineNumber}
                </div>

                {/* Canvas area */}
                <div className="flex-1 relative bg-white" style={{ height: `${canvasHeight}px` }}>
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

                    {/* Hint Popup - shown when user writes "hint" */}
                    {showHint && hintMessage && (
                        <div className="absolute inset-2 flex items-center justify-center z-20 pointer-events-none">
                            <div className="bg-gradient-to-br from-blue-50 to-indigo-50 border-2 border-blue-300 px-5 py-4 shadow-xl rounded-xl max-w-md animate-fade-in pointer-events-auto">
                                <div className="flex items-center gap-2 mb-2">
                                    <Lightbulb className="w-5 h-5 text-blue-600" />
                                    <span className="text-base font-semibold text-blue-800">Hint</span>
                                </div>
                                <div className="text-sm text-blue-700 leading-relaxed">{hintMessage}</div>
                                <div className="mt-3 text-xs text-blue-500">Start writing to dismiss</div>
                            </div>
                        </div>
                    )}

                    {/* Visual Feedback Overlay with Yellow Tooltip (for errors) */}
                    {showVisualFeedback && !showHint && visualFeedback?.bounding_box && (
                        <div
                            className="absolute border-2 border-red-500 bg-red-500/10 z-10 transition-all duration-500 group/feedback cursor-help"
                            style={{
                                top: `${visualFeedback.bounding_box[0] / 10}%`,
                                left: `${visualFeedback.bounding_box[1] / 10}%`,
                                height: `${(visualFeedback.bounding_box[2] - visualFeedback.bounding_box[0]) / 10}%`,
                                width: `${(visualFeedback.bounding_box[3] - visualFeedback.bounding_box[1]) / 10}%`,
                            }}
                        >
                            {/* Yellow tooltip on hover */}
                            {visualFeedback.visual_feedback && (
                                <div className="hidden group-hover/feedback:block absolute top-full left-0 mt-1 bg-yellow-50 border-2 border-yellow-400 px-4 py-3 shadow-xl rounded-lg min-w-[250px] max-w-sm whitespace-normal z-30">
                                    <div className="flex items-center gap-2 mb-1">
                                        <Lightbulb className="w-4 h-4 text-yellow-600" />
                                        <span className="text-sm font-semibold text-yellow-700">Hint</span>
                                    </div>
                                    <div className="text-sm text-yellow-700">{visualFeedback.visual_feedback}</div>
                                </div>
                            )}
                        </div>
                    )}


                    {/* OCR Result Display - always show extracted text */}
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
                            <div className="hidden group-hover:block absolute top-0 left-full ml-2 bg-red-50 border-2 border-red-300 px-4 py-3 shadow-xl rounded-lg min-w-[250px] max-w-sm whitespace-normal z-20">
                                <div className="text-sm font-semibold text-red-700 mb-1">Incorrect transformation</div>
                                <div className="text-sm text-red-600">{validationResult.explanation || "Check your work carefully"}</div>
                            </div>
                        </div>
                    )}

                    {/* Show hint lightbulb when user writes "hint" or when there's a warning */}
                    {((showHint && validationResult) || (validationResult && validationResult.is_valid && validationResult.warning)) && (
                    <div className="absolute top-2 left-2 group z-10">
                        <Lightbulb className="w-6 h-6 text-yellow-500 cursor-help animate-pulse drop-shadow-lg" />
                        <div className="hidden group-hover:block absolute top-full left-0 mt-1 bg-yellow-50 border-2 border-yellow-300 px-4 py-3 shadow-xl min-w-[250px] max-w-sm whitespace-normal z-20">
                            <div className="text-sm font-semibold text-yellow-700 mb-1">Hint</div>
                            <div className="text-sm text-yellow-700">
                                {validationResult.warning || validationResult.explanation || "Try working through the next step carefully. Consider what operation would help you isolate the variable."}
                            </div>
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
                <div className="w-16 shrink-0 flex items-center justify-center border-l border-gray-200 bg-white">
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

            {/* Resize Handle */}
            <div
                className={`h-2 bg-gray-100 hover:bg-blue-200 cursor-ns-resize transition-colors flex items-center justify-center group ${isResizing ? 'bg-blue-300' : ''
                    }`}
                onMouseDown={(e) => {
                    setIsResizing(true);
                    resizeStartY.current = e.clientY;
                    resizeStartHeight.current = canvasHeight;
                    e.preventDefault();
                }}
                title="Drag to resize"
            >
                <div className="w-12 h-1 bg-gray-400 rounded-full group-hover:bg-blue-500 transition-colors"></div>
            </div>
        </>
    );
}
