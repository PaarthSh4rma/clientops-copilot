import { FileText, UploadCloud } from "lucide-react";
import type { UploadedDocument } from "../types/documents";
import { StatusBadge } from "./StatusBadge";

type UploadCardProps = {
  document: UploadedDocument | null;
  isUploading: boolean;
  onUpload: (file: File) => void;
};

export function UploadCard({ document, isUploading, onUpload }: UploadCardProps) {
  return (
    <section className="rounded-3xl border border-white/10 bg-white/[0.06] p-6 shadow-2xl shadow-black/30 backdrop-blur-xl">
      <div className="mb-6 flex items-start justify-between gap-4">
        <div>
          <p className="text-sm text-cyan-200">Step 1</p>
          <h2 className="mt-1 text-2xl font-semibold">Upload knowledge</h2>
          <p className="mt-2 max-w-xl text-sm leading-6 text-white/55">
            Upload a text document and the backend will extract, chunk and embed it
            using the local semantic engine.
          </p>
        </div>

        <FileText className="h-6 w-6 text-white/40" />
      </div>

      <label className="group flex cursor-pointer flex-col items-center justify-center rounded-3xl border border-dashed border-white/15 bg-black/20 px-6 py-10 text-center transition hover:border-cyan-300/50 hover:bg-cyan-300/5">
        <UploadCloud className="mb-4 h-9 w-9 text-cyan-200" />
        <span className="text-sm font-medium">
          {isUploading ? "Uploading..." : "Drop in a file"}
        </span>
        <span className="mt-1 text-xs text-white/40">
          Supports TXT, PDF, and DOCX documents
        </span>

        <input
          type="file"
          accept=".txt,.pdf,.docx"
          className="hidden"
          disabled={isUploading}
          onChange={(event) => {
            const file = event.target.files?.[0];
            if (file) onUpload(file);
          }}
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
    </section>
  );
}