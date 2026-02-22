import { useRef, useState } from "react";
import { streamCoverLetter, type GenerateFormData } from "./api";
import GenerateForm from "./components/GenerateForm";
import HistoryPanel from "./components/HistoryPanel";
import LoginPage from "./components/LoginPage";
import ResultCard from "./components/ResultCard";
import Spinner from "./components/Spinner";
import UserHeader from "./components/UserHeader";
import { AuthProvider, useAuth } from "./hooks/useAuth";
import { useHistory } from "./hooks/useHistory";

function Main() {
  const { user, login, logout } = useAuth();
  const [loading, setLoading] = useState(false);
  const [streaming, setStreaming] = useState(false);
  const [result, setResult] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);
  const abortRef = useRef<AbortController | null>(null);
  const { entries, refresh, removeEntry } = useHistory();

  if (user === "loading") {
    return (
      <div className="flex min-h-screen items-center justify-center">
        <Spinner />
      </div>
    );
  }

  if (!user) {
    return <LoginPage onLogin={login} />;
  }

  const handleSubmit = async (data: GenerateFormData) => {
    abortRef.current?.abort();
    const controller = new AbortController();
    abortRef.current = controller;

    setLoading(true);
    setStreaming(true);
    setError(null);
    setResult("");

    try {
      let full = "";
      await streamCoverLetter(
        data,
        (token) => {
          full += token;
          setResult(full);
        },
        controller.signal,
      );
      setResult(full);
      refresh();
    } catch (err) {
      if ((err as Error).name !== "AbortError") {
        setError(err instanceof Error ? err.message : "Unexpected error");
      }
    } finally {
      setLoading(false);
      setStreaming(false);
    }
  };

  const handleHistorySelect = (text: string) => {
    setResult(text);
    setError(null);
  };

  return (
    <div className="min-h-screen bg-gradient-to-br from-slate-50 to-indigo-50">
      <div className="mx-auto max-w-2xl px-4 py-12">
        <UserHeader user={user} onLogout={logout} />

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

        {result !== null && result !== "" && (
          <div className="mt-6">
            <ResultCard text={result} streaming={streaming} />
          </div>
        )}

        <div className="mt-6">
          <HistoryPanel
            entries={entries}
            onSelect={handleHistorySelect}
            onRemove={removeEntry}
          />
        </div>
      </div>
    </div>
  );
}

export default function App() {
  return (
    <AuthProvider>
      <Main />
    </AuthProvider>
  );
}
