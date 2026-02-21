export interface GenerateFormData {
  resume: File;
  jobUrl: string;
  language: string;
}

export interface GenerateResponse {
  cover_letter: string;
}

export async function generateCoverLetter(
  data: GenerateFormData,
): Promise<GenerateResponse> {
  const form = new FormData();
  form.append("resume", data.resume);
  form.append("job_url", data.jobUrl);
  form.append("language", data.language);

  const res = await fetch("/api/generate", {
    method: "POST",
    body: form,
  });

  if (!res.ok) {
    const body = await res.json().catch(() => null);
    const message = body?.detail ?? `Server error: ${res.status}`;
    throw new Error(message);
  }

  return res.json();
}
