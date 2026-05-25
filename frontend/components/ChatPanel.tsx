import { SendHorizonal, Sparkles } from "lucide-react";
import { useState } from "react";
import type { ChatResponse } from "../types/documents";
import { CitationList } from "./CitationList";

type ChatPanelProps = {
  disabled: boolean;
  isLoading: boolean;
  response: ChatResponse | null;
  onAsk: (question: string) => void;
};

export function ChatPanel({ disabled, isLoading, response, onAsk }: ChatPanelProps) {
  const [question, setQuestion] = useState("");

  function handleSubmit(event: React.FormEvent<HTMLFormElement>) {
    event.preventDefault();
    if (!question.trim()) return;

    onAsk(question.trim());
  }

  return (
    <section className="rounded-3xl border border-white/10 bg-white/[0.06] p-6 shadow-2xl shadow-black/30 backdrop-blur-xl">
      <div className="mb-6 flex items-start justify-between gap-4">
        <div>
          <p className="text-sm text-cyan-200">Step 2</p>
          <h2 className="mt-1 text-2xl font-semibold">Ask grounded questions</h2>
          <p className="mt-2 max-w-xl text-sm leading-6 text-white/55">
            Query the uploaded knowledge base and receive an answer backed by retrieved
            chunks and similarity scores.
          </p>
        </div>

        <Sparkles className="h-6 w-6 text-white/40" />
      </div>

      <form onSubmit={handleSubmit} className="flex gap-3">
        <input
          value={question}
          disabled={disabled || isLoading}
          onChange={(event) => setQuestion(event.target.value)}
          placeholder={
            disabled
              ? "Upload a document first..."
              : "Ask something about the document..."
          }
          className="min-w-0 flex-1 rounded-2xl border border-white/10 bg-black/30 px-4 py-3 text-sm text-white outline-none transition placeholder:text-white/30 focus:border-cyan-300/50"
        />

        <button
          type="submit"
          disabled={disabled || isLoading}
          className="inline-flex items-center gap-2 rounded-2xl bg-cyan-300 px-5 py-3 text-sm font-semibold text-slate-950 transition hover:bg-cyan-200 disabled:cursor-not-allowed disabled:opacity-40"
        >
          <SendHorizonal className="h-4 w-4" />
          Ask
        </button>
      </form>

      {isLoading && (
        <div className="mt-6 rounded-2xl border border-white/10 bg-black/20 p-5 text-sm text-white/50">
          Retrieving relevant chunks...
        </div>
      )}

      {response && (
        <div className="mt-6">
          <div className="rounded-2xl border border-cyan-300/15 bg-cyan-300/5 p-5">
            <p className="mb-2 text-xs uppercase tracking-[0.2em] text-cyan-200/70">
              Grounded answer
            </p>
            <span className="rounded-full bg-white/10 px-3 py-1 text-xs text-white/50">
            {response.answer_mode === "llm" ? "LLM generated" : "Fallback mode"}
            </span>
            <p className="whitespace-pre-line text-sm leading-7 text-white/75">
              {response.answer}
            </p>
          </div>

          <CitationList citations={response.citations} />
        </div>
      )}
    </section>
  );
}