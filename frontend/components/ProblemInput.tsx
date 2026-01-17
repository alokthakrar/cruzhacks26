interface ProblemInputProps {
    value: string;
    onChange: (value: string) => void;
}

export default function ProblemInput({ value, onChange }: ProblemInputProps) {
    return (
        <div className="mb-6 p-4 bg-white border-2 border-gray-300 rounded-lg">
            <label className="block text-sm font-semibold text-gray-700 mb-2">
                Problem to Solve:
            </label>
            <input
                type="text"
                value={value}
                onChange={(e) => onChange(e.target.value)}
                placeholder="e.g., 2x + 5 = 13"
                className="w-full px-4 py-2 border border-gray-300 rounded focus:outline-none focus:ring-2 focus:ring-blue-500"
            />
        </div>
    );
}
