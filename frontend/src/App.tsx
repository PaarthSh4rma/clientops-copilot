import { useState } from "react";
import { chatWithDocument, uploadDocument } from "../api/client";
import { AppShell } from "../components/AppShell";
import { ChatPanel } from "../components/ChatPanel";
import { Header } from "../components/Header";
import { UploadCard } from "../components/UploadCard";
import type { ChatResponse, UploadedDocument } from "../types/documents";

function App() {
  const [document, setDocument] = useState<UploadedDocument | null>(null);
  const [chatResponse, setChatResponse] = useState<ChatResponse | null>(null);
  const [isUploading, setIsUploading] = useState(false);
  const [isAsking, setIsAsking] = useState(false);
  const [error, setError] = useState<string | null>(null);

  async function handleUpload(file: File) {
    setError(null);
    setIsUploading(true);
    setChatResponse(null);

    try {
      const uploadedDocument = await uploadDocument(file);
      setDocument(uploadedDocument);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Upload failed");
    } finally {
      setIsUploading(false);
    }
  }

  async function handleAsk(question: string) {
    if (!document) return;

    setError(null);
    setIsAsking(true);

    try {
      const response = await chatWithDocument({
        documentId: document.document_id,
        question,
      });

      setChatResponse(response);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Question failed");
    } finally {
      setIsAsking(false);
    }
  }

  return (
    <AppShell>
      <Header />

      {error && (
        <div className="mb-5 rounded-2xl border border-red-400/20 bg-red-400/10 px-4 py-3 text-sm text-red-100">
          {error}
        </div>
      )}

      <section className="grid flex-1 gap-6 lg:grid-cols-[0.9fr_1.1fr]">
        <UploadCard
          document={document}
          isUploading={isUploading}
          onUpload={handleUpload}
        />

        <ChatPanel
          disabled={!document}
          isLoading={isAsking}
          response={chatResponse}
          onAsk={handleAsk}
        />
      </section>
    </AppShell>
  );
}

export default App;