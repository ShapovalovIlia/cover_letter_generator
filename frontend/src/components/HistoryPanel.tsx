import { useState } from "react";
import type { HistoryEntry } from "../hooks/useHistory";

interface Props {
  entries: HistoryEntry[];
  onSelect: (text: string) => void;
  onRemove: (id: string) => void;
}

function formatDate(iso: string): string {
  const d = new Date(iso);
  return d.toLocaleDateString("ru-RU", {
    day: "numeric",
    month: "short",
    hour: "2-digit",
    minute: "2-digit",
  });
}

export default function HistoryPanel({
  entries,
  onSelect,
  onRemove,
}: Props) {
  const [open, setOpen] = useState(false);

  if (entries.length === 0) return null;

  return (
    <div className="rounded-xl border border-gray-200 bg-white shadow-sm">
      <button
        type="button"
        onClick={() => setOpen(!open)}
        className="flex w-full items-center justify-between px-5 py-3 text-sm font-medium text-gray-700 hover:bg-gray-50 transition rounded-xl"
      >
        <span>
          История ({entries.length})
        </span>
        <svg
          className={`h-4 w-4 text-gray-400 transition-transform ${open ? "rotate-180" : ""}`}
          fill="none"
          viewBox="0 0 24 24"
          stroke="currentColor"
          strokeWidth={2}
        >
          <path strokeLinecap="round" strokeLinejoin="round" d="M19 9l-7 7-7-7" />
        </svg>
      </button>

      {open && (
        <div className="border-t border-gray-100">
          <ul className="max-h-64 divide-y divide-gray-100 overflow-y-auto">
            {entries.map((entry) => (
              <li
                key={entry.id}
                className="group flex items-start gap-3 px-5 py-3 hover:bg-gray-50 transition"
              >
                <button
                  type="button"
                  onClick={() => onSelect(entry.cover_letter)}
                  className="min-w-0 flex-1 text-left"
                >
                  <p className="truncate text-sm text-gray-700">
                    {entry.cover_letter.slice(0, 100)}...
                  </p>
                  <p className="mt-0.5 text-xs text-gray-400">
                    {formatDate(entry.created_at)}
                    {entry.resume_filename && ` · ${entry.resume_filename}`}
                  </p>
                </button>
                <button
                  type="button"
                  onClick={() => onRemove(entry.id)}
                  className="shrink-0 rounded p-1 text-gray-300 opacity-0 transition hover:text-red-500 group-hover:opacity-100"
                  title="Удалить"
                >
                  <svg className="h-4 w-4" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
                    <path strokeLinecap="round" strokeLinejoin="round" d="M6 18L18 6M6 6l12 12" />
                  </svg>
                </button>
              </li>
            ))}
          </ul>
        </div>
      )}
    </div>
  );
}
