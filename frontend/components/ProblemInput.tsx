interface ProblemInputProps {
    value: string;
    onChange: (value: string) => void;
}

export default function ProblemInput({ value, onChange }: ProblemInputProps) {
    return (
        <div>
            <label className="block text-xs font-semibold text-gray-500 uppercase tracking-wide mb-2">
                Solve for X
            </label>
            <input
                type="text"
                value={value}
                onChange={(e) => onChange(e.target.value)}
                placeholder="e.g., 3x - 7 = 14"
                className="text-3xl font-semibold text-gray-900 border-none outline-none w-full bg-transparent"
            />
        </div>
    );
}


