import { useState } from "react";
import { chatWithDocument, uploadDocument } from "../api/client";
import { AppShell } from "./components/AppShell";
import { ChatPanel } from "./components/ChatPanel";
import { Header } from "./components/Header";
import { UploadCard } from "./components/UploadCard";
import { Toast } from "./components/ui/Toast";
import type { ChatResponse, UploadedDocument } from "./types/documents";

function App() {
  const [document, setDocument] = useState<UploadedDocument | null>(null);
  const [chatResponse, setChatResponse] = useState<ChatResponse | null>(null);
  const [isUploading, setIsUploading] = useState(false);
  const [isAsking, setIsAsking] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [success, setSuccess] = useState<string | null>(null);

  async function handleUpload(file: File) {
    setError(null);
    setIsUploading(true);
    setChatResponse(null);
    setError(null);
    setSuccess(null);

    try {
      const uploadedDocument = await uploadDocument(file);
      setDocument(uploadedDocument);
      setSuccess("Document ingested successfully.");
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
    setError(null);
    setSuccess(null);

    try {
      const response = await chatWithDocument({
        documentId: document.document_id,
        question,
      });

      setChatResponse(response);
      setSuccess("Grounded answer generated.");
    } catch (err) {
      setError(err instanceof Error ? err.message : "Question failed");
    } finally {
      setIsAsking(false);
    }
  }

  return (
  <AppShell>
    <Header />

    {error && <Toast type="error" message={error} />}
    {success && <Toast type="success" message={success} />}

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