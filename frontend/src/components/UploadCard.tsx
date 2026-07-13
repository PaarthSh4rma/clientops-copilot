import { FileText, Trash2, UploadCloud } from "lucide-react";
import { useState } from "react";
import type { DocumentSummary } from "../types/documents";
import { Card } from "./ui/Card";
import { Spinner } from "./ui/Spinner";
import { cn } from "../lib/cn";

const EXTENSIONS = [".txt", ".pdf", ".docx"];

type Props = {
  documents: DocumentSummary[];
  selectedId: string | null;
  isLoading: boolean;
  isUploading: boolean;
  maxUploadSize: number;
  onUpload: (file: File) => void;
  onSelect: (id: string) => void;
  onDelete: (id: string) => void;
};

export function UploadCard({
  documents,
  selectedId,
  isLoading,
  isUploading,
  maxUploadSize,
  onUpload,
  onSelect,
  onDelete,
}: Props) {
  const [isDragging, setIsDragging] = useState(false);
  const [validation, setValidation] = useState<string | null>(null);
  function handleFile(file?: File) {
    if (!file || isUploading) return;
    const extension = `.${file.name.split(".").pop()?.toLowerCase()}`;
    if (!EXTENSIONS.includes(extension))
      return setValidation("Choose a TXT, PDF, or DOCX file.");
    if (file.size > maxUploadSize)
      return setValidation(
        `File must be ${(maxUploadSize / 1024 / 1024).toFixed(0)} MB or smaller.`,
      );
    if (file.size === 0) return setValidation("The selected file is empty.");
    setValidation(null);
    onUpload(file);
  }
  return (
    <Card>
      <div className="mb-6 flex items-start justify-between gap-4">
        <div>
          <p className="text-sm text-cyan-200">Document library</p>
          <h2 className="mt-1 text-2xl font-semibold">Client knowledge</h2>
          <p className="mt-2 text-sm leading-6 text-white/55">
            Single-workspace prototype. Files stay on this server; answers are
            scoped to the selected document.
          </p>
        </div>
        <FileText className="h-6 w-6 text-white/40" />
      </div>
      <label
        aria-label="Upload a document"
        onDragOver={(e) => {
          e.preventDefault();
          setIsDragging(true);
        }}
        onDragLeave={() => setIsDragging(false)}
        onDrop={(e) => {
          e.preventDefault();
          setIsDragging(false);
          handleFile(e.dataTransfer.files?.[0]);
        }}
        className={cn(
          "flex cursor-pointer flex-col items-center rounded-3xl border border-dashed px-6 py-7 text-center transition focus-within:border-cyan-300 focus-within:ring-2 focus-within:ring-cyan-300/30",
          isDragging
            ? "border-cyan-300/70 bg-cyan-300/10"
            : "border-white/15 bg-black/20",
        )}
      >
        {isUploading ? (
          <Spinner />
        ) : (
          <UploadCloud className="mb-3 h-8 w-8 text-cyan-200" />
        )}
        <span className="text-sm font-medium">
          {isUploading ? "Indexing document…" : "Drop or choose a file"}
        </span>
        <span className="mt-1 text-xs text-white/40">
          TXT, PDF, DOCX · maximum {(maxUploadSize / 1024 / 1024).toFixed(0)} MB
        </span>
        <input
          type="file"
          accept=".txt,.pdf,.docx"
          className="sr-only"
          disabled={isUploading}
          onChange={(e) => handleFile(e.target.files?.[0])}
        />
      </label>
      {validation && (
        <p role="alert" className="mt-2 text-sm text-rose-300">
          {validation}
        </p>
      )}
      <div className="mt-6 space-y-2" aria-busy={isLoading}>
        {isLoading && (
          <p className="text-sm text-white/45">Loading documents…</p>
        )}
        {!isLoading && documents.length === 0 && (
          <p className="rounded-2xl border border-white/10 p-4 text-sm text-white/45">
            No documents indexed yet.
          </p>
        )}
        {documents.map((doc) => (
          <div
            key={doc.id}
            className={cn(
              "flex items-center gap-3 rounded-2xl border p-3",
              selectedId === doc.id
                ? "border-cyan-300/40 bg-cyan-300/5"
                : "border-white/10 bg-black/20",
            )}
          >
            <button
              disabled={doc.processing_status !== "ready"}
              className="min-w-0 flex-1 rounded-lg text-left outline-none disabled:cursor-not-allowed disabled:opacity-60 focus-visible:ring-2 focus-visible:ring-cyan-300/60"
              onClick={() => onSelect(doc.id)}
            >
              <span
                title={doc.filename}
                className="block truncate text-sm font-medium"
              >
                {doc.filename}
              </span>
              <span className="text-xs text-white/40">
                {doc.processing_status !== "ready"
                  ? `${doc.processing_status} · `
                  : ""}
                {doc.chunk_count} chunks · {(doc.file_size / 1024).toFixed(1)}{" "}
                KB
              </span>
            </button>
            <button
              aria-label={`Delete ${doc.filename}`}
              className="rounded-xl p-2 text-white/40 outline-none hover:bg-rose-400/10 hover:text-rose-300 focus-visible:ring-2 focus-visible:ring-rose-300/60"
              onClick={() => onDelete(doc.id)}
            >
              <Trash2 className="h-4 w-4" />
            </button>
          </div>
        ))}
      </div>
    </Card>
  );
}
