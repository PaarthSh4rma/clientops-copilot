import type { ChatResponse, UploadedDocument } from "../src/types/documents";

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL ?? "http://127.0.0.1:8000";

export async function uploadDocument(file: File): Promise<UploadedDocument> {
  const formData = new FormData();
  formData.append("file", file);

  const response = await fetch(`${API_BASE_URL}/documents/upload`, {
    method: "POST",
    body: formData,
  });

  if (!response.ok) {
    const error = await response.json().catch(() => null);
    throw new Error(error?.detail ?? "Failed to upload document");
  }

  return response.json();
}

export async function chatWithDocument(params: {
  documentId: string;
  question: string;
  topK?: number;
}): Promise<ChatResponse> {
  const response = await fetch(`${API_BASE_URL}/documents/chat`, {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
    },
    body: JSON.stringify({
      document_id: params.documentId,
      question: params.question,
      top_k: params.topK ?? 3,
    }),
  });

  if (!response.ok) {
    const error = await response.json().catch(() => null);
    throw new Error(error?.detail ?? "Failed to chat with document");
  }

  return response.json();
}