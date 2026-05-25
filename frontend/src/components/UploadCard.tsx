import { FileText, UploadCloud } from "lucide-react";
import { useState } from "react";
import type { UploadedDocument } from "../types/documents";
import { Card } from "./ui/Card";
import { Spinner } from "./ui/Spinner";
import { StatusBadge } from "./StatusBadge";
import { cn } from "../lib/cn";

type UploadCardProps = {
  document: UploadedDocument | null;
  isUploading: boolean;
  onUpload: (file: File) => void;
};

export function UploadCard({ document, isUploading, onUpload }: UploadCardProps) {
  const [isDragging, setIsDragging] = useState(false);

  function handleFile(file?: File) {
    if (!file || isUploading) return;
    onUpload(file);
  }

  return (
    <Card>
      <div className="mb-6 flex items-start justify-between gap-4">
        <div>
          <p className="text-sm text-cyan-200">Step 1</p>
          <h2 className="mt-1 text-2xl font-semibold">Upload knowledge</h2>
          <p className="mt-2 max-w-xl text-sm leading-6 text-white/55">
            Upload a business document and ClientOps will extract, chunk, embed,
            and persist it for grounded retrieval.
          </p>
        </div>

        <FileText className="h-6 w-6 text-white/40" />
      </div>

      <label
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
          "group flex cursor-pointer flex-col items-center justify-center rounded-3xl border border-dashed px-6 py-10 text-center transition",
          "bg-black/20 hover:border-cyan-300/50 hover:bg-cyan-300/5",
          isDragging
            ? "border-cyan-300/70 bg-cyan-300/10"
            : "border-white/15",
        )}
      >
        {isUploading ? (
          <div className="mb-4 grid h-10 w-10 place-items-center rounded-full bg-cyan-300">
            <Spinner />
          </div>
        ) : (
          <UploadCloud className="mb-4 h-9 w-9 text-cyan-200" />
        )}

        <span className="text-sm font-medium">
          {isUploading ? "Ingesting document..." : "Drop in a file"}
        </span>
        <span className="mt-1 text-xs text-white/40">
          Supports TXT, PDF, and DOCX documents
        </span>

        <input
          type="file"
          accept=".txt,.pdf,.docx"
          className="hidden"
          disabled={isUploading}
          onChange={(event) => handleFile(event.target.files?.[0])}
        />
      </label>

      {document && (
        <div className="mt-6 space-y-4">
          <div>
            <p className="text-sm text-white/40">Active document</p>
            <p className="mt-1 font-medium">{document.filename}</p>
          </div>

          <div className="grid gap-3 sm:grid-cols-3">
            <StatusBadge label="Chunks" value={document.chunk_count} />
            <StatusBadge label="Embedded" value={document.embedded_chunk_count} />
            <StatusBadge label="Dimensions" value={document.embedding_dimensions} />
          </div>

          <div className="rounded-2xl border border-white/10 bg-black/20 p-4">
            <p className="mb-2 text-xs uppercase tracking-[0.2em] text-white/35">
              Preview
            </p>
            <p className="line-clamp-5 text-sm leading-6 text-white/60">
              {document.preview}
            </p>
          </div>
        </div>
      )}
    </Card>
  );
}