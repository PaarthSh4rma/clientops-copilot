import { BrainCircuit } from "lucide-react";

export function Header() {
  return (
    <header className="mb-8 flex items-center justify-between">
      <div className="flex items-center gap-3">
        <div className="grid h-11 w-11 place-items-center rounded-2xl border border-white/10 bg-white/10 shadow-2xl shadow-blue-500/10">
          <BrainCircuit className="h-5 w-5 text-cyan-300" />
        </div>

        <div>
          <p className="text-sm text-white/50">ClientOps Copilot</p>
          <h1 className="text-xl font-semibold tracking-tight">
            AI knowledge ops for modern teams
          </h1>
        </div>
      </div>

      <div className="hidden rounded-full border border-emerald-400/20 bg-emerald-400/10 px-4 py-2 text-sm text-emerald-200 md:block">
        Local RAG Engine Online
      </div>
    </header>
  );
}