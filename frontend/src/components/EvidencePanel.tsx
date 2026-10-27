import { ExternalLink, FileSearch, Gauge, X } from "lucide-react";
import type { Citation } from "../types/documents";
import { cn } from "../lib/cn";

function sourceLabel(citation: Citation) {
  return citation.page_number
    ? `Page ${citation.page_number}`
    : citation.location || `Chunk ${citation.chunk_index + 1}`;
}

function relevance(score: number) {
  if (score >= 0.75)
    return { label: "Strong match", color: "text-emerald-300" };
  if (score >= 0.5) return { label: "Relevant match", color: "text-sky-300" };
  return { label: "Supporting match", color: "text-amber-300" };
}

type Props = {
  citations: Citation[];
  active: Citation | null;
  open: boolean;
  onSelect: (citation: Citation) => void;
  onClose: () => void;
};

export function EvidencePanel({
  citations,
  active,
  open,
  onSelect,
  onClose,
}: Props) {
  const selected = active ?? citations[0] ?? null;
  const content = (
    <aside className="flex h-full min-h-0 flex-col bg-[#0c1016]">
      <div className="flex items-center justify-between border-b border-white/8 px-4 py-4">
        <div>
          <h2 className="text-sm font-semibold">Evidence inspector</h2>
          <p className="mt-0.5 text-xs text-slate-500">
            {citations.length
              ? `${citations.length} retrieved source${citations.length === 1 ? "" : "s"}`
              : "No source selected"}
          </p>
        </div>
        <button
          type="button"
          onClick={onClose}
          className="rounded-lg p-2 text-slate-400 hover:bg-white/5 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-sky-400 xl:hidden"
          aria-label="Close evidence inspector"
        >
          <X className="h-4 w-4" />
        </button>
      </div>
      {!selected ? (
        <div className="flex flex-1 flex-col items-center justify-center p-8 text-center">
          <div className="grid h-11 w-11 place-items-center rounded-xl bg-white/5">
            <FileSearch className="h-5 w-5 text-slate-500" />
          </div>
          <p className="mt-3 text-sm font-medium">Evidence appears here</p>
          <p className="mt-1 text-xs leading-5 text-slate-500">
            Ask a grounded question, then inspect the exact source passages
            without losing the conversation.
          </p>
        </div>
      ) : (
        <>
          <div className="border-b border-white/8 p-4">
            <p className="break-words text-sm font-medium text-slate-200">
              {selected.filename}
            </p>
            <div className="mt-2 flex flex-wrap items-center gap-2 text-xs">
              <span className="rounded-md border border-white/10 bg-white/5 px-2 py-1 text-slate-300">
                {sourceLabel(selected)}
              </span>
              <span
                className={cn(
                  "inline-flex items-center gap-1",
                  relevance(selected.relevance_score).color,
                )}
              >
                <Gauge className="h-3 w-3" />
                {relevance(selected.relevance_score).label}
              </span>
            </div>
            <p className="mt-2 font-mono text-[10px] text-slate-600">
              cosine similarity {selected.relevance_score.toFixed(3)} · chunk{" "}
              {selected.chunk_index + 1}
            </p>
          </div>
          <div className="min-h-0 flex-1 overflow-y-auto p-4">
            <p className="text-[10px] font-semibold uppercase tracking-[0.18em] text-slate-600">
              Retrieved passage
            </p>
            <blockquote className="mt-3 whitespace-pre-wrap break-words border-l-2 border-sky-400/40 pl-4 text-sm leading-7 text-slate-300">
              {selected.source_preview}
            </blockquote>
            <p className="mt-5 flex items-start gap-2 text-xs leading-5 text-slate-500">
              <ExternalLink className="mt-0.5 h-3 w-3 shrink-0" />
              This preview is the exact evidence sent to the answer provider.
              Original-file rendering is not available in this version.
            </p>
          </div>
          {citations.length > 1 && (
            <div className="max-h-48 overflow-y-auto border-t border-white/8 p-3">
              <p className="px-1 pb-2 text-[10px] font-semibold uppercase tracking-[0.18em] text-slate-600">
                All evidence
              </p>
              <div className="space-y-1">
                {citations.map((citation, index) => (
                  <button
                    type="button"
                    key={citation.chunk_id}
                    onClick={() => onSelect(citation)}
                    className={cn(
                      "flex w-full items-center justify-between gap-3 rounded-lg px-2.5 py-2 text-left text-xs focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-sky-400",
                      selected.chunk_id === citation.chunk_id
                        ? "bg-sky-400/10 text-sky-200"
                        : "text-slate-400 hover:bg-white/5",
                    )}
                  >
                    <span className="truncate">
                      [{index + 1}] {sourceLabel(citation)}
                    </span>
                    <span className="font-mono text-[10px] text-slate-600">
                      {citation.relevance_score.toFixed(2)}
                    </span>
                  </button>
                ))}
              </div>
            </div>
          )}
        </>
      )}
    </aside>
  );
  return (
    <>
      <div className="hidden min-h-0 border-l border-white/8 xl:block">
        {content}
      </div>
      {open && (
        <div
          className="fixed inset-0 z-40 bg-black/65 xl:hidden"
          onClick={onClose}
        >
          <div
            className="absolute inset-y-0 right-0 w-full max-w-sm border-l border-white/10 shadow-2xl"
            onClick={(event) => event.stopPropagation()}
          >
            {content}
          </div>
        </div>
      )}
    </>
  );
}
