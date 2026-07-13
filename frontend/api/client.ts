import type {
  ChatResponse,
  DocumentSummary,
  Readiness,
  UploadedDocument,
} from "../src/types/documents";

const API_BASE_URL =
  import.meta.env.VITE_API_BASE_URL ?? "http://127.0.0.1:8000";

async function parse<T>(response: Response): Promise<T> {
  if (!response.ok) {
    const error = await response.json().catch(() => null);
    throw new Error(error?.detail ?? `Request failed (${response.status})`);
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
