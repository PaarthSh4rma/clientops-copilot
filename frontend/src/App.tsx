import { useEffect, useState } from "react";
import {
  chatWithDocument,
  deleteDocument,
  getReadiness,
  listDocuments,
  uploadDocument,
} from "../api/client";
import { AppShell } from "./components/AppShell";
import { ChatPanel } from "./components/ChatPanel";
import { Header } from "./components/Header";
import { UploadCard } from "./components/UploadCard";
import { Toast } from "./components/ui/Toast";
import type {
  ChatResponse,
  DocumentSummary,
  Readiness,
} from "./types/documents";

function App() {
  const [documents, setDocuments] = useState<DocumentSummary[]>([]);
  const [selectedId, setSelectedId] = useState<string | null>(null);
  const [chatResponse, setChatResponse] = useState<ChatResponse | null>(null);
  const [readiness, setReadiness] = useState<Readiness | null>(null);
  const [isLoadingDocuments, setIsLoadingDocuments] = useState(true);
  const [isUploading, setIsUploading] = useState(false);
  const [isAsking, setIsAsking] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [success, setSuccess] = useState<string | null>(null);
  const selected =
    documents.find((document) => document.id === selectedId) ?? null;

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
        } else setError("Could not load the document library.");
        setReadiness(
          ready.status === "fulfilled"
            ? ready.value
            : {
                status: "not_ready",
                dependencies: {},
                limits: { max_upload_size_bytes: 10 * 1024 * 1024 },
              },
        );
        setIsLoadingDocuments(false);
      },
    );
  }, []);

  async function handleUpload(file: File) {
    setError(null);
    setSuccess(null);
    setIsUploading(true);
    try {
      const uploaded = await uploadDocument(file);
      setDocuments((current) => [uploaded, ...current]);
      setSelectedId(uploaded.id);
      setChatResponse(null);
      setSuccess("Document indexed successfully.");
    } catch (err) {
      setError(err instanceof Error ? err.message : "Upload failed");
    } finally {
      setIsUploading(false);
    }
  }

  async function handleDelete(id: string) {
    if (
      !window.confirm(
        "Delete this document, its chunks, vectors, and source file?",
      )
    )
      return;
    setError(null);
    try {
      await deleteDocument(id);
      const remaining = documents.filter((doc) => doc.id !== id);
      setDocuments(remaining);
      if (selectedId === id) {
        setSelectedId(
          remaining.find((document) => document.processing_status === "ready")
            ?.id ?? null,
        );
        setChatResponse(null);
      }
      setSuccess("Document deleted.");
    } catch (err) {
      setError(err instanceof Error ? err.message : "Delete failed");
    }
  }

  async function handleAsk(question: string) {
    if (!selected) return;
    setError(null);
    setSuccess(null);
    setIsAsking(true);
    try {
      setChatResponse(
        await chatWithDocument({ documentId: selected.id, question }),
      );
    } catch (err) {
      setError(err instanceof Error ? err.message : "Question failed");
    } finally {
      setIsAsking(false);
    }
  }

  return (
    <AppShell>
      <Header readiness={readiness} />
      {error && <Toast type="error" message={error} />}
      {success && <Toast type="success" message={success} />}
      <section className="grid flex-1 gap-6 lg:grid-cols-[0.9fr_1.1fr]">
        <UploadCard
          documents={documents}
          selectedId={selectedId}
          isLoading={isLoadingDocuments}
          isUploading={isUploading}
          maxUploadSize={
            readiness?.limits?.max_upload_size_bytes ?? 10 * 1024 * 1024
          }
          onUpload={handleUpload}
          onSelect={(id) => {
            setSelectedId(id);
            setChatResponse(null);
          }}
          onDelete={handleDelete}
        />
        <ChatPanel
          disabled={!selected}
          isLoading={isAsking}
          response={chatResponse}
          onAsk={handleAsk}
        />
      </section>
    </AppShell>
  );
}

export default App;
