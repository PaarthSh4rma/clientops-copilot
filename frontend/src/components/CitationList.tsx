import { BookOpenText } from "lucide-react";
import type { Citation } from "../types/documents";

function sourceLabel(citation: Citation) {
  if (citation.page_number) return `Page ${citation.page_number}`;
  return citation.location || `Chunk ${citation.chunk_index + 1}`;
}

export function CitationList({
  citations,
  onInspect,
}: {
  citations: Citation[];
  onInspect: (citation: Citation) => void;
}) {
  if (!citations.length) return null;
  return (
    <div className="mt-4 flex flex-wrap gap-2" aria-label="Evidence used">
      {citations.map((citation, index) => (
        <button
          type="button"
          key={citation.chunk_id}
          onClick={() => onInspect(citation)}
          className="inline-flex max-w-full items-center gap-2 rounded-lg border border-white/10 bg-white/[0.035] px-2.5 py-1.5 text-left text-[11px] text-slate-400 transition hover:border-sky-400/30 hover:text-sky-200 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-sky-400"
        >
          <BookOpenText className="h-3 w-3 shrink-0" />
          <span className="truncate">
            [{index + 1}] {sourceLabel(citation)}
          </span>
        </button>
      ))}
    </div>
  );
}
