import { useEffect, useRef, useState } from "react";

interface Props {
  text: string;
  streaming?: boolean;
}

export default function ResultCard({ text, streaming }: Props) {
  const [edited, setEdited] = useState(text);
  const [copied, setCopied] = useState(false);
  const textareaRef = useRef<HTMLTextAreaElement>(null);

  useEffect(() => {
    setEdited(text);
  }, [text]);

  useEffect(() => {
    const ta = textareaRef.current;
    if (ta) {
      ta.style.height = "auto";
      ta.style.height = `${ta.scrollHeight}px`;
    }
  }, [edited]);

  const handleCopy = async () => {
    await navigator.clipboard.writeText(edited);
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  };

  return (
    <div className="rounded-xl border border-gray-200 bg-white p-6 shadow-sm">
      <div className="mb-4 flex items-center justify-between">
        <h2 className="text-lg font-semibold text-gray-800">
          Сопроводительное письмо
          {streaming && (
            <span className="ml-2 inline-block h-2 w-2 animate-pulse rounded-full bg-indigo-500" />
          )}
        </h2>
        <button
          onClick={handleCopy}
          className="cursor-pointer rounded-lg border border-gray-300 px-3 py-1.5 text-xs font-medium text-gray-600 transition hover:bg-gray-100"
        >
          {copied ? "Скопировано!" : "Скопировать"}
        </button>
      </div>
      <textarea
        ref={textareaRef}
        value={edited}
        onChange={(e) => setEdited(e.target.value)}
        readOnly={streaming}
        className="w-full resize-none border-0 bg-transparent p-0 text-sm leading-relaxed text-gray-700 outline-none focus:ring-0"
      />
    </div>
  );
}
