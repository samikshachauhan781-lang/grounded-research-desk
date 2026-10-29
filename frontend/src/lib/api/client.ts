const ENV_BASE = String(import.meta.env.VITE_API_BASE ?? "").replace(/\/$/, "");
const FALLBACK_BASE = "http://127.0.0.1:8000";

let cachedBase: string | null = null;

async function probeHealth(base: string): Promise<boolean> {
  try {
    const response = await fetch(`${base}/health`, { signal: AbortSignal.timeout(2500) });
    if (!response.ok) return false;
    const body = (await response.json()) as { status?: string };
    return body.status === "ok";
  } catch {
    return false;
  }
}

export async function resolveApiBase(): Promise<string | null> {
  if (cachedBase !== null && (await probeHealth(cachedBase))) {
    return cachedBase;
  }
  cachedBase = null;
  const candidates = [...new Set([ENV_BASE, "", FALLBACK_BASE])];
  for (const base of candidates) {
    if (await probeHealth(base)) {
      cachedBase = base;
      return base;
    }
  }
  return null;
}

export class ApiError extends Error {
  status: number;
  body: string;

  constructor(status: number, body: string) {
    super(body || `HTTP ${status}`);
    this.status = status;
    this.body = body;
  }
}

async function request<T>(path: string, init?: RequestInit): Promise<T> {
  const base = cachedBase ?? (await resolveApiBase()) ?? ENV_BASE;
  let response: Response;
  try {
    response = await fetch(`${base}${path}`, init);
  } catch (error) {
    if (base !== FALLBACK_BASE) {
      cachedBase = FALLBACK_BASE;
      response = await fetch(`${FALLBACK_BASE}${path}`, init);
    } else {
      throw error;
    }
  }
  if (!response.ok) {
    const text = await response.text();
    throw new ApiError(response.status, text);
  }
  if (response.status === 204) {
    return undefined as T;
  }
  return (await response.json()) as T;
}

export type Health = { status: string; app: string; version: string };
export type DocumentItem = {
  document_id: string;
  filename: string;
  created_at: string;
  chunk_count: number;
  processing_status: string;
};
export type DocumentDetail = {
  document_id: string;
  filename: string;
  created_at: string;
  updated_at: string;
  byte_size: number;
  chunk_count: number;
  processing_status: string;
  processing_error: string | null;
  preview: string | null;
};
export type Citation = {
  citation_id: string;
  chunk_id: string;
  document_id: string;
  filename: string;
  snippet: string;
  score?: number;
};
export type AskResponse = {
  answer: string;
  citations: Citation[];
  insufficient_evidence: boolean;
  retrieval: Record<string, unknown>;
  request_id: string;
  session_id?: string | null;
};

export type ResearchResponse = {
  answer: string;
  citations: Citation[];
  steps: Array<{ step_index: number; tool: string; tool_input: Record<string, unknown>; observation_summary: string }>;
  status: string;
  request_id: string;
};
export type SearchResponse = {
  query: string;
  results: Array<{
    chunk_id: string;
    document_id: string;
    filename: string;
    snippet: string;
    score: number;
  }>;
  duration_ms: number;
  model: string;
  top_k?: number;
};
export type SessionItem = {
  session_id: string;
  title: string;
  created_at: string;
  updated_at: string;
  message_count: number;
};
export type CollectionItem = {
  collection_id: string;
  name: string;
  description: string;
  document_count: number;
  created_at: string;
};
export type PublicSettings = {
  app_name: string;
  app_env: string;
  embedding_provider: string;
  embedding_model_name: string;
  llm_provider: string;
  retrieval_top_k: number;
  max_upload_bytes: number;
  allowed_upload_extensions: string[];
  demo_mode: boolean;
  agent_enabled: boolean;
};
export type SystemStatus = {
  status: string;
  database: string;
  document_count: number;
  chunk_count: number;
  embedding_model: string;
  llm_provider: string;
  version: string;
};

export const api = {
  health: () => request<Health>("/health"),
  ready: () => request<{ status: string; database: string }>("/health/ready"),
  systemStatus: () => request<SystemStatus>("/api/v1/system/status"),
  publicSettings: () => request<PublicSettings>("/api/v1/settings/public"),
  listDocuments: () => request<{ items: DocumentItem[]; total: number }>("/api/v1/documents"),
  uploadDocument: (file: File) => {
    const body = new FormData();
    body.append("file", file);
    return request<{ document_id: string; filename: string; chunk_count: number; status: string }>(
      "/api/v1/documents",
      { method: "POST", body },
    );
  },
  deleteDocument: (id: string) => request<void>(`/api/v1/documents/${id}`, { method: "DELETE" }),
  getDocument: (id: string) => request<DocumentDetail>(`/api/v1/documents/${id}`),
  getDocumentContent: (id: string) =>
    request<{ content_text: string; filename: string }>(`/api/v1/documents/${id}/content`),
  getChunks: (id: string) =>
    request<{
      items: Array<{ chunk_id: string; chunk_index: number; text: string; char_start?: number; char_end?: number }>;
    }>(`/api/v1/documents/${id}/chunks`),
  search: (query: string, top_k = 5) =>
    request<SearchResponse>("/api/v1/search", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ query, top_k }),
    }),
  ask: (question: string, options?: { document_ids?: string[]; session_id?: string }) =>
    request<AskResponse>("/api/v1/ask", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        question,
        document_ids: options?.document_ids,
        session_id: options?.session_id,
      }),
    }),
  getSession: (id: string) => request<SessionItem>(`/api/v1/sessions/${id}`),
  getSessionMessages: (id: string) =>
    request<
      Array<{
        message_id: string;
        question: string;
        answer: string;
        citations: Citation[];
        created_at: string;
      }>
    >(`/api/v1/sessions/${id}/messages`),
  listSessions: () => request<SessionItem[]>("/api/v1/sessions"),
  createSession: (title?: string) =>
    request<SessionItem>("/api/v1/sessions", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ title }),
    }),
  deleteSession: (id: string) => request<void>(`/api/v1/sessions/${id}`, { method: "DELETE" }),
  listCollections: () => request<CollectionItem[]>("/api/v1/collections"),
  createCollection: (name: string, description = "") =>
    request<CollectionItem>("/api/v1/collections", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ name, description }),
    }),
  deleteCollection: (id: string) => request<void>(`/api/v1/collections/${id}`, { method: "DELETE" }),
  addCollectionDocument: (collectionId: string, documentId: string) =>
    request<void>(`/api/v1/collections/${collectionId}/documents`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ document_id: documentId }),
    }),
  removeCollectionDocument: (collectionId: string, documentId: string) =>
    request<void>(`/api/v1/collections/${collectionId}/documents/${documentId}`, { method: "DELETE" }),
  listEvalRuns: () =>
    request<
      Array<{
        run_id: string;
        dataset_name: string;
        metrics: Record<string, number>;
        config: Record<string, unknown>;
        created_at: string;
      }>
    >("/api/v1/evaluations/runs"),
  runEvaluation: () =>
    request<{ run_id: string; metrics: Record<string, number>; created_at: string }>(
      "/api/v1/evaluations/runs",
      {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ dataset_name: "golden", top_k: 5 }),
      },
    ),
  activity: () => request<{ items: Array<Record<string, unknown>> }>("/api/v1/activity"),
  research: (goal: string) =>
    request<ResearchResponse>("/api/v1/research", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ goal }),
    }),
};
