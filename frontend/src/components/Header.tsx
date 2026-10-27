import { DatabaseZap, ShieldCheck } from "lucide-react";
import type { Readiness } from "../types/documents";

export function Header({ readiness }: { readiness: Readiness | null }) {
  const ready = readiness?.status === "ready";
  return (
    <header className="flex min-h-16 items-center justify-between gap-4 border-b border-white/8 bg-[#0c1016] px-4 py-3 sm:px-6">
      <div className="flex items-center gap-3">
        <div className="grid h-9 w-9 place-items-center rounded-xl border border-sky-400/20 bg-sky-400/10">
          <DatabaseZap className="h-4 w-4 text-sky-300" />
        </div>
        <div>
          <h1 className="text-sm font-semibold tracking-tight sm:text-base">
            ClientOps Copilot
          </h1>
          <p className="hidden text-xs text-slate-500 sm:block">
            Grounded client knowledge workspace · v1.6
          </p>
        </div>
      </div>
      <div className="flex items-center gap-2">
        {readiness?.demo_mode && (
          <span className="hidden items-center gap-1.5 rounded-full border border-violet-400/20 bg-violet-400/8 px-3 py-1.5 text-xs text-violet-200 sm:flex">
            <ShieldCheck className="h-3.5 w-3.5" /> Public demo
          </span>
        )}
        <div
          aria-live="polite"
          className={`flex shrink-0 items-center gap-2 rounded-full border px-3 py-1.5 text-xs ${ready ? "border-emerald-400/20 bg-emerald-400/8 text-emerald-200" : "border-amber-400/20 bg-amber-400/8 text-amber-200"}`}
        >
          <span
            className={`h-1.5 w-1.5 rounded-full ${ready ? "bg-emerald-300" : "bg-amber-300"}`}
          />
          {readiness === null
            ? "Connecting"
            : ready
              ? "Systems ready"
              : "Setup needed"}
        </div>
      </div>
    </header>
  );
}
