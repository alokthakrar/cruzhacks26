"use client";

import { useState } from "react";
import MathLine from "@/components/MathLine";
import ProblemInput from "@/components/ProblemInput";

export default function CanvasPage() {
  const [lines, setLines] = useState<number[]>([1]);
  const [strokeColor] = useState("#000000");
  const [strokeWidth] = useState(4);
  const [problemText, setProblemText] = useState("2x + 5 = 13");

  const handleStrokeEnd = (lineNumber: number) => {
    // If writing on the last line, add a new line
    if (lineNumber === lines[lines.length - 1]) {
      setLines([...lines, lineNumber + 1]);
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
            />
          ))}
        </div>
      </div>
    </div>
  );
}
