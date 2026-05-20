export type UploadedDocument = {
  document_id: string;
  filename: string;
  stored_as: string;
  content_type: string;
  character_count: number;
  chunk_count: number;
  embedded_chunk_count: number;
  embedding_dimensions: number;
  preview: string;
  message: string;
};

export type Citation = {
  chunk_index: number;
  score: number;
  source: string;
  preview: string;
};

export type ChatResponse = {
  document_id: string;
  filename: string;
  question: string;
  answer: string;
  citations: Citation[];
};