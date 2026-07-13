import { BrainCircuit } from "lucide-react";
import type { Readiness } from "../types/documents";

export function Header({ readiness }: { readiness: Readiness | null }) {
  const ready = readiness?.status === "ready";
  return (
    <header className="mb-8 flex items-center justify-between gap-4">
      <div className="flex items-center gap-3">
        <div className="grid h-11 w-11 place-items-center rounded-2xl border border-white/10 bg-white/10">
          <BrainCircuit className="h-5 w-5 text-cyan-300" />
        </div>
        <div>
          <p className="text-sm text-white/50">ClientOps Copilot · v1.5</p>
          <h1 className="text-xl font-semibold tracking-tight">
            Source-grounded client knowledge workspace
          </h1>
        </div>
      </div>
      <div
        aria-live="polite"
        className={`shrink-0 rounded-full border px-3 py-2 text-xs sm:px-4 sm:text-sm ${ready ? "border-emerald-400/20 bg-emerald-400/10 text-emerald-200" : "border-amber-400/20 bg-amber-400/10 text-amber-200"}`}
      >
        {readiness === null
          ? "Checking backend…"
          : ready
            ? "Backend ready"
            : "Backend not ready"}
      </div>
    </header>
  );
}
