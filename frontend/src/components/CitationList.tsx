import type { Citation } from "../types/documents";

export function CitationList({ citations }: { citations: Citation[] }) {
  if (!citations.length) return null;
  return (
    <div className="mt-5 space-y-3">
      <p className="text-xs uppercase tracking-[0.2em] text-white/35">
        Sources used
      </p>
      {citations.map((citation) => (
        <article
          key={citation.chunk_id}
          className="rounded-2xl border border-white/10 bg-black/20 p-4"
        >
          <div className="mb-2 flex items-center justify-between gap-3">
            <p className="text-sm font-medium">
              {citation.filename} ·{" "}
              {citation.page_number
                ? `page ${citation.page_number}`
                : citation.location || `chunk ${citation.chunk_index + 1}`}
            </p>
            <span className="rounded-full bg-cyan-300/10 px-3 py-1 text-xs text-cyan-200">
              {citation.relevance_score.toFixed(3)}
            </span>
          </div>
          <p className="text-sm leading-6 text-white/55">
            {citation.source_preview}
          </p>
        </article>
      ))}
    </div>
  );
}
