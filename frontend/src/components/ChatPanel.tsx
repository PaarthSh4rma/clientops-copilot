import {
  AlertTriangle,
  ArrowUp,
  CalendarClock,
  CheckCircle2,
  ClipboardCheck,
  FileQuestion,
  ListChecks,
  PanelRightOpen,
  ShieldAlert,
  Sparkles,
} from "lucide-react";
import { useEffect, useRef, useState } from "react";
import type {
  Citation,
  ChatResponse,
  DocumentSummary,
} from "../types/documents";
import { CitationList } from "./CitationList";
import { Spinner } from "./ui/Spinner";

const ACTIONS = [
  {
    label: "Summarise",
    icon: Sparkles,
    prompt:
      "Summarise this document concisely. Focus on its purpose, scope, and most important details.",
  },
  {
    label: "Key decisions",
    icon: ClipboardCheck,
    prompt:
      "Extract the key decisions stated in this document. If a decision is ambiguous, say so.",
  },
  {
    label: "Risks & blockers",
    icon: ShieldAlert,
    prompt:
      "Identify risks, blockers, constraints, or unresolved concerns explicitly supported by this document.",
  },
  {
    label: "Action items",
    icon: ListChecks,
    prompt:
      "Extract action items or commitments in this document, including owners where the evidence names them.",
  },
  {
    label: "Dates",
    icon: CalendarClock,
    prompt:
      "Find important dates, deadlines, milestones, or time-bound commitments in this document.",
  },
] as const;

type Props = {
  selected: DocumentSummary | null;
  isLoading: boolean;
  history: ChatResponse[];
  onAsk: (question: string) => void;
  onInspect: (citation: Citation, citations: Citation[]) => void;
};

function Outcome({ response }: { response: ChatResponse }) {
  const config =
    response.status === "supported"
      ? {
          label: "Supported by evidence",
          icon: CheckCircle2,
          classes: "border-emerald-400/20 bg-emerald-400/8 text-emerald-200",
        }
      : response.status === "insufficient_evidence"
        ? {
            label: "Insufficient evidence",
            icon: FileQuestion,
            classes: "border-amber-400/20 bg-amber-400/8 text-amber-200",
          }
        : {
            label: "Provider unavailable",
            icon: AlertTriangle,
            classes: "border-rose-400/20 bg-rose-400/8 text-rose-200",
          };
  const Icon = config.icon;
  return (
    <span
      className={`inline-flex items-center gap-1.5 rounded-full border px-2.5 py-1 text-[10px] font-medium ${config.classes}`}
    >
      <Icon className="h-3 w-3" />
      {config.label}
    </span>
  );
}

