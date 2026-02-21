export interface GenerateFormData {
  resume: File;
  jobUrl?: string;
  jobText?: string;
  language: string;
}

export interface GenerateResponse {
  cover_letter: string;
}

function buildForm(data: GenerateFormData): FormData {
  const form = new FormData();
  form.append("resume", data.resume);
  form.append("language", data.language);
  if (data.jobUrl) form.append("job_url", data.jobUrl);
  if (data.jobText) form.append("job_text", data.jobText);
  return form;
}

export async function generateCoverLetter(
  data: GenerateFormData,
): Promise<GenerateResponse> {
  const res = await fetch("/api/generate", {
    method: "POST",
    body: buildForm(data),
  });

  if (!res.ok) {
    const body = await res.json().catch(() => null);
    const message = body?.detail ?? `Server error: ${res.status}`;
    throw new Error(message);
  }

  return res.json();
}

export async function streamCoverLetter(
  data: GenerateFormData,
  onToken: (token: string) => void,
  signal?: AbortSignal,
): Promise<void> {
  const res = await fetch("/api/generate/stream", {
    method: "POST",
    body: buildForm(data),
    signal,
  });

  if (!res.ok) {
    const body = await res.json().catch(() => null);
    const message = body?.detail ?? `Server error: ${res.status}`;
    throw new Error(message);
  }

  const reader = res.body?.getReader();
  if (!reader) throw new Error("No response body");

  const decoder = new TextDecoder();
  let buffer = "";

  while (true) {
    const { done, value } = await reader.read();
    if (done) break;

    buffer += decoder.decode(value, { stream: true });
    const lines = buffer.split("\n");
    buffer = lines.pop() ?? "";

    for (const line of lines) {
      if (line.startsWith("data: ")) {
        const payload = line.slice(6);
        if (payload === "[DONE]") return;
        onToken(payload);
      }
    }
  }
}
