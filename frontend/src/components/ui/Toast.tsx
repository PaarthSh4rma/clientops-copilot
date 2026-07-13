import { AlertCircle, CheckCircle2 } from "lucide-react";

type ToastProps = {
  type: "success" | "error";
  message: string;
};

export function Toast({ type, message }: ToastProps) {
  const isSuccess = type === "success";

  return (
    <div
      className={
        isSuccess
          ? "mb-5 flex items-center gap-3 rounded-2xl border border-emerald-400/20 bg-emerald-400/10 px-4 py-3 text-sm text-emerald-100"
          : "mb-5 flex items-center gap-3 rounded-2xl border border-red-400/20 bg-red-400/10 px-4 py-3 text-sm text-red-100"
      }
    >
      {isSuccess ? (
        <CheckCircle2 className="h-4 w-4" />
      ) : (
        <AlertCircle className="h-4 w-4" />
      )}
      {message}
    </div>
  );
}
