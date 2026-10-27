import { AlertCircle, CheckCircle2 } from "lucide-react";

type ToastProps = {
  type: "success" | "error";
  message: string;
};

export function Toast({ type, message }: ToastProps) {
  const isSuccess = type === "success";

  return (
    <div
      role={isSuccess ? "status" : "alert"}
      className={
        isSuccess
          ? "flex items-center gap-3 rounded-xl border border-emerald-400/20 bg-[#102019] px-4 py-3 text-sm text-emerald-100 shadow-xl"
          : "flex items-center gap-3 rounded-xl border border-red-400/20 bg-[#241316] px-4 py-3 text-sm text-red-100 shadow-xl"
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
