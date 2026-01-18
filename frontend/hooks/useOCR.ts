import { useState } from "react";

interface OCRResult {
    latex_string: string;
    ocr_confidence: number;
    ocr_error: string | null;
}

export function useOCR() {
    const [isChecking, setIsChecking] = useState(false);
    const [error, setError] = useState<string | null>(null);

    const performOCR = async (imageBlob: Blob): Promise<string> => {
        setIsChecking(true);
        setError(null);

        try {
            const formData = new FormData();
            formData.append("image", imageBlob, "canvas.png");

            const apiResponse = await fetch("http://localhost:8000/api/analyze/ocr_first", {
                method: "POST",
                body: formData,
            });

            if (!apiResponse.ok) {
                throw new Error(`API error: ${apiResponse.statusText}`);
            }

            const result: OCRResult = await apiResponse.json();
            return result.latex_string || "";
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
