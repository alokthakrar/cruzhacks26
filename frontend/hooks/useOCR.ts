import { useState } from "react";

interface OCRResult {
    latex_string: string;
    is_correct: boolean | null;
    feedback: string;
    hints: string[];
    error_types: string[];
    bounding_box: number[] | null;  // [ymin, xmin, ymax, xmax] 0-1000
    visual_feedback: string | null;
    correct_answer: string | null;
    analysis_error: string | null;
    timing: Record<string, number>;
}

export interface VisualFeedback {
    bounding_box: number[] | null;
    visual_feedback: string | null;
    correct_answer: string | null;
}

export function useOCR() {
    const [isChecking, setIsChecking] = useState(false);
    const [error, setError] = useState<string | null>(null);

    const performOCR = async (imageBlob: Blob, problemContext?: string, previousStep?: string, requestHint?: boolean): Promise<{ latex: string; visualFeedback: VisualFeedback | null }> => {
        setIsChecking(true);
        setError(null);

        try {
            const formData = new FormData();
            formData.append("image", imageBlob, "canvas.png");
            if (problemContext) {
                formData.append("problem_context", problemContext);
            }
            if (previousStep) {
                formData.append("previous_step", previousStep);
            }
            if (requestHint) {
                formData.append("request_hint", "true");
            }

            const apiResponse = await fetch("http://localhost:8000/api/analyze/ocr_first", {
                method: "POST",
                body: formData,
            });

            if (!apiResponse.ok) {
                throw new Error(`API error: ${apiResponse.statusText}`);
            }

            const result: OCRResult = await apiResponse.json();
            
            console.log('🔍 Backend OCR Response:', {
                latex: result.latex_string,
                is_correct: result.is_correct,
                bounding_box: result.bounding_box,
                visual_feedback: result.visual_feedback,
                correct_answer: result.correct_answer
            });
            
            // Extract visual feedback if present
            const visualFeedback: VisualFeedback | null = result.bounding_box 
                ? { 
                    bounding_box: result.bounding_box, 
                    visual_feedback: result.visual_feedback,
                    correct_answer: result.correct_answer
                  }
                : null;
            
            console.log('📦 Extracted visualFeedback:', visualFeedback);
            
            return {
                latex: result.latex_string || "",
                visualFeedback
            };
        } catch (err) {
            const errorMessage = err instanceof Error ? err.message : "Failed to analyze";
            setError(errorMessage);
            throw new Error(errorMessage);
        } finally {
            setIsChecking(false);
        }
    };

    return { performOCR, isChecking, error };
}
