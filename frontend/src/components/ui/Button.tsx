import type { ButtonHTMLAttributes, ReactNode } from "react";
import { cn } from "../../lib/cn";

type ButtonProps = ButtonHTMLAttributes<HTMLButtonElement> & {
  children: ReactNode;
};

export function Button({ children, className, ...props }: ButtonProps) {
  return (
    <button
      className={cn(
        "inline-flex items-center justify-center gap-2 rounded-2xl bg-cyan-300 px-5 py-3 text-sm font-semibold text-slate-950 transition",
        "hover:bg-cyan-200 disabled:cursor-not-allowed disabled:opacity-40",
        "focus:outline-none focus:ring-2 focus:ring-cyan-300/40",
        className,
      )}
      {...props}
    >
      {children}
    </button>
  );
}
