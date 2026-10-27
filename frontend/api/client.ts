import type {
  ChatResponse,
  DocumentSummary,
  Readiness,
  UploadedDocument,
} from "../src/types/documents";

const API_BASE_URL =
  import.meta.env.VITE_API_BASE_URL ?? "http://127.0.0.1:8000";

export class ApiError extends Error {
  status: number;
  detail?: Record<string, unknown>;

  constructor(
    message: string,
    status: number,
    detail?: Record<string, unknown>,
  ) {
    super(message);
    this.status = status;
    this.detail = detail;
  }
}

async function parse<T>(response: Response): Promise<T> {
  if (!response.ok) {
    const error = await response.json().catch(() => null);
    const detail = error?.detail;
    const message =
      typeof detail === "string"
        ? detail
        : typeof detail?.message === "string"
          ? detail.message
          : `Request failed (${response.status})`;
    throw new ApiError(message, response.status, detail);
  }
  return response.json();
}

export async function uploadDocument(file: File): Promise<UploadedDocument> {
  const data = new FormData();
  data.append("file", file);
  return parse(
    await fetch(`${API_BASE_URL}/documents/upload`, {
      method: "POST",
      body: data,
    }),
  );
}

export async function listDocuments(): Promise<DocumentSummary[]> {
  const data = await parse<{ documents: DocumentSummary[] }>(
    await fetch(`${API_BASE_URL}/documents`),
  );
  return data.documents;
}

export async function deleteDocument(id: string): Promise<void> {
  await parse(
    await fetch(`${API_BASE_URL}/documents/${id}`, { method: "DELETE" }),
  );
}

export async function getReadiness(): Promise<Readiness> {
  const response = await fetch(`${API_BASE_URL}/ready`);
  const body = await response.json().catch(() => ({
    status: "not_ready",
    dependencies: {},
    limits: { max_upload_size_bytes: 10 * 1024 * 1024 },
  }));
  return {
    status: body.status === "ready" ? "ready" : "not_ready",
    dependencies: body.dependencies ?? {},
    limits: {
      max_upload_size_bytes:
        body.limits?.max_upload_size_bytes ?? 10 * 1024 * 1024,
    },
    demo_mode: Boolean(body.demo_mode),
    capabilities: body.capabilities ?? {
      upload: true,
      delete: true,
      grounded_chat: true,
    },
  };
}

export async function chatWithDocument(params: {
  documentId: string;
  question: string;
  topK?: number;
}): Promise<ChatResponse> {
  return parse(
    await fetch(`${API_BASE_URL}/documents/chat`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        document_id: params.documentId,
        question: params.question,
        top_k: params.topK ?? 4,
      }),
    }),
  );
}
