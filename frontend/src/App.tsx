import { useEffect, useMemo, useState } from "react";
import {
  ApiError,
  chatWithDocument,
  deleteDocument,
  getReadiness,
  listDocuments,
  uploadDocument,
} from "../api/client";
import { AppShell } from "./components/AppShell";
import { ChatPanel } from "./components/ChatPanel";
import { EvidencePanel } from "./components/EvidencePanel";
import { Header } from "./components/Header";
import { UploadCard } from "./components/UploadCard";
import { Toast } from "./components/ui/Toast";
import type {
  Citation,
  ChatResponse,
  DocumentSummary,
  Readiness,
} from "./types/documents";

const FALLBACK_READINESS: Readiness = {
  status: "not_ready",
  dependencies: {},
  limits: { max_upload_size_bytes: 10 * 1024 * 1024 },
  demo_mode: false,
  capabilities: { upload: true, delete: true, grounded_chat: true },
};

function App() {
  const [documents, setDocuments] = useState<DocumentSummary[]>([]);
  const [selectedId, setSelectedId] = useState<string | null>(null);
  const [history, setHistory] = useState<Record<string, ChatResponse[]>>({});
  const [readiness, setReadiness] = useState<Readiness | null>(null);
  const [backendAvailable, setBackendAvailable] = useState(true);
  const [isLoadingDocuments, setIsLoadingDocuments] = useState(true);
  const [isUploading, setIsUploading] = useState(false);
  const [isAsking, setIsAsking] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [success, setSuccess] = useState<string | null>(null);
  const [activeCitation, setActiveCitation] = useState<Citation | null>(null);
  const [activeCitations, setActiveCitations] = useState<Citation[]>([]);
  const [evidenceOpen, setEvidenceOpen] = useState(false);

  const selected = useMemo(
    () => documents.find((document) => document.id === selectedId) ?? null,
    [documents, selectedId],
  );
  const selectedHistory = selectedId ? (history[selectedId] ?? []) : [];

  useEffect(() => {
    Promise.allSettled([listDocuments(), getReadiness()]).then(
      ([docs, ready]) => {
        if (docs.status === "fulfilled") {
          setDocuments(docs.value);
          setSelectedId(
            docs.value.find(
              (document) => document.processing_status === "ready",
            )?.id ?? null,
          );
          setBackendAvailable(true);
        } else {
          setBackendAvailable(false);
          setError(
            "Could not reach the API. Start the backend and refresh the page.",
          );
        }
        setReadiness(
          ready.status === "fulfilled" ? ready.value : FALLBACK_READINESS,
        );
        setIsLoadingDocuments(false);
      },
    );
  }, []);

  function clearNotices() {
    setError(null);
    setSuccess(null);
  }

  async function handleUpload(file: File) {
    clearNotices();
    setIsUploading(true);
    try {
      const uploaded = await uploadDocument(file);
      setDocuments((current) => [uploaded, ...current]);
      selectDocument(uploaded.id);
      setSuccess(`${uploaded.filename} is indexed and ready.`);
    } catch (caught) {
      if (
        caught instanceof ApiError &&
        caught.detail?.code === "duplicate_document"
      ) {
        const existingId = String(caught.detail.document_id ?? "");
        if (existingId) selectDocument(existingId);
        setError(`${caught.message}. The existing document has been selected.`);
      } else
        setError(
          caught instanceof Error
            ? caught.message
            : "Upload failed. Check the file and try again.",
        );
    } finally {
      setIsUploading(false);
    }
  }

  async function handleDelete(id: string) {
    clearNotices();
    try {
      await deleteDocument(id);
      const remaining = documents.filter((document) => document.id !== id);
      setDocuments(remaining);
      setHistory((current) => {
        const next = { ...current };
        delete next[id];
        return next;
      });
      if (selectedId === id)
        selectDocument(
          remaining.find((document) => document.processing_status === "ready")
            ?.id ?? null,
        );
      setSuccess("Document and its indexed evidence were deleted.");
    } catch (caught) {
      setError(
        caught instanceof Error
          ? caught.message
          : "Deletion failed. Retry to complete cleanup.",
      );
    }
  }

  async function handleAsk(question: string) {
    if (!selected) return;
    clearNotices();
    setIsAsking(true);
    try {
      const response = await chatWithDocument({
        documentId: selected.id,
        question,
      });
      setHistory((current) => ({
        ...current,
        [selected.id]: [...(current[selected.id] ?? []), response],
      }));
      if (response.citations[0]) {
        setActiveCitation(response.citations[0]);
        setActiveCitations(response.citations);
      } else {
        setActiveCitation(null);
        setActiveCitations([]);
      }
    } catch (caught) {
      setError(
        caught instanceof Error
          ? caught.message
          : "The question could not be completed. Try again.",
      );
    } finally {
      setIsAsking(false);
    }
  }

  function selectDocument(id: string | null) {
    setSelectedId(id);
    const latestWithEvidence = id
      ? [...(history[id] ?? [])].reverse().find((item) => item.citations.length)
      : undefined;
    setActiveCitations(latestWithEvidence?.citations ?? []);
    setActiveCitation(latestWithEvidence?.citations[0] ?? null);
    setEvidenceOpen(false);
  }

  function inspectEvidence(citation: Citation, citations: Citation[]) {
    setActiveCitation(citation);
    setActiveCitations(citations);
    setEvidenceOpen(true);
  }

  return (
    <AppShell>
      <Header readiness={readiness} />
      <div className="relative min-h-0 flex-1">
        <div
          className="pointer-events-none absolute inset-x-0 top-3 z-30 mx-auto flex max-w-lg flex-col gap-2 px-4"
          aria-live="polite"
        >
          {error && (
            <div className="pointer-events-auto">
              <Toast type="error" message={error} />
            </div>
          )}
          {success && (
            <div className="pointer-events-auto">
              <Toast type="success" message={success} />
            </div>
          )}
        </div>
        <div className="grid min-h-[calc(100vh-4rem)] grid-cols-1 lg:h-[calc(100vh-4rem)] lg:grid-cols-[290px_minmax(0,1fr)] xl:grid-cols-[300px_minmax(0,1fr)_340px]">
          <UploadCard
            documents={documents}
            selectedId={selectedId}
            isLoading={isLoadingDocuments}
            isUploading={isUploading}
            maxUploadSize={
              readiness?.limits.max_upload_size_bytes ??
              FALLBACK_READINESS.limits.max_upload_size_bytes
            }
            demoMode={readiness?.demo_mode ?? false}
            backendAvailable={backendAvailable}
            onUpload={handleUpload}
            onSelect={selectDocument}
            onDelete={handleDelete}
          />
          <ChatPanel
            selected={selected}
            isLoading={isAsking}
            history={selectedHistory}
            onAsk={handleAsk}
            onInspect={inspectEvidence}
          />
          <EvidencePanel
            citations={activeCitations}
            active={activeCitation}
            open={evidenceOpen}
            onSelect={setActiveCitation}
            onClose={() => setEvidenceOpen(false)}
          />
        </div>
      </div>
    </AppShell>
  );
}

export default App;
