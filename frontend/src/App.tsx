import { useState } from "react";
import { generateCoverLetter, type GenerateFormData } from "./api";
import GenerateForm from "./components/GenerateForm";
import ResultCard from "./components/ResultCard";

export default function App() {
  const [loading, setLoading] = useState(false);
  const [result, setResult] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);

  const handleSubmit = async (data: GenerateFormData) => {
    setLoading(true);
    setError(null);
    setResult(null);
    try {
      const res = await generateCoverLetter(data);
      setResult(res.cover_letter);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Unexpected error");
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="min-h-screen bg-gradient-to-br from-slate-50 to-indigo-50">
      <div className="mx-auto max-w-2xl px-4 py-12">
        <header className="mb-10 text-center">
          <h1 className="text-3xl font-bold tracking-tight text-gray-900">
            Cover Letter Generator
          </h1>
          <p className="mt-2 text-gray-500">
            Загрузите резюме и укажите ссылку на вакансию — получите
            сопроводительное письмо за секунды
          </p>
        </header>

        <div className="rounded-2xl border border-gray-200 bg-white p-6 shadow-sm sm:p-8">
          <GenerateForm onSubmit={handleSubmit} loading={loading} />
        </div>

        {error && (
          <div className="mt-6 rounded-xl border border-red-200 bg-red-50 p-4 text-sm text-red-700">
            {error}
          </div>
        )}

        {result && (
          <div className="mt-6">
            <ResultCard text={result} />
          </div>
        )}
      </div>
    </div>
  );
}
