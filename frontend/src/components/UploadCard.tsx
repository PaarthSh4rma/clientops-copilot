import {
  AlertCircle,
  FileText,
  LockKeyhole,
  Plus,
  Trash2,
  UploadCloud,
  X,
} from "lucide-react";
import { useRef, useState } from "react";
import type { DocumentSummary } from "../types/documents";
import { cn } from "../lib/cn";
import { Spinner } from "./ui/Spinner";

const EXTENSIONS = [".txt", ".pdf", ".docx"];

type Props = {
  documents: DocumentSummary[];
  selectedId: string | null;
  isLoading: boolean;
  isUploading: boolean;
  maxUploadSize: number;
  demoMode: boolean;
  allowSessionUploads?: boolean;
  sessionDocumentIds?: string[];
  backendAvailable: boolean;
  onUpload: (file: File) => void;
  onSelect: (id: string) => void;
  onDelete: (id: string) => void;
};

function formatBytes(bytes: number) {
  if (bytes < 1024) return `${bytes} B`;
  if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(1)} KB`;
  return `${(bytes / 1024 / 1024).toFixed(1)} MB`;
}

function extensionFor(document: DocumentSummary) {
  return document.filename.split(".").pop()?.toUpperCase() || "FILE";
}

export function UploadCard({
  documents,
  selectedId,
  isLoading,
  isUploading,
  maxUploadSize,
  demoMode,
  allowSessionUploads = false,
  sessionDocumentIds = [],
  backendAvailable,
  onUpload,
  onSelect,
  onDelete,
}: Props) {
  const inputRef = useRef<HTMLInputElement>(null);
  const [isDragging, setIsDragging] = useState(false);
  const [validation, setValidation] = useState<string | null>(null);
  const [pendingDelete, setPendingDelete] = useState<DocumentSummary | null>(
    null,
  );
  const uploadsLocked = demoMode && !allowSessionUploads;

  function handleFile(file?: File) {
    if (!file || isUploading || uploadsLocked) return;
    const extension = `.${file.name.split(".").pop()?.toLowerCase()}`;
    if (!EXTENSIONS.includes(extension)) {
      setValidation("Choose a TXT, PDF, or DOCX file.");
      return;
    }
    if (file.size > maxUploadSize) {
      setValidation(`File must be ${formatBytes(maxUploadSize)} or smaller.`);
      return;
    }
    if (file.size === 0) {
      setValidation("The selected file is empty.");
      return;
    }
    setValidation(null);
    onUpload(file);
  }

  return (
    <aside className="flex min-h-0 flex-col border-b border-white/8 bg-[#0c1016] lg:border-r lg:border-b-0">
      <div className="flex items-start justify-between gap-3 border-b border-white/8 px-4 py-4">
        <div>
          <p className="text-sm font-semibold">Document library</p>
          <p className="mt-0.5 text-xs text-slate-500">
            {documents.length}{" "}
            {documents.length === 1 ? "document" : "documents"} · one selected
            at a time
          </p>
        </div>
        <button
          type="button"
          disabled={uploadsLocked || isUploading || !backendAvailable}
          onClick={() => inputRef.current?.click()}
          className="rounded-lg border border-white/10 bg-white/5 p-2 text-slate-300 transition hover:border-sky-400/30 hover:text-sky-200 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-sky-400 disabled:cursor-not-allowed disabled:opacity-40"
          aria-label={
            uploadsLocked
              ? "Uploads disabled in public demo"
              : "Upload document"
          }
          title={
            uploadsLocked
              ? "Uploads are disabled in public demo mode"
              : "Upload document"
          }
        >
          {isUploading ? <Spinner /> : <Plus className="h-4 w-4" />}
        </button>
        <input
          ref={inputRef}
          type="file"
          aria-label="Choose document file"
          accept=".txt,.pdf,.docx"
          className="sr-only"
          disabled={uploadsLocked || isUploading}
          onChange={(event) => {
            handleFile(event.target.files?.[0]);
            event.currentTarget.value = "";
          }}
        />
      </div>

      {!uploadsLocked && backendAvailable && (
        <div className="px-3 pt-3">
          <button
            type="button"
            onClick={() => inputRef.current?.click()}
            onDragOver={(event) => {
              event.preventDefault();
              setIsDragging(true);
            }}
            onDragLeave={() => setIsDragging(false)}
            onDrop={(event) => {
              event.preventDefault();
              setIsDragging(false);
              handleFile(event.dataTransfer.files?.[0]);
            }}
            className={cn(
              "flex w-full items-center gap-3 rounded-xl border border-dashed px-3 py-3 text-left transition focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-sky-400",
              isDragging
                ? "border-sky-400 bg-sky-400/10"
                : "border-white/12 bg-white/[0.025] hover:border-white/25",
            )}
          >
            <UploadCloud className="h-4 w-4 shrink-0 text-sky-300" />
            <span className="min-w-0">
              <span className="block text-xs font-medium">
                Drop or choose a document
              </span>
              <span className="block text-[11px] text-slate-500">
                TXT, PDF, DOCX · {formatBytes(maxUploadSize)} max
              </span>
            </span>
          </button>
          {validation && (
            <p role="alert" className="mt-2 px-1 text-xs text-rose-300">
              {validation}
            </p>
          )}
        </div>
      )}

      {demoMode && (
        <div className="m-3 flex gap-2 rounded-xl border border-violet-400/15 bg-violet-400/[0.06] p-3 text-xs leading-5 text-violet-100/80">
          <LockKeyhole className="mt-0.5 h-3.5 w-3.5 shrink-0" />
          <span>
            {allowSessionUploads
              ? "Upload your own document for this tab. Refreshing clears uploads. Extracted text is sent to AI providers; use non-sensitive files. Sample documents stay read-only."
              : "Sample documents only. Upload and delete are locked in this public demo."}
          </span>
        </div>
      )}

      {!backendAvailable && !isLoading && (
        <div
          role="alert"
          className="m-3 flex gap-2 rounded-xl border border-amber-400/15 bg-amber-400/[0.06] p-3 text-xs leading-5 text-amber-100/80"
        >
          <AlertCircle className="mt-0.5 h-3.5 w-3.5 shrink-0" />
          <span>
            The API is unavailable. Start the backend, then refresh this page.
          </span>
        </div>
      )}

      <div
        className="min-h-0 flex-1 overflow-y-auto p-3"
        aria-busy={isLoading}
        aria-live="polite"
      >
        {isLoading && (
          <div className="space-y-2" aria-label="Loading document library">
            {[0, 1, 2].map((item) => (
              <div
                key={item}
                className="h-[68px] animate-pulse rounded-xl bg-white/5"
              />
            ))}
          </div>
        )}
        {!isLoading && documents.length === 0 && backendAvailable && (
          <div className="flex min-h-44 flex-col items-center justify-center px-4 text-center">
            <div className="grid h-10 w-10 place-items-center rounded-xl bg-white/5">
              <FileText className="h-4 w-4 text-slate-500" />
            </div>
            <p className="mt-3 text-sm font-medium">No documents yet</p>
            <p className="mt-1 max-w-52 text-xs leading-5 text-slate-500">
              Add a client brief, contract, or delivery plan to start a grounded
              workspace.
            </p>
          </div>
        )}
        <div className="space-y-1.5">
          {documents.map((document) => (
            <div
              key={document.id}
              className={cn(
                "group flex items-center gap-2 rounded-xl border p-2 transition",
                selectedId === document.id
                  ? "border-sky-400/25 bg-sky-400/[0.08]"
                  : "border-transparent hover:border-white/8 hover:bg-white/[0.035]",
              )}
            >
              <button
                type="button"
                disabled={document.processing_status !== "ready"}
                onClick={() => onSelect(document.id)}
                className="flex min-w-0 flex-1 items-center gap-3 rounded-lg text-left focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-sky-400 disabled:cursor-not-allowed disabled:opacity-60"
              >
                <span className="grid h-9 w-9 shrink-0 place-items-center rounded-lg border border-white/8 bg-white/5 text-[10px] font-semibold text-slate-400">
                  {extensionFor(document)}
                </span>
                <span className="min-w-0 flex-1">
                  <span
                    title={document.filename}
                    className="block truncate text-xs font-medium text-slate-200"
                  >
                    {document.filename}
                  </span>
                  <span className="mt-1 flex items-center gap-1.5 text-[11px] text-slate-500">
                    <span
                      className={cn(
                        "h-1.5 w-1.5 rounded-full",
                        document.processing_status === "ready"
                          ? "bg-emerald-400"
                          : document.processing_status === "failed"
                            ? "bg-rose-400"
                            : "animate-pulse bg-amber-400",
                      )}
                    />
                    {document.processing_status === "ready"
                      ? `${formatBytes(document.file_size)} · ${document.chunk_count} sources${sessionDocumentIds.includes(document.id) ? " · This tab" : ""}`
                      : document.processing_status}
                  </span>
                </span>
              </button>
              {(!demoMode || sessionDocumentIds.includes(document.id)) && (
                <button
                  type="button"
                  onClick={() => setPendingDelete(document)}
                  aria-label={`Delete ${document.filename}`}
                  className="rounded-lg p-2 text-slate-600 opacity-70 transition hover:bg-rose-400/10 hover:text-rose-300 focus-visible:opacity-100 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-rose-400 group-hover:opacity-100"
                >
                  <Trash2 className="h-3.5 w-3.5" />
                </button>
              )}
            </div>
          ))}
        </div>
      </div>

      {pendingDelete && (
        <div
          className="fixed inset-0 z-50 grid place-items-center bg-black/70 p-4"
          role="dialog"
          aria-modal="true"
          aria-labelledby="delete-title"
        >
          <div className="w-full max-w-md rounded-2xl border border-white/10 bg-[#11161e] p-5 shadow-2xl">
            <div className="flex items-start justify-between gap-4">
              <div>
                <h2 id="delete-title" className="font-semibold">
                  {sessionDocumentIds.includes(pendingDelete.id)
                    ? "Remove uploaded document?"
                    : "Delete document?"}
                </h2>
                <p className="mt-2 break-words text-sm leading-6 text-slate-400">
                  This removes{" "}
                  <strong className="text-slate-200">
                    {pendingDelete.filename}
                  </strong>
                  {sessionDocumentIds.includes(pendingDelete.id)
                    ? " and its extracted content from this browser tab."
                    : ", its source file, metadata, chunks, and scoped vectors."}
                </p>
              </div>
              <button
                type="button"
                onClick={() => setPendingDelete(null)}
                aria-label="Close confirmation"
                className="rounded-lg p-1 text-slate-400 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-sky-400"
              >
                <X className="h-4 w-4" />
              </button>
            </div>
            <div className="mt-5 flex justify-end gap-2">
              <button
                type="button"
                onClick={() => setPendingDelete(null)}
                className="rounded-lg border border-white/10 px-4 py-2 text-sm text-slate-300 hover:bg-white/5 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-sky-400"
              >
                Cancel
              </button>
              <button
                type="button"
                onClick={() => {
                  onDelete(pendingDelete.id);
                  setPendingDelete(null);
                }}
                className="rounded-lg bg-rose-500 px-4 py-2 text-sm font-semibold text-white hover:bg-rose-400 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-rose-300"
              >
                {sessionDocumentIds.includes(pendingDelete.id)
                  ? "Remove from tab"
                  : "Delete everywhere"}
              </button>
            </div>
          </div>
        </div>
      )}
    </aside>
  );
}
