import { SendHorizonal, Sparkles } from "lucide-react";
import { useState } from "react";
import type { ChatResponse } from "../types/documents";
import { Button } from "./ui/Button";
import { Card } from "./ui/Card";
import { Spinner } from "./ui/Spinner";
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
    <Card>
      <div className="mb-6 flex items-start justify-between gap-4">
        <div>
          <p className="text-sm text-cyan-200">Step 2</p>
          <h2 className="mt-1 text-2xl font-semibold">Ask grounded questions</h2>
          <p className="mt-2 max-w-xl text-sm leading-6 text-white/55">
            Query the uploaded knowledge base and receive an answer generated from
            retrieved chunks with citations.
          </p>
        </div>

        <Sparkles className="h-6 w-6 text-white/40" />
      </div>

      <form onSubmit={handleSubmit} className="flex flex-col gap-3 sm:flex-row">
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

        <Button type="submit" disabled={disabled || isLoading}>
          {isLoading ? <Spinner /> : <SendHorizonal className="h-4 w-4" />}
          {isLoading ? "Thinking" : "Ask"}
        </Button>
      </form>

      {isLoading && (
        <div className="mt-6 rounded-2xl border border-white/10 bg-black/20 p-5 text-sm text-white/50">
          Retrieving relevant chunks and generating a grounded answer...
        </div>
      )}

      {response && (
        <div className="mt-6">
          <div className="rounded-2xl border border-cyan-300/15 bg-cyan-300/5 p-5">
            <div className="mb-3 flex items-center justify-between gap-3">
              <p className="text-xs uppercase tracking-[0.2em] text-cyan-200/70">
                Grounded answer
              </p>

              {response.answer_mode && (
                <span className="rounded-full bg-white/10 px-3 py-1 text-xs text-white/50">
                  {response.answer_mode === "llm" ? "LLM generated" : "Fallback"}
                </span>
              )}
            </div>

            <p className="whitespace-pre-line text-sm leading-7 text-white/75">
              {response.answer}
            </p>
          </div>

          <CitationList citations={response.citations} />
        </div>
      )}
    </Card>
  );
}