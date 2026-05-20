import type { Citation } from "../types/documents";

type CitationListProps = {
  citations: Citation[];
};

export function CitationList({ citations }: CitationListProps) {
  if (!citations.length) return null;

  return (
    <div className="mt-5 space-y-3">
      <p className="text-xs uppercase tracking-[0.2em] text-white/35">
        Source citations
      </p>

      {citations.map((citation) => (
        <article
          key={`${citation.source}-${citation.chunk_index}`}
          className="rounded-2xl border border-white/10 bg-black/20 p-4"
        >
          <div className="mb-2 flex items-center justify-between gap-3">
            <p className="text-sm font-medium">
              {citation.source} · chunk {citation.chunk_index}
            </p>
            <span className="rounded-full bg-cyan-300/10 px-3 py-1 text-xs text-cyan-200">
              {citation.score}
            </span>
          </div>

          <p className="text-sm leading-6 text-white/55">{citation.preview}</p>
        </article>
      ))}
    </div>
  );
}