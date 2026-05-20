# ClientOps Copilot

An AI-powered operations copilot for small businesses.

ClientOps Copilot lets teams upload internal documents, ask natural-language questions, and receive grounded answers with source citations. It is designed as a production-style AI system using RAG, vector search, and workflow automation.

## Why I built this

Businesses often know they want to use AI, but struggle to connect it to real workflows. This project explores how a client-facing AI platform can turn messy documents into searchable knowledge and actionable insights.

## Core Features

- Upload business documents
- Chunk and embed document content
- Store embeddings in a vector database
- Ask questions using a RAG pipeline
- Return grounded answers with source citations
- Simple dashboard for uploaded knowledge sources

## Tech Stack

- Frontend: React, Tailwind
- Backend: FastAPI
- AI/RAG: LangChain, OpenAI/Azure OpenAI
- Vector DB: Pinecone initially, Azure AI Search later
- Storage: local first, Azure Blob/Supabase later
- Deployment: Vercel + Render initially, Azure later

## Roadmap

- [ ] Backend API setup
- [ ] Frontend dashboard
- [ ] Document upload
- [ ] Text extraction
- [ ] Chunking and embeddings
- [ ] Pinecone vector search
- [ ] RAG chat endpoint
- [ ] Source citations
- [ ] Azure deployment
- [ ] Workflow automation demo
