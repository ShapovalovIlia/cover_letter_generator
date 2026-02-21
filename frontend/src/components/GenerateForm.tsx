import { useCallback, useRef, useState, type FormEvent } from "react";
import type { GenerateFormData } from "../api";
import Spinner from "./Spinner";

interface Props {
  onSubmit: (data: GenerateFormData) => void;
  loading: boolean;
}

type JobInputMode = "url" | "text";

const ACCEPTED_EXTENSIONS = [".pdf", ".docx"] as const;

function isAcceptedFile(name: string): boolean {
  const lower = name.toLowerCase();
  return ACCEPTED_EXTENSIONS.some((ext) => lower.endsWith(ext));
}

export default function GenerateForm({ onSubmit, loading }: Props) {
  const [file, setFile] = useState<File | null>(null);
  const [dragOver, setDragOver] = useState(false);
  const [jobInputMode, setJobInputMode] = useState<JobInputMode>("url");
  const [jobUrl, setJobUrl] = useState("");
  const [jobText, setJobText] = useState("");
  const [language, setLanguage] = useState("ru");
  const inputRef = useRef<HTMLInputElement>(null);

  const handleFile = useCallback((f: File | undefined) => {
    if (!f) return;
    if (!isAcceptedFile(f.name)) {
      alert("Поддерживаются только PDF и DOCX файлы");
      return;
    }
    setFile(f);
  }, []);

  const hasJobInput =
    jobInputMode === "url" ? jobUrl.trim() !== "" : jobText.trim() !== "";

  const handleSubmit = (e: FormEvent) => {
    e.preventDefault();
    if (!file || !hasJobInput) return;

    const data: GenerateFormData =
      jobInputMode === "url"
        ? { resume: file, jobUrl: jobUrl.trim(), language }
        : { resume: file, jobText: jobText.trim(), language };

    onSubmit(data);
  };

  return (
    <form onSubmit={handleSubmit} className="space-y-6">
      <div
        onDragOver={(e) => {
          e.preventDefault();
          setDragOver(true);
        }}
        onDragLeave={() => setDragOver(false)}
        onDrop={(e) => {
          e.preventDefault();
          setDragOver(false);
          handleFile(e.dataTransfer.files[0]);
        }}
        onClick={() => inputRef.current?.click()}
        className={`cursor-pointer rounded-xl border-2 border-dashed p-8 text-center transition-colors ${
          dragOver
            ? "border-indigo-500 bg-indigo-50"
            : file
              ? "border-green-400 bg-green-50"
              : "border-gray-300 hover:border-indigo-400 hover:bg-gray-50"
        }`}
      >
        <input
          ref={inputRef}
          type="file"
          accept=".pdf,.docx"
          className="hidden"
          onChange={(e) => handleFile(e.target.files?.[0])}
        />
        {file ? (
          <p className="text-green-700 font-medium">{file.name}</p>
        ) : (
          <div>
            <p className="text-gray-600 font-medium">
              Перетащите файл резюме сюда
            </p>
            <p className="mt-1 text-sm text-gray-400">PDF или DOCX</p>
          </div>
        )}
      </div>

      <div>
        <div className="mb-2 flex gap-1 rounded-lg bg-gray-100 p-1">
          <button
            type="button"
            onClick={() => setJobInputMode("url")}
            className={`flex-1 rounded-md px-3 py-1.5 text-sm font-medium transition ${
              jobInputMode === "url"
                ? "bg-white text-gray-900 shadow-sm"
                : "text-gray-500 hover:text-gray-700"
            }`}
          >
            Ссылка
          </button>
          <button
            type="button"
            onClick={() => setJobInputMode("text")}
            className={`flex-1 rounded-md px-3 py-1.5 text-sm font-medium transition ${
              jobInputMode === "text"
                ? "bg-white text-gray-900 shadow-sm"
                : "text-gray-500 hover:text-gray-700"
            }`}
          >
            Текст
          </button>
        </div>

        {jobInputMode === "url" ? (
          <>
            <label
              htmlFor="job-url"
              className="mb-1 block text-sm font-medium text-gray-700"
            >
              Ссылка на вакансию
            </label>
            <input
              id="job-url"
              type="url"
              placeholder="https://hh.ru/vacancy/..."
              value={jobUrl}
              onChange={(e) => setJobUrl(e.target.value)}
              className="w-full rounded-lg border border-gray-300 px-4 py-2.5 text-sm focus:border-indigo-500 focus:ring-2 focus:ring-indigo-200 focus:outline-none transition"
            />
          </>
        ) : (
          <>
            <label
              htmlFor="job-text"
              className="mb-1 block text-sm font-medium text-gray-700"
            >
              Описание вакансии
            </label>
            <textarea
              id="job-text"
              rows={6}
              placeholder="Вставьте текст описания вакансии..."
              value={jobText}
              onChange={(e) => setJobText(e.target.value)}
              className="w-full resize-y rounded-lg border border-gray-300 px-4 py-2.5 text-sm focus:border-indigo-500 focus:ring-2 focus:ring-indigo-200 focus:outline-none transition"
            />
          </>
        )}
      </div>

      <div>
        <label
          htmlFor="language"
          className="mb-1 block text-sm font-medium text-gray-700"
        >
          Язык письма
        </label>
        <select
          id="language"
          value={language}
          onChange={(e) => setLanguage(e.target.value)}
          className="w-full rounded-lg border border-gray-300 px-4 py-2.5 text-sm focus:border-indigo-500 focus:ring-2 focus:ring-indigo-200 focus:outline-none transition"
        >
          <option value="ru">Русский</option>
          <option value="en">English</option>
        </select>
      </div>

      <button
        type="submit"
        disabled={loading || !file || !hasJobInput}
        className="w-full cursor-pointer rounded-lg bg-indigo-600 px-6 py-3 text-sm font-semibold text-white transition hover:bg-indigo-700 disabled:cursor-not-allowed disabled:opacity-50"
      >
        {loading ? (
          <span className="inline-flex items-center gap-2">
            <Spinner />
            Генерация...
          </span>
        ) : (
          "Сгенерировать письмо"
        )}
      </button>
    </form>
  );
}
