import type { ReactNode } from "react";

type AppShellProps = {
  children: ReactNode;
};

export function AppShell({ children }: AppShellProps) {
  return (
    <main className="min-h-screen overflow-x-hidden bg-[#0a0d12] text-slate-100">
      <div className="mx-auto flex min-h-screen max-w-[1800px] flex-col">
        {children}
      </div>
    </main>
  );
}
