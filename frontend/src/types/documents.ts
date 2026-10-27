export type DocumentSummary = {
  id: string;
  filename: string;
  content_type: string;
  file_size: number;
  checksum: string;
  processing_status: "processing" | "ready" | "failed";
  processing_error: string | null;
  chunk_count: number;
  created_at: string;
  updated_at: string;
};

export type UploadedDocument = DocumentSummary & {
  preview: string;
  message: string;
};

export type Citation = {
  document_id: string;
  filename: string;
  chunk_id: number;
  chunk_index: number;
  page_number: number | null;
  location: string | null;
  relevance_score: number;
  source_preview: string;
};

export type ChatResponse = {
  document_id: string;
  filename: string;
  question: string;
  answer: string;
  status: "supported" | "insufficient_evidence" | "provider_failure";
  citations: Citation[];
};

export type Readiness = {
  status: "ready" | "not_ready";
  dependencies: Record<string, string>;
  limits: { max_upload_size_bytes: number };
  demo_mode: boolean;
  capabilities: {
    upload: boolean;
    delete: boolean;
    grounded_chat: boolean;
  };
};