export function ChatPanel({
  selected,
  isLoading,
  history,
  onAsk,
  onInspect,
}: Props) {
  const [question, setQuestion] = useState("");
  const bottomRef = useRef<HTMLDivElement>(null);
  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: "smooth", block: "nearest" });
  }, [history, isLoading]);

  function submit(questionToAsk: string) {
    const clean = questionToAsk.trim();
    if (!clean || !selected || isLoading) return;
    onAsk(clean);
    setQuestion("");
  }

  return (
    <section className="flex min-h-[620px] min-w-0 flex-col bg-[#0a0d12] lg:min-h-0">
      <div className="border-b border-white/8 px-4 py-4 sm:px-6">
        {selected ? (
          <div className="flex items-center justify-between gap-4">
            <div className="min-w-0">
              <p
                className="truncate text-sm font-semibold text-slate-100"
                title={selected.filename}
              >
                {selected.filename}
              </p>
              <p className="mt-1 text-xs text-slate-500">
                Questions and prompt actions are scoped to this document only
              </p>
            </div>
            <span className="hidden shrink-0 rounded-full border border-emerald-400/15 bg-emerald-400/[0.06] px-2.5 py-1 text-[10px] text-emerald-300 sm:block">
              Indexed · {selected.chunk_count} sources
            </span>
          </div>
        ) : (
          <div>
            <p className="text-sm font-semibold">Document workspace</p>
            <p className="mt-1 text-xs text-slate-500">
              Select an indexed document to begin
            </p>
          </div>
        )}
      </div>

      <div
        className="min-h-0 flex-1 overflow-y-auto px-4 py-5 sm:px-6"
        aria-live="polite"
        aria-busy={isLoading}
      >
        {!selected && (
          <div className="mx-auto flex h-full max-w-md flex-col items-center justify-center text-center">
            <div className="grid h-12 w-12 place-items-center rounded-2xl border border-white/8 bg-white/[0.035]">
              <FileQuestion className="h-5 w-5 text-slate-500" />
            </div>
            <h2 className="mt-4 text-base font-semibold">
              Choose a source document
            </h2>
            <p className="mt-2 text-sm leading-6 text-slate-500">
              The workspace keeps retrieval, answers, and citations strictly
              scoped to the document you select.
            </p>
          </div>
        )}
        {selected && history.length === 0 && !isLoading && (
          <div className="mx-auto flex h-full max-w-2xl flex-col justify-center py-8">
            <p className="text-xs font-medium uppercase tracking-[0.18em] text-sky-300">
              Start with a client workflow
            </p>
            <h2 className="mt-3 text-2xl font-semibold tracking-tight text-slate-100 sm:text-3xl">
              Turn source material into an answer you can verify.
            </h2>
            <p className="mt-3 max-w-xl text-sm leading-6 text-slate-500">
              Use a transparent prompt action or ask your own question. Every
              answer must clear the relevance threshold before the LLM is
              called.
            </p>
            <div className="mt-6 grid gap-2 sm:grid-cols-2">
              {ACTIONS.map(({ label, icon: Icon, prompt }) => (
                <button
                  type="button"
                  key={label}
                  onClick={() => submit(prompt)}
                  className="flex items-center gap-3 rounded-xl border border-white/8 bg-white/[0.025] px-4 py-3 text-left text-sm text-slate-300 transition hover:border-sky-400/20 hover:bg-sky-400/[0.05] focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-sky-400"
                >
                  <Icon className="h-4 w-4 shrink-0 text-sky-300" />
                  {label}
                </button>
              ))}
            </div>
          </div>
        )}
        {selected && history.length > 0 && (
          <div className="mx-auto max-w-3xl space-y-7">
            {history.map((response, index) => (
              <article key={`${response.question}-${index}`}>
                <div className="flex justify-end">
                  <p className="max-w-[88%] break-words rounded-2xl rounded-br-md bg-slate-800 px-4 py-3 text-sm leading-6 text-slate-200">
                    {response.question}
                  </p>
                </div>
                <div className="mt-3 rounded-2xl border border-white/8 bg-[#10151d] p-4 sm:p-5">
                  <div className="mb-3 flex flex-wrap items-center justify-between gap-2">
                    <p className="text-[10px] font-semibold uppercase tracking-[0.18em] text-slate-500">
                      Grounded response
                    </p>
                    <Outcome response={response} />
                  </div>
                  <p className="whitespace-pre-wrap break-words text-sm leading-7 text-slate-300">
                    {response.answer}
                  </p>
                  <CitationList
                    citations={response.citations}
                    onInspect={(citation) =>
                      onInspect(citation, response.citations)
                    }
                  />
                </div>
              </article>
            ))}
          </div>
        )}
        {isLoading && (
          <div className="mx-auto mt-5 flex max-w-3xl items-center gap-3 rounded-xl border border-sky-400/10 bg-sky-400/[0.04] p-4 text-sm text-slate-400">
            <Spinner />
            <span>Retrieving scoped evidence and preparing the answer…</span>
          </div>
        )}
        <div ref={bottomRef} />
      </div>

      <div className="border-t border-white/8 bg-[#0c1016] p-3 sm:p-4">
        {selected && history.length > 0 && (
          <div className="workflow-scroll mx-auto mb-2 flex max-w-3xl gap-1 overflow-x-auto pb-1">
            {ACTIONS.map(({ label, icon: Icon, prompt }) => (
              <button
                type="button"
                key={label}
                disabled={isLoading}
                onClick={() => submit(prompt)}
                className="inline-flex shrink-0 items-center gap-1.5 rounded-lg px-2.5 py-1.5 text-[11px] text-slate-500 transition hover:bg-white/5 hover:text-slate-300 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-sky-400"
              >
                <Icon className="h-3 w-3" />
                {label}
              </button>
            ))}
          </div>
        )}
        <form
          onSubmit={(event) => {
            event.preventDefault();
            submit(question);
          }}
          className="mx-auto flex max-w-3xl items-end gap-2 rounded-2xl border border-white/10 bg-[#111720] p-2 focus-within:border-sky-400/30 focus-within:ring-2 focus-within:ring-sky-400/10"
        >
          <textarea
            value={question}
            onChange={(event) => setQuestion(event.target.value)}
            onKeyDown={(event) => {
              if (event.key === "Enter" && !event.shiftKey) {
                event.preventDefault();
                submit(question);
              }
            }}
            disabled={!selected || isLoading}
            rows={1}
            maxLength={2000}
            aria-label="Question about selected document"
            placeholder={
              selected
                ? "Ask a grounded question…"
                : "Select a document to ask a question"
            }
            className="max-h-32 min-h-10 min-w-0 flex-1 resize-none bg-transparent px-2 py-2 text-sm leading-5 text-slate-200 outline-none placeholder:text-slate-600 disabled:cursor-not-allowed"
          />
          <button
            type="submit"
            disabled={!selected || isLoading || !question.trim()}
            aria-label="Ask question"
            className="grid h-9 w-9 shrink-0 place-items-center rounded-xl bg-sky-300 text-slate-950 transition hover:bg-sky-200 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-sky-300 disabled:cursor-not-allowed disabled:opacity-30"
          >
            {isLoading ? <Spinner /> : <ArrowUp className="h-4 w-4" />}
          </button>
        </form>
        <div className="mx-auto mt-2 flex max-w-3xl items-center justify-between gap-3 px-1 text-[10px] text-slate-600">
          <span>Answers are limited to retrieved evidence.</span>
          <button
            type="button"
            disabled={!history.at(-1)?.citations.length}
            onClick={() => {
              const latest = history.at(-1);
              if (latest?.citations[0])
                onInspect(latest.citations[0], latest.citations);
            }}
            className="inline-flex items-center gap-1 text-slate-500 hover:text-sky-300 disabled:hidden focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-sky-400"
          >
            <PanelRightOpen className="h-3 w-3" />
            Evidence
          </button>
        </div>
      </div>
    </section>
  );
}
