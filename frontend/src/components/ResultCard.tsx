import { useState } from "react";

interface Props {
  text: string;
}

export default function ResultCard({ text }: Props) {
  const [copied, setCopied] = useState(false);

  const handleCopy = async () => {
    await navigator.clipboard.writeText(text);
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  };

  return (
    <div className="rounded-xl border border-gray-200 bg-white p-6 shadow-sm">
      <div className="mb-4 flex items-center justify-between">
        <h2 className="text-lg font-semibold text-gray-800">
          Сопроводительное письмо
        </h2>
        <button
          onClick={handleCopy}
          className="cursor-pointer rounded-lg border border-gray-300 px-3 py-1.5 text-xs font-medium text-gray-600 transition hover:bg-gray-100"
        >
          {copied ? "Скопировано!" : "Скопировать"}
        </button>
      </div>
      <div className="whitespace-pre-wrap text-sm leading-relaxed text-gray-700">
        {text}
      </div>
    </div>
  );
}
