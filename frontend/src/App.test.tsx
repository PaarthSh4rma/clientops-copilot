import { cleanup, render, screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { afterEach, describe, expect, it, vi } from "vitest";
import App from "./App";
import type {
  ChatResponse,
  DocumentSummary,
  SessionDocument,
} from "./types/documents";

const DOCUMENTS: DocumentSummary[] = [
  {
    id: "doc-1",
    filename: "Northstar client success plan with a long filename.txt",
    content_type: "text/plain",
    file_size: 4280,
    checksum: "a".repeat(64),
    processing_status: "ready",
    processing_error: null,
    chunk_count: 6,
    created_at: "2026-09-07T00:00:00Z",
    updated_at: "2026-09-07T00:00:00Z",
  },
];

const READINESS = {
  status: "ready",
  dependencies: {
    database: "ready",
    file_storage: "ready",
    vector_store: "ready",
    llm: "configured",
  },
  limits: { max_upload_size_bytes: 10485760 },
  demo_mode: false,
  capabilities: { upload: true, delete: true, grounded_chat: true },
};

function response(status: ChatResponse["status"]): ChatResponse {
  return {
    document_id: "doc-1",
    filename: DOCUMENTS[0].filename,
    question: "Summarise this document concisely.",
    answer:
      status === "supported"
        ? "The pilot launches in November."
        : status === "insufficient_evidence"
          ? "I could not find enough relevant evidence in this document to answer that question."
          : "The answer provider is temporarily unavailable.",
    status,
    citations:
      status === "insufficient_evidence"
        ? []
        : [
            {
              document_id: "doc-1",
              filename: DOCUMENTS[0].filename,
              chunk_id: 1,
              chunk_index: 0,
              page_number: null,
              location: "Text document",
              relevance_score: 0.86,
              source_preview:
                "The pilot launch is scheduled for 4 November 2026.",
            },
          ],
  };
}

function mockApi(
  documents = DOCUMENTS,
  chatStatus: ChatResponse["status"] = "supported",
  demoMode = false,
) {
  vi.stubGlobal(
    "fetch",
    vi.fn(async (input: RequestInfo | URL, init?: RequestInit) => {
      const url = String(input);
      if (url.endsWith("/documents") && !init?.method)
        return new Response(JSON.stringify({ documents }), { status: 200 });
      if (url.endsWith("/ready"))
        return new Response(
          JSON.stringify({
            ...READINESS,
            demo_mode: demoMode,
            capabilities: {
              ...READINESS.capabilities,
              upload: !demoMode,
              delete: !demoMode,
            },
          }),
          { status: 200 },
        );
      if (url.endsWith("/documents/chat"))
        return new Response(JSON.stringify(response(chatStatus)), {
          status: 200,
        });
      throw new Error(`Unexpected request: ${url}`);
    }),
  );
}

afterEach(() => {
  cleanup();
  vi.unstubAllGlobals();
});

describe("ClientOps workspace", () => {
  it("renders an actionable empty document library", async () => {
    mockApi([]);
    render(<App />);
    expect(await screen.findByText("No documents yet")).toBeInTheDocument();
    expect(screen.getByText(/Add a client brief/)).toBeInTheDocument();
  });

  it("selects a document and renders a grounded answer with inspectable evidence", async () => {
    mockApi();
    const user = userEvent.setup();
    render(<App />);
    await screen.findByText("Start with a client workflow");
    await user.click(screen.getByRole("button", { name: "Summarise" }));
    expect(
      await screen.findByText("The pilot launches in November."),
    ).toBeInTheDocument();
    expect(screen.getByText("Supported by evidence")).toBeInTheDocument();
    await user.click(screen.getByRole("button", { name: /Text document/ }));
    expect(
      screen.getAllByText(/pilot launch is scheduled/i).length,
    ).toBeGreaterThan(0);
    expect(screen.getAllByText(/Strong match/).length).toBeGreaterThan(0);
  });

  it.each([
    ["insufficient_evidence", "Insufficient evidence"],
    ["provider_failure", "Provider unavailable"],
  ] as const)("keeps %s visually distinct", async (status, label) => {
    mockApi(DOCUMENTS, status);
    const user = userEvent.setup();
    render(<App />);
    await screen.findByText("Start with a client workflow");
    await user.click(screen.getByRole("button", { name: "Summarise" }));
    expect(await screen.findByText(label)).toBeInTheDocument();
  });

  it("labels demo mode and removes upload and delete workflows", async () => {
    mockApi(DOCUMENTS, "supported", true);
    render(<App />);
    expect(
      await screen.findByText(
        "Sample documents only. Upload and delete are locked in this public demo.",
      ),
    ).toBeInTheDocument();
    expect(
      screen.queryByRole("button", { name: /Delete/ }),
    ).not.toBeInTheDocument();
    await waitFor(() =>
      expect(
        screen.getByLabelText("Uploads disabled in public demo"),
      ).toBeDisabled(),
    );
  });

  it("uploads a tab-scoped document, sends follow-up evidence, and removes it locally", async () => {
    const source: SessionDocument = {
      id: "uploaded-1",
      filename: "aurora.txt",
      content_type: "text/plain",
      file_size: 70,
      checksum: "b".repeat(64),
      chunks: [
        {
          id: 1,
          chunk_index: 0,
          text: "Taylor owns the review.",
          page_number: null,
          location: "Text document",
          vector_id: "session:uploaded-1:0",
          embedding: [1, 0],
        },
      ],
    };
    const requests: Record<string, unknown>[] = [];
    const uploaded = {
      ...DOCUMENTS[0],
      id: source.id,
      filename: source.filename,
      session_document: source,
      message: "Document ready in this browser tab.",
    };
    const api = vi.fn(async (input: RequestInfo | URL, init?: RequestInit) => {
      const url = String(input);
      if (url.endsWith("/ready"))
        return new Response(
          JSON.stringify({
            ...READINESS,
            demo_mode: true,
            capabilities: {
              upload: true,
              delete: false,
              grounded_chat: true,
              session_uploads: true,
            },
          }),
        );
      if (url.endsWith("/documents"))
        return new Response(JSON.stringify({ documents: DOCUMENTS }));
      if (url.endsWith("/documents/upload"))
        return new Response(JSON.stringify(uploaded), { status: 201 });
      if (url.endsWith("/documents/chat")) {
        const body = JSON.parse(String(init?.body));
        requests.push(body);
        const answer = response("supported");
        return new Response(
          JSON.stringify({
            ...answer,
            document_id: source.id,
            filename: source.filename,
            question: body.question,
            citations: answer.citations.map((citation) => ({
              ...citation,
              document_id: source.id,
              filename: source.filename,
              relevance_score: null,
            })),
          }),
        );
      }
      throw new Error(`Unexpected request: ${url}`);
    });
    vi.stubGlobal("fetch", api);
    const user = userEvent.setup();
    render(<App />);
    await screen.findByText(/Upload your own document for this tab/);
    await user.upload(
      screen.getByLabelText("Choose document file"),
      new File([source.chunks[0].text], source.filename, {
        type: "text/plain",
      }),
    );
    await screen.findByRole("button", { name: "Delete aurora.txt" });
    await user.click(screen.getByRole("button", { name: "Summarise" }));
    await screen.findByText("The pilot launches in November.");
    expect(requests[0].workflow).toBe("summary");
    expect(requests[0].session_document).toEqual(source);
    expect(screen.getAllByText("Document passage").length).toBeGreaterThan(0);
    await user.type(
      screen.getByRole("textbox", { name: "Question about selected document" }),
      "so what should we do?",
    );
    await user.click(screen.getByRole("button", { name: "Ask question" }));
    await waitFor(() => expect(requests).toHaveLength(2));
    expect(requests[1].context).toEqual({
      document_id: source.id,
      question: requests[0].question,
      chunk_ids: [1],
    });
    await user.click(screen.getByRole("button", { name: "Delete aurora.txt" }));
    await user.click(screen.getByRole("button", { name: "Remove from tab" }));
    await waitFor(() =>
      expect(
        screen.queryByRole("button", { name: "Delete aurora.txt" }),
      ).not.toBeInTheDocument(),
    );
    expect(api.mock.calls.some(([, init]) => init?.method === "DELETE")).toBe(
      false,
    );
  });
});
