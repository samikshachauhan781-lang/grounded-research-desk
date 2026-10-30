import { ApiError } from "./client";

type ErrorEnvelope = {
  error?: {
    message?: string;
  };
};

/** Parse FastAPI ErrorEnvelope JSON from a failed response body. */
export function parseApiErrorMessage(body: string): string | null {
  if (!body.trim()) return null;
  try {
    const json = JSON.parse(body) as ErrorEnvelope;
    const message = json.error?.message?.trim();
    return message || null;
  } catch {
    return null;
  }
}

/** User-facing upload failure text from API or network errors. */
export function resolveUploadErrorMessage(err: unknown, maxUploadBytes?: number): string {
  if (err instanceof ApiError) {
    const parsed = parseApiErrorMessage(err.body);
    if (err.status === 413) {
      const mb = maxUploadBytes ? Math.round(maxUploadBytes / 1024 / 1024) : 5;
      return parsed ?? `File exceeds the maximum upload size (${mb} MB).`;
    }
    if (parsed) {
      return parsed;
    }
    if (err.status === 422) {
      return "This file couldn't be uploaded. Check format and UTF-8 encoding.";
    }
  }
  return "Upload failed. Please try again.";
}
