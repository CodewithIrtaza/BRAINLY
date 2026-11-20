# Technical Design: Brainly — AI Customer Support Agent Platform

---

## 1. Assumptions & Architectural Decisions

### 1.1 Assumptions from PRD

| # | Assumption | Rationale |
|---|------------|-----------|
| A1 | **Single agent per workspace** for V1 | PRD explicitly states "One AI agent per workspace for the initial release" |
| A2 | **Supabase handles Auth + DB + Realtime + Storage** | PRD constraints specify Vercel + Supabase stack; reduces operational burden |
| A3 | **NVIDIA NIM provides OpenAI-compatible API** | PRD states "OpenAI-compatible" — enables use of standard OpenAI SDK |
| A4 | **Jina AI v3 embeddings are 1024-dimensional** | Verified via Jina AI documentation; impacts pgvector column definition |
| A5 | **Widget is embedded via JavaScript snippet** | PRD specifies "JS embed snippet or a simple script-based integration" |
| A6 | **No billing/subscriptions in V1** | Explicitly in Non-Goals; simplifies V1 scope significantly |
| A7 | **File uploads stored in Supabase Storage** | PRD mentions PDF/TXT upload; Supabase Storage included in stack |
| A8 | **Background processing via Supabase Edge Functions or Vercel Cron** | No separate worker infrastructure in budget; serverless functions for async tasks |
| A9 | **Multi-tenancy enforced at row level (RLS)** | Supabase Postgres with RLS is the standard pattern for this stack |
| A10 | **Urdu/Roman Urdu/English detection at application layer** | Language detection before LLM call; separate from embedding process |

### 1.2 Missing Requirements & Addressed Gaps

| Gap | Decision |
|-----|----------|
| Conversation retention period | **90 days** for conversations, then soft-delete; vectors retained with KB sources |
| Maximum KB size per workspace | **50 MB total** (≈500 PDF pages) — fits Supabase free tier + Jina AI free tier |
| Maximum file upload size | **10 MB per file** — Supabase Storage default limit |
| Rate limiting strategy | **Per-workspace: 30 req/min chat, 10 req/min upload** — enforced at API Gateway (Vercel) |
| Widget customization depth | **Colors, logo, welcome message, agent name, position** — configurable via dashboard |
| GDPR data export format | **JSON** — conversations, KB sources, lead data |
| Error tracking | **Sentry free tier** — frontend + backend error monitoring |
| API versioning | **URL versioning** (`/api/v1/`) — prepare for future breaking changes |

### 1.3 Recommended Architectural Approach

**Monorepo with two deployable units:**
- **Frontend (Next.js 14+ App Router)** → Deployed to Vercel
- **Backend API (FastAPI)** → Deployed to Vercel as Edge Functions / Serverless Functions
- **Shared types** → Generated from OpenAPI spec or Zod schemas

**Why this approach:**
- Vercel native support for both Next.js and Python (via `vercel-python`)
- Single deploy pipeline, shared environment variables
- Edge Functions for low-latency chat streaming
- Supabase as the unified data layer (Auth, Postgres, Realtime, Storage)

### 1.4 Important Technical Decisions

| Decision | Reasoning | Rejected Alternative |
|----------|-----------|---------------------|
| **FastAPI over Node/Express** | Team has Python ML expertise; better async support for streaming LLM; OpenAI SDK first-class in Python | Node.js — would require context switching for ML team |
| **pgvector over Pinecone/Weaviate** | Zero cost, included in Supabase, sufficient for <100K vectors per workspace | Pinecone — adds cost, external dependency, vendor lock-in |
| **Supabase Auth over custom JWT** | Built-in email/password, OAuth, MFA, RLS integration; saves 2+ weeks | Custom auth — reinventing wheel, security risk |
| **Serverless functions over dedicated workers** | Bootstrap budget; Vercel Cron + Edge Functions handle async jobs | Railway/Render workers — adds monthly cost, ops burden |
| **Jina AI v3 for embeddings** | Best multilingual (89 langs including Urdu), free tier, OpenAI-compatible | OpenAI text-embedding-3-small — costs money after $5 credit |
| **NVIDIA NIM (Llama 3.1 70B) for chat** | Free tier, OpenAI-compatible, strong multilingual | Groq only — no embeddings; OpenAI — costs money |
| **Shadow DOM for widget** | Style isolation, no CSS conflicts on host sites | iframe — heavier, communication complexity, SEO issues |

### 1.5 MVP Scope vs. Future Scalability

| Area | MVP (V1) | V1.1+ Scalability Path |
|------|----------|------------------------|
| **Agents** | 1 per workspace | Multiple agents, department routing |
| **Channels** | Web widget only | WhatsApp, Instagram, Telegram, Email |
| **KB Sources** | PDF, TXT, FAQ, single URL | DOCX, CSV, sitemap crawl, cloud drives |
| **Analytics** | Basic counters + CSV export | Real-time dashboards, AI insights |
| **Auth** | Email/password | SSO (SAML/OIDC), org invites |
| **Billing** | None | Stripe subscriptions, usage-based |
| **Vector Scale** | <100K vectors/ws | Partitioned indexes, hybrid search |
| **Realtime** | Supabase Realtime | Dedicated WebSocket gateway |

---

## 2. Recommended Technology Stack

| Layer | Technology | Version | Justification | Rejected Alternative |
|-------|------------|---------|---------------|---------------------|
| **Frontend Framework** | Next.js (App Router) | 14.2.x | React 18, Server Components, native Vercel deployment, excellent DX | Remix — smaller ecosystem, less Vercel integration |
| **Frontend Language** | TypeScript | 5.4.x | Type safety for API contracts, shared types with backend | JavaScript — no compile-time guarantees |
| **UI Library** | Radix UI + Tailwind CSS | Radix 1.0, Tailwind 3.4 | Unstyled accessible primitives, utility-first CSS, small bundle | MUI / Chakra — heavier, opinionated styling |
| **State Management** | React Query (TanStack Query) | 5.28.x | Server state caching, mutations, optimistic updates | Redux Toolkit — overkill for server state |
| **Forms** | React Hook Form + Zod | RHF 7.51, Zod 3.22 | Performant, schema validation shared with backend | Formik + Yup — slower, larger bundle |
| **Backend Framework** | FastAPI | 0.111.x | Async native, OpenAPI auto-gen, Pydantic integration, Python ML ecosystem | Flask — no async, manual OpenAPI; Django — heavy |
| **API Validation** | Pydantic | 2.7.x | Rust-backed, fast, JSON Schema generation | Marshmallow — slower, no native FastAPI integration |
| **Database** | PostgreSQL + pgvector | PG 16, pgvector 0.7.x | Supabase managed, ACID, vector search, RLS | MongoDB + Atlas Vector Search — no SQL, extra cost |
| **ORM** | SQLAlchemy 2.0 (async) + Alembic | SQLAlchemy 2.0.30 | Async support, type-safe queries, migration management | Prisma — Python support immature; Django ORM — tied to Django |
| **Authentication** | Supabase Auth (GoTrue) | Latest | Email/password, OAuth, MFA, RLS integration, free tier | Clerk — cost at scale; custom JWT — security risk |
| **Realtime** | Supabase Realtime | Latest | Postgres changes → WebSocket, no extra infra | Pusher / Ably — cost, extra dependency |
| **File Storage** | Supabase Storage (S3-compatible) | Latest | Integrated auth, signed URLs, CDN, free tier | AWS S3 — extra config, cost, separate IAM |
| **Vector Embeddings** | Jina AI v3 (jina-embeddings-v3) | API v1 | 1024-dim, 89 languages (Urdu), free tier, OpenAI-compatible | OpenAI text-embedding-3-small — paid; Cohere — paid |
| **LLM Chat (Primary)** | NVIDIA NIM (Llama 3.1 70B / Nemotron 3 Ultra) | API v1 | Free tier, OpenAI-compatible, multilingual, 128K context | Groq only — no embeddings; Anthropic — paid |
| **LLM Chat (Fallback)** | Groq (Llama 3.1 70B) | API v1 | Ultra-fast fallback, free tier | Together AI — less reliable free tier |
| **Background Jobs** | Vercel Cron + Edge Functions | Latest | Zero infra, integrated deploy, generous free tier | Celery + Redis — requires VPS, ops |
| **PDF Processing** | PyMuPDF (fitz) + pdfplumber | PyMuPDF 1.23, pdfplumber 0.11 | Fast text extraction, table extraction, no external API | pdfminer.slow — slower; Adobe API — paid |
| **OCR (Optional)** | Tesseract + Urdu model | Tesseract 5.3 | Free, open-source, Urdu support | Google Vision / Azure — paid, latency |
| **Language Detection** | fasttext / langdetect | fasttext 0.9.2 | Fast, accurate, supports Urdu script detection | Google Translate API — paid, latency |
| **Testing (Backend)** | pytest + pytest-asyncio | pytest 8.2, pytest-asyncio 0.23 | Async support, fixtures, parametrize, rich ecosystem | unittest — verbose, no async |
| **Testing (Frontend)** | Vitest + React Testing Library | Vitest 1.5, RTL 14.2 | Vite-native, fast, Jest-compatible API | Jest — slower, config overhead |
| **E2E Testing** | Playwright | 1.44.x | Multi-browser, mobile emulation, CI-friendly | Cypress — less mobile support |
| **Error Tracking** | Sentry | Latest | Free tier, source maps, release tracking | Datadog — expensive; LogRocket — session replay focus |
| **Analytics** | Plausible (self-hosted) or Supabase events | Latest | Privacy-friendly, GDPR-ready, simple | Google Analytics — privacy issues, complex |
| **Deployment** | Vercel (Frontend + API) + Supabase | Latest | Git push deploy, preview deployments, free tier | AWS/GCP — ops overhead, cost |
| **CI/CD** | GitHub Actions | Latest | Free for public/private, matrix builds, Vercel integration | GitLab CI — less Vercel integration |

---

## 3. System Sequence Diagrams

### 3.1 User Registration & Workspace Creation

```mermaid
sequenceDiagram
    autonumber
    actor User as Business Owner
    participant UI as Next.js Frontend
    participant Auth as Supabase Auth
    participant API as FastAPI Backend
    participant DB as Supabase Postgres
    participant Realtime as Supabase Realtime

    User->>UI: Clicks "Sign Up"
    UI->>Auth: signUp(email, password)
    Auth-->>UI: { user, session, needsEmailVerification }
    UI->>User: "Check email for verification"
    User->>Auth: Clicks verification link
    Auth-->>User: Redirects to /dashboard?verified=true
    UI->>API: POST /api/v1/workspaces (with session JWT)
    API->>DB: INSERT INTO workspaces (owner_id, name, slug)
    DB-->>API: workspace row
    API->>DB: INSERT INTO agents (workspace_id, default_config)
    DB-->>API: agent row
    API-->>UI: { workspace, agent }
    UI->>Realtime: Subscribe to workspace changes
    Realtime-->>UI: Initial state
    UI-->>User: Dashboard loaded
```

**What this proves:** Authentication is fully delegated to Supabase Auth; workspace creation is an atomic transaction; realtime subscription establishes live dashboard updates.

---

### 3.2 Knowledge Base Ingestion (PDF Upload)

```mermaid
sequenceDiagram
    autonumber
    actor User as Business Owner
    participant UI as Next.js Frontend
    participant API as FastAPI Backend
    participant Storage as Supabase Storage
    participant DB as Supabase Postgres
    participant Worker as Vercel Edge Function
    participant Jina as Jina AI API
    participant Vector as pgvector

    User->>UI: Drags PDF file
    UI->>API: POST /api/v1/kb/sources (multipart: file, type=pdf)
    API->>DB: INSERT INTO kb_sources (workspace_id, type, status='processing', filename)
    DB-->>API: source_id
    API->>Storage: Upload file to bucket: workspace/{ws_id}/{source_id}.pdf
    Storage-->>API: signed_url (24h)
    API-->>UI: { source_id, status: 'processing' }
    UI->>User: Shows "Processing..." in KB list

    par Background Processing
        Worker->>Storage: Download PDF (signed URL)
        Worker->>Worker: Extract text (PyMuPDF) + tables (pdfplumber)
        Worker->>Worker: Chunk text (500 tokens, 50 overlap)
        loop For each chunk batch
            Worker->>Jina: POST /embeddings (chunks)
            Jina-->>Worker: embeddings (1024-dim)
            Worker->>Vector: INSERT INTO kb_chunks (source_id, content, embedding, metadata)
        end
        Worker->>DB: UPDATE kb_sources SET status='ready', chunk_count=N WHERE id=source_id
    and Realtime Updates
        DB-->>Realtime: pg_notify on kb_sources update
        Realtime-->>UI: status: 'ready'
        UI-->>User: Shows "Ready" with chunk count
    end

    alt Processing Failure
        Worker->>DB: UPDATE kb_sources SET status='failed', error_msg='...' WHERE id=source_id
        DB-->>Realtime: pg_notify
        Realtime-->>UI: status: 'failed', error
        UI-->>User: Shows "Failed: <reason>" with retry button
    end
```

**What this proves:** File upload is synchronous (fast response); processing is async via Edge Function; realtime updates keep UI in sync; failure path is explicit with retry capability.

---

### 3.3 RAG Chat (Website Visitor → Agent Response)

```mermaid
sequenceDiagram
    autonumber
    actor Visitor as Website Visitor
    participant Widget as Chat Widget (JS)
    participant API as FastAPI Backend
    participant DB as Supabase Postgres
    participant Vector as pgvector
    participant Jina as Jina AI API
    participant NIM as NVIDIA NIM API
    participant Groq as Groq API (Fallback)

    Visitor->>Widget: Types question, hits Enter
    Widget->>API: POST /api/v1/chat/message { workspace_slug, message, session_id?, language? }
    API->>DB: SELECT agent_config, kb_sources FROM workspaces WHERE slug=?
    API->>Jina: POST /embeddings { input: message }
    Jina-->>API: query_embedding (1024-dim)
    API->>Vector: SELECT content, metadata FROM kb_chunks WHERE source_id IN (...) ORDER BY embedding <=> query_embedding LIMIT 5
    Vector-->>API: top_k chunks with similarity scores
    alt Chunks found (score > threshold)
        API->>NIM: POST /chat/completions { messages: [system(prompt+chunks), user(message)], stream: true }
        NIM-->>API: Stream: { delta: "token", citations: [chunk_ids] }
        API-->>Widget: SSE stream with tokens + citations
        Widget-->>Visitor: Renders streaming response with [1][2] links
    else No relevant chunks (fallback)
        API->>NIM: POST /chat/completions { messages: [system(fallback_prompt), user(message)], stream: true }
        NIM-->>API: Stream: fallback response
        API-->>Widget: SSE stream
        Widget-->>Visitor: "I don't know... Talk to human?"
    end
    API->>DB: INSERT INTO messages (conversation_id, role, content, citations, language)
    API->>DB: UPDATE conversations SET last_message_at=now(), message_count++
    opt NIM Rate Limited / Error
        API->>Groq: POST /chat/completions (same payload)
        Groq-->>API: Stream response
        API-->>Widget: SSE stream (transparent fallback)
    end
```

**What this proves:** RAG pipeline is streaming end-to-end; vector search uses pgvector with cosine similarity; dual-LLM fallback is transparent to user; citations are included in stream.

---

### 3.4 Human Agent Escalation

```mermaid
sequenceDiagram
    autonumber
    actor Visitor as Website Visitor
    participant Widget as Chat Widget
    participant API as FastAPI Backend
    participant DB as Supabase Postgres
    participant Email as Resend / SendGrid
    participant Slack as Slack Webhook (optional)

    Visitor->>Widget: Clicks "Talk to Human"
    Widget->>API: POST /api/v1/chat/escalate { conversation_id, reason }
    API->>DB: SELECT * FROM conversations WHERE id=? AND workspace_id=?
    API->>DB: SELECT * FROM messages WHERE conversation_id=? ORDER BY created_at
    API->>DB: SELECT relevant KB chunks (from last message citations)
    API->>Email: Send escalation email to workspace owner(s)
    Note right of Email: Includes: transcript, KB context, visitor info, lead data
    opt Slack Configured
        API->>Slack: POST webhook { blocks: [transcript, context, actions] }
    end
    API->>DB: UPDATE conversations SET status='escalated', escalated_at=now()
    API-->>Widget: { success: true, estimated_response_time: "15 min" }
    Widget-->>Visitor: "We've notified the team. Expected reply: 15 min"
```

**What this proves:** Escalation captures full context (transcript + KB chunks); notifications are async (email + optional Slack); conversation state transitions to 'escalated'.

---

### 3.5 Lead Capture Flow

```mermaid
sequenceDiagram
    autonumber
    actor Visitor as Website Visitor
    participant Widget as Chat Widget
    participant API as FastAPI Backend
    participant DB as Supabase Postgres
    participant Realtime as Supabase Realtime

    Visitor->>Widget: Chats with agent
    Widget->>API: POST /api/v1/chat/message { ... }
    API->>API: Detects lead intent (configured triggers: pricing, demo, contact)
    API-->>Widget: SSE stream + { show_lead_form: true, fields: [name, phone, email] }
    Widget-->>Visitor: Renders inline form in chat
    Visitor->>Widget: Fills form, submits
    Widget->>API: POST /api/v1/leads { conversation_id, fields, consent: true }
    API->>DB: INSERT INTO leads (workspace_id, conversation_id, data, consent, source='widget')
    API->>DB: UPDATE conversations SET has_lead=true
    DB-->>Realtime: pg_notify on leads insert
    Realtime-->>UI (Dashboard): New lead notification
    API-->>Widget: { success: true, message: "Thanks! We'll contact you soon." }
    Widget-->>Visitor: Confirmation message
```

**What this proves:** Lead capture is triggered contextually by backend logic; form fields configurable per workspace; GDPR consent captured; realtime dashboard notification.

---

## 4. Component Architecture

| Component | Responsibility | Owns | Communicates With | Boundaries |
|-----------|----------------|------|-------------------|------------|
| **Next.js Frontend (Dashboard)** | Business owner UI: auth, KB management, agent config, conversation history, analytics, lead dashboard | Pages, components, hooks, API client | FastAPI Backend (REST + SSE), Supabase Realtime, Supabase Auth | No direct DB access; all via API |
| **Chat Widget (Vanilla JS/React)** | Embeddable website chat: message I/O, streaming render, lead form, escalation button, session persistence | Widget bundle (< 2KB gz), localStorage session, Shadow DOM styles | FastAPI Backend (REST + SSE) | Zero dependencies on host page; CSP-compatible |
| **FastAPI Backend (API)** | Business logic: auth validation, workspace isolation, KB CRUD, chat orchestration, lead capture, escalation | API routes, services, Pydantic schemas, OpenAPI spec | Supabase (Postgres, Auth, Storage, Realtime), Jina AI, NVIDIA NIM, Groq, Email/Slack | Stateless; workspace_id from JWT claim |
| **Edge Functions (Vercel)** | Async background jobs: PDF processing, embedding generation, FAQ suggestion cron, analytics rollup | Job handlers, queue logic | Supabase (Postgres, Storage), Jina AI, pgvector | Triggered by Cron or DB webhooks; no long-running processes |
| **Supabase (Managed Services)** | Data layer: Auth (GoTrue), Postgres + pgvector, Realtime, Storage, Edge Functions | Tables, RLS policies, buckets, functions | All application components | Single source of truth; RLS enforces tenancy |
| **Jina AI API** | Embedding generation for KB chunks and query vectors | None (stateless) | FastAPI Backend, Edge Functions | Rate-limited; retry with backoff |
| **NVIDIA NIM API** | Primary LLM chat completion (streaming) | None (stateless) | FastAPI Backend | OpenAI-compatible; 128K context; fallback to Groq |
| **Groq API** | Fallback LLM chat completion | None (stateless) | FastAPI Backend | Used only on NIM error/rate-limit |
| **Email/Slack** | Notifications for escalation, lead alerts, weekly digest | None | FastAPI Backend | Async fire-and-forget; retries via queue |

---

## 5. Data Model & Application State

### 5.1 Entity Relationship Diagram

```mermaid
erDiagram
    WORKSPACE ||--o{ AGENT : has
    WORKSPACE ||--o{ KB_SOURCE : owns
    WORKSPACE ||--o{ CONVERSATION : contains
    WORKSPACE ||--o{ LEAD : captures
    WORKSPACE ||--o{ WORKSPACE_MEMBER : has
    WORKSPACE ||--o{ AGENT_CONFIG : configures
    
    KB_SOURCE ||--o{ KB_CHUNK : "chunks into"
    KB_SOURCE }|--|| WORKSPACE : belongs_to
    
    CONVERSATION ||--o{ MESSAGE : has
    CONVERSATION }|--|| WORKSPACE : belongs_to
    CONVERSATION }|--o| LEAD : "may generate"
    
    MESSAGE }|--|| CONVERSATION : belongs_to
    MESSAGE }|--o{ KB_CHUNK : "cites"
    
    LEAD }|--|| WORKSPACE : belongs_to
    LEAD }|--o| CONVERSATION : from
    
    AGENT_CONFIG }|--|| WORKSPACE : configures
    AGENT_CONFIG }|--|| AGENT : configures
    
    WORKSPACE_MEMBER }|--|| WORKSPACE : belongs_to
    WORKSPACE_MEMBER }|--|| USER : is
    
    USER ||--o{ WORKSPACE_MEMBER : member_of
```

### 5.2 Table Definitions

#### `workspaces` (Core tenant entity)
```sql
CREATE TABLE workspaces (
    id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name            TEXT NOT NULL,
    slug            TEXT NOT NULL UNIQUE,          -- for widget embedding
    owner_id        UUID NOT NULL REFERENCES auth.users(id),
    plan            TEXT NOT NULL DEFAULT 'free',  -- free, pro, business (future)
    settings        JSONB NOT NULL DEFAULT '{}',   -- branding, widget config
    created_at      TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at      TIMESTAMPTZ NOT NULL DEFAULT now(),
    deleted_at      TIMESTAMPTZ                    -- soft delete
);

CREATE INDEX idx_workspaces_owner ON workspaces(owner_id);
CREATE INDEX idx_workspaces_slug ON workspaces(slug);
```

#### `agents` (One per workspace in V1)
```sql
CREATE TABLE agents (
    id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    workspace_id    UUID NOT NULL REFERENCES workspaces(id) ON DELETE CASCADE,
    name            TEXT NOT NULL DEFAULT 'Brainly Assistant',
    description     TEXT,
    instructions    TEXT,                          -- system prompt addition
    welcome_message TEXT NOT NULL DEFAULT 'Hello! How can I help you?',
    model           TEXT NOT NULL DEFAULT 'nvidia/llama-3.1-70b',
    temperature     REAL NOT NULL DEFAULT 0.3,
    max_tokens      INTEGER NOT NULL DEFAULT 2048,
    fallback_msg    TEXT NOT NULL DEFAULT 'I don''t have that info. Want to talk to a human?',
    created_at      TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at      TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE UNIQUE INDEX idx_agents_workspace ON agents(workspace_id);
```

#### `kb_sources` (Knowledge base sources)
```sql
CREATE TABLE kb_sources (
    id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    workspace_id    UUID NOT NULL REFERENCES workspaces(id) ON DELETE CASCADE,
    type            TEXT NOT NULL CHECK (type IN ('pdf', 'txt', 'faq', 'url')),
    filename        TEXT,                          -- original filename
    url             TEXT,                          -- for type='url'
    status          TEXT NOT NULL DEFAULT 'pending' CHECK (status IN ('pending', 'processing', 'ready', 'failed')),
    error_message   TEXT,
    chunk_count     INTEGER NOT NULL DEFAULT 0,
    token_count     INTEGER NOT NULL DEFAULT 0,
    file_size       INTEGER,                       -- bytes
    storage_path    TEXT,                          -- Supabase Storage path
    meta            JSONB NOT NULL DEFAULT '{}',   -- FAQ entries, URL selectors, etc.
    created_at      TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at      TIMESTAMPTZ NOT NULL DEFAULT now(),
    processed_at    TIMESTAMPTZ
);

CREATE INDEX idx_kb_sources_workspace ON kb_sources(workspace_id);
CREATE INDEX idx_kb_sources_status ON kb_sources(status);
```

#### `kb_chunks` (Vector embeddings + content)
```sql
CREATE TABLE kb_chunks (
    id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    source_id       UUID NOT NULL REFERENCES kb_sources(id) ON DELETE CASCADE,
    workspace_id    UUID NOT NULL REFERENCES workspaces(id) ON DELETE CASCADE,
    content         TEXT NOT NULL,                 -- original text chunk
    content_hash    TEXT NOT NULL,                 -- for deduplication
    embedding       VECTOR(1024),                  -- Jina AI v3 = 1024 dim
    metadata        JSONB NOT NULL DEFAULT '{}',   -- page_num, section, FAQ q/a, etc.
    token_count     INTEGER NOT NULL,
    created_at      TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE INDEX idx_kb_chunks_workspace ON kb_chunks(workspace_id);
CREATE INDEX idx_kb_chunks_source ON kb_chunks(source_id);
CREATE INDEX idx_kb_chunks_embedding ON kb_chunks USING ivfflat (embedding vector_cosine_ops) WITH (lists = 100);
```

#### `conversations` (Chat sessions)
```sql
CREATE TABLE conversations (
    id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    workspace_id    UUID NOT NULL REFERENCES workspaces(id) ON DELETE CASCADE,
    session_id      TEXT NOT NULL,                 -- client-side session cookie
    visitor_id      TEXT,                          -- fingerprint or anonymous ID
    language        TEXT NOT NULL DEFAULT 'en' CHECK (language IN ('en', 'ur', 'ur-Roman')),
    status          TEXT NOT NULL DEFAULT 'active' CHECK (status IN ('active', 'escalated', 'closed', 'archived')),
    has_lead        BOOLEAN NOT NULL DEFAULT FALSE,
    message_count   INTEGER NOT NULL DEFAULT 0,
    metadata        JSONB NOT NULL DEFAULT '{}',   -- referrer, UTM, widget config snapshot
    started_at      TIMESTAMPTZ NOT NULL DEFAULT now(),
    last_message_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    closed_at       TIMESTAMPTZ
);

CREATE INDEX idx_conversations_workspace ON conversations(workspace_id);
CREATE INDEX idx_conversations_session ON conversations(session_id);
CREATE INDEX idx_conversations_status ON conversations(status);
CREATE INDEX idx_conversations_last_msg ON conversations(last_message_at DESC);
```

#### `messages` (Individual chat messages)
```sql
CREATE TABLE messages (
    id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    conversation_id UUID NOT NULL REFERENCES conversations(id) ON DELETE CASCADE,
    role            TEXT NOT NULL CHECK (role IN ('user', 'assistant', 'system')),
    content         TEXT NOT NULL,
    language        TEXT NOT NULL DEFAULT 'en' CHECK (language IN ('en', 'ur', 'ur-Roman')),
    citations       JSONB NOT NULL DEFAULT '[]',   -- [{chunk_id, content_preview, score}]
    token_count     INTEGER,
    model_used      TEXT,                          -- 'nvidia/llama-3.1-70b' or 'groq/llama-3.1-70b'
    is_fallback     BOOLEAN NOT NULL DEFAULT FALSE,
    meta            JSONB NOT NULL DEFAULT '{}',   -- lead_form_shown, escalation_triggered, etc.
    created_at      TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE INDEX idx_messages_conversation ON messages(conversation_id, created_at);
CREATE INDEX idx_messages_fallback ON messages(is_fallback) WHERE is_fallback = TRUE;
```

#### `leads` (Captured leads)
```sql
CREATE TABLE leads (
    id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    workspace_id    UUID NOT NULL REFERENCES workspaces(id) ON DELETE CASCADE,
    conversation_id UUID REFERENCES conversations(id) ON DELETE SET NULL,
    data            JSONB NOT NULL,                -- {name, phone, email, custom_fields...}
    consent         BOOLEAN NOT NULL DEFAULT TRUE, -- GDPR consent
    source          TEXT NOT NULL DEFAULT 'widget',
    status          TEXT NOT NULL DEFAULT 'new' CHECK (status IN ('new', 'contacted', 'qualified', 'lost')),
    notes           TEXT,
    created_at      TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at      TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE INDEX idx_leads_workspace ON leads(workspace_id);
CREATE INDEX idx_leads_conversation ON leads(conversation_id);
CREATE INDEX idx_leads_status ON leads(status);
```

#### `faq_suggestions` (Auto-generated FAQ candidates)
```sql
CREATE TABLE faq_suggestions (
    id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    workspace_id    UUID NOT NULL REFERENCES workspaces(id) ON DELETE CASCADE,
    question        TEXT NOT NULL,
    answer          TEXT NOT NULL,
    source_conversation_ids UUID[] NOT NULL,
    confidence      REAL NOT NULL,                 -- 0.0 - 1.0
    status          TEXT NOT NULL DEFAULT 'pending' CHECK (status IN ('pending', 'approved', 'rejected', 'added')),
    reviewed_by     UUID REFERENCES auth.users(id),
    reviewed_at     TIMESTAMPTZ,
    created_at      TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE INDEX idx_faq_suggestions_workspace ON faq_suggestions(workspace_id);
CREATE INDEX idx_faq_suggestions_status ON faq_suggestions(status);
```

### 5.3 Row Level Security (RLS) Policies

```sql
-- Enable RLS on all tenant tables
ALTER TABLE workspaces ENABLE ROW LEVEL SECURITY;
ALTER TABLE agents ENABLE ROW LEVEL SECURITY;
ALTER TABLE kb_sources ENABLE ROW LEVEL SECURITY;
ALTER TABLE kb_chunks ENABLE ROW LEVEL SECURITY;
ALTER TABLE conversations ENABLE ROW LEVEL SECURITY;
ALTER TABLE messages ENABLE ROW LEVEL SECURITY;
ALTER TABLE leads ENABLE ROW LEVEL SECURITY;
ALTER TABLE faq_suggestions ENABLE ROW LEVEL SECURITY;

-- Policy: Users can only access their workspace data
CREATE POLICY workspace_isolation ON workspaces
    USING (owner_id = auth.uid() OR id IN (SELECT workspace_id FROM workspace_members WHERE user_id = auth.uid()));

CREATE POLICY agents_isolation ON agents
    USING (workspace_id IN (SELECT id FROM workspaces WHERE owner_id = auth.uid() OR id IN (SELECT workspace_id FROM workspace_members WHERE user_id = auth.uid())));

-- Repeat pattern for all tenant tables...
-- kb_sources, kb_chunks, conversations, messages, leads, faq_suggestions
-- all use: workspace_id IN (SELECT id FROM workspaces WHERE ...)
```

### 5.4 Application State & Transitions

| Entity | States | Valid Transitions |
|--------|--------|-------------------|
| `kb_sources.status` | `pending` → `processing` → `ready` / `failed` | `failed` → `processing` (retry) |
| `conversations.status` | `active` → `escalated` / `closed` / `archived` | `escalated` → `active` (agent takes over) |
| `leads.status` | `new` → `contacted` → `qualified` / `lost` | `qualified` → `lost` (re-open) |
| `faq_suggestions.status` | `pending` → `approved` / `rejected` | `approved` → `added` (one-way) |

### 5.5 Data Lifecycle & Retention

| Data | Retention | Deletion Policy |
|------|-----------|-----------------|
| `conversations` + `messages` | 90 days active, then soft-delete | GDPR: hard delete on request |
| `kb_chunks` | Retained while `kb_sources` exists | Cascade delete on source removal |
| `leads` | 2 years (business record) | GDPR: export + delete on request |
| `faq_suggestions` | 30 days if `pending`, permanent if `added` | Auto-clean rejected after 30 days |
| `workspaces` (soft-deleted) | 30 days grace period | Hard delete after 30 days |

---

## 6. API Design

### 6.1 Conventions

- **Base URL**: `https://api.brainly.ai/v1` (production), `https://<preview>.vercel.app/api/v1` (preview)
- **Auth**: Bearer token (Supabase JWT) in `Authorization` header
- **Workspace context**: Extracted from JWT `workspace_id` claim (set via custom Supabase Auth hook)
- **Response envelope**: `{ "data": T, "meta": { ... } }` for success; `{ "error": { "code", "message", "details" } }` for errors
- **Pagination**: `?page=1&limit=20` → returns `{ data: [], meta: { page, limit, total, total_pages } }`
- **Streaming**: `text/event-stream` for chat responses

### 6.2 Authentication Endpoints (Delegated to Supabase)

| Method | Route | Purpose |
|--------|-------|---------|
| POST | `/auth/signup` | Email/password registration (calls Supabase) |
| POST | `/auth/login` | Email/password login (calls Supabase) |
| POST | `/auth/logout` | Sign out (calls Supabase) |
| POST | `/auth/refresh` | Refresh access token |
| GET | `/auth/me` | Current user + workspace membership |

> **Note**: Actual auth flows use Supabase JS client directly from frontend. Backend only validates JWT.

### 6.3 Workspace & Agent Endpoints

| Method | Route | Purpose | Auth |
|--------|-------|---------|------|
| GET | `/workspaces` | List user's workspaces | ✅ |
| POST | `/workspaces` | Create workspace | ✅ |
| GET | `/workspaces/{id}` | Get workspace details | ✅ |
| PATCH | `/workspaces/{id}` | Update workspace (branding, settings) | ✅ |
| DELETE | `/workspaces/{id}` | Soft delete workspace | ✅ |
| GET | `/workspaces/{id}/agent` | Get agent config | ✅ |
| PATCH | `/workspaces/{id}/agent` | Update agent config | ✅ |

**Example: Update Agent Config**
```json
PATCH /api/v1/workspaces/ws_123/agent
{
  "name": "Support Bot",
  "instructions": "You are a helpful support agent for Acme Corp. Be concise.",
  "welcome_message": "Hi! Welcome to Acme support. How can I help?",
  "temperature": 0.2,
  "max_tokens": 1500
}
```

### 6.4 Knowledge Base Endpoints

| Method | Route | Purpose | Auth |
|--------|-------|---------|------|
| GET | `/workspaces/{ws_id}/kb/sources` | List KB sources (paginated, filterable) | ✅ |
| POST | `/workspaces/{ws_id}/kb/sources` | Create KB source (multipart for files) | ✅ |
| GET | `/workspaces/{ws_id}/kb/sources/{id}` | Get source details + status | ✅ |
| POST | `/workspaces/{ws_id}/kb/sources/{id}/reprocess` | Retry failed processing | ✅ |
| DELETE | `/workspaces/{ws_id}/kb/sources/{id}` | Delete source + vectors | ✅ |
| POST | `/workspaces/{ws_id}/kb/sources/faq` | Bulk upsert FAQ entries | ✅ |

**Example: Create PDF Source**
```bash
POST /api/v1/workspaces/ws_123/kb/sources
Content-Type: multipart/form-data

file: <binary>
type: pdf
```

**Response:**
```json
{
  "data": {
    "id": "src_abc",
    "type": "pdf",
    "filename": "policy.pdf",
    "status": "processing",
    "created_at": "2024-01-15T10:30:00Z"
  }
}
```

### 6.5 Chat Endpoints (Widget + Dashboard)

| Method | Route | Purpose | Auth |
|--------|-------|---------|------|
| POST | `/chat/message` | Send message, get streaming response | ⚠️ Widget: public (workspace_slug) |
| GET | `/chat/conversations` | List conversations (dashboard) | ✅ |
| GET | `/chat/conversations/{id}` | Get conversation + messages | ✅ |
| POST | `/chat/conversations/{id}/reset` | Reset conversation (new session) | ✅ |
| POST | `/chat/escalate` | Request human handoff | ⚠️ Widget: public |
| POST | `/chat/lead` | Submit lead capture form | ⚠️ Widget: public |

**Widget Chat Message (Public - uses workspace slug)**
```json
POST /api/v1/chat/message
{
  "workspace_slug": "acme-corp",
  "message": "What's your refund policy?",
  "session_id": "sess_xyz",
  "language": "auto"
}
```

**Streaming Response (SSE):**
```
event: token
data: {"delta": "Our", "citations": []}

event: token
data: {"delta": " refund", "citations": []}

event: citation
data: {"chunk_id": "chk_123", "preview": "Refunds within 30 days...", "score": 0.92}

event: token
data: {"delta": " policy is 30 days.", "citations": ["chk_123"]}

event: done
data: {"message_id": "msg_456", "conversation_id": "conv_789", "fallback": false}
```

### 6.6 Analytics & Leads Endpoints

| Method | Route | Purpose | Auth |
|--------|-------|---------|------|
| GET | `/analytics/overview` | Dashboard stats (conversations, resolution, fallback) | ✅ |
| GET | `/analytics/conversations` | Conversation list with filters | ✅ |
| GET | `/analytics/export` | CSV export of conversations | ✅ |
| GET | `/leads` | List leads (paginated, filterable) | ✅ |
| PATCH | `/leads/{id}` | Update lead status/notes | ✅ |

### 6.7 FAQ Suggestions Endpoints

| Method | Route | Purpose | Auth |
|--------|-------|---------|------|
| GET | `/faq/suggestions` | List pending/approved suggestions | ✅ |
| POST | `/faq/suggestions/{id}/approve` | Approve + add to KB | ✅ |
| POST | `/faq/suggestions/{id}/reject` | Reject suggestion | ✅ |

### 6.8 Error Response Format

```json
{
  "error": {
    "code": "KB_SOURCE_PROCESSING_FAILED",
    "message": "Failed to extract text from PDF",
    "details": {
      "source_id": "src_123",
      "reason": "Password protected PDF"
    }
  }
}
```

**Common Error Codes:**
| Code | HTTP Status | Description |
|------|-------------|-------------|
| `UNAUTHORIZED` | 401 | Invalid/expired JWT |
| `FORBIDDEN` | 403 | Workspace access denied |
| `NOT_FOUND` | 404 | Resource not found |
| `VALIDATION_ERROR` | 422 | Request body invalid |
| `RATE_LIMITED` | 429 | Too many requests |
| `KB_SOURCE_PROCESSING_FAILED` | 500 | Background job failed |
| `LLM_UNAVAILABLE` | 503 | Both NIM and Groq failed |
| `VECTOR_SEARCH_FAILED` | 500 | pgvector query error |

---

## 7. Project Folder Structure

```
brainly/
├── apps/
│   ├── web/                          # Next.js Dashboard (Business Owner UI)
│   │   ├── src/
│   │   │   ├── app/                  # App Router pages
│   │   │   │   ├── (auth)/           # Login, signup, verify
│   │   │   │   ├── (dashboard)/      # Protected dashboard routes
│   │   │   │   │   ├── workspace/[slug]/
│   │   │   │   │   │   ├── page.tsx          # Overview
│   │   │   │   │   │   ├── agent/page.tsx    # Agent config
│   │   │   │   │   │   ├── knowledge/page.tsx # KB management
│   │   │   │   │   │   ├── conversations/page.tsx
│   │   │   │   │   │   ├── analytics/page.tsx
│   │   │   │   │   │   └── leads/page.tsx
│   │   │   │   ├── api/              # Next.js API routes (proxy to FastAPI)
│   │   │   │   └── layout.tsx
│   │   │   ├── components/           # React components
│   │   │   │   ├── ui/               # Radix + Tailwind primitives
│   │   │   │   ├── dashboard/        # Dashboard-specific components
│   │   │   │   ├── kb/               # KB source cards, upload zone
│   │   │   │   ├── chat/             # Conversation viewer, message bubbles
│   │   │   │   └── forms/            # Form components (RHF + Zod)
│   │   │   ├── hooks/                # Custom React hooks
│   │   │   │   ├── useWorkspaces.ts
│   │   │   │   ├── useKB.ts
│   │   │   │   ├── useConversations.ts
│   │   │   │   └── useRealtime.ts
│   │   │   ├── lib/                  # Utilities
│   │   │   │   ├── api.ts            # API client (fetch wrapper)
│   │   │   │   ├── supabase.ts       # Supabase client (browser)
│   │   │   │   ├── auth.ts           # Auth helpers
│   │   │   │   └── utils.ts
│   │   │   ├── types/                # TypeScript types (shared with API)
│   │   │   └── styles/               # Global styles, Tailwind config
│   │   ├── public/                   # Static assets
│   │   ├── package.json
│   │   ├── tsconfig.json
│   │   ├── next.config.js
│   │   └── tailwind.config.ts
│   │
│   ├── widget/                       # Embeddable Chat Widget (Vanilla TS/React)
│   │   ├── src/
│   │   │   ├── entry.ts              # Widget bootstrap
│   │   │   ├── components/           # Preact/React components (Shadow DOM)
│   │   │   ├── hooks/                # Widget-specific hooks
│   │   │   ├── api.ts                # Widget API client (no auth)
│   │   │   ├── styles.css            # Scoped styles
│   │   │   └── types.ts
│   │   ├── build.ts                  # esbuild config for IIFE bundle
│   │   ├── package.json
│   │   └── tsconfig.json
│   │
│   └── api/                          # FastAPI Backend
│       ├── src/
│       │   ├── main.py               # FastAPI app factory
│       │   ├── config.py             # Pydantic Settings (env config)
│       │   ├── database.py           # SQLAlchemy async engine, session
│       │   ├── models/               # SQLAlchemy models
│       │   │   ├── __init__.py
│       │   │   ├── workspace.py
│       │   │   ├── agent.py
│       │   │   ├── kb.py
│       │   │   ├── conversation.py
│       │   │   ├── message.py
│       │   │   ├── lead.py
│       │   │   └── faq.py
│       │   ├── schemas/              # Pydantic schemas (request/response)
│       │   │   ├── __init__.py
│       │   │   ├── workspace.py
│       │   │   ├── agent.py
│       │   │   ├── kb.py
│       │   │   ├── chat.py
│       │   │   ├── lead.py
│       │   │   └── analytics.py
│       │   ├── api/                  # API route modules
│       │   │   ├── __init__.py
│       │   │   ├── deps.py           # FastAPI dependencies (auth, workspace)
│       │   │   ├── v1/
│       │   │   │   ├── __init__.py
│       │   │   │   ├── auth.py
│       │   │   │   ├── workspaces.py
│       │   │   │   ├── kb.py
│       │   │   │   ├── chat.py
│       │   │   │   ├── leads.py
│       │   │   │   ├── analytics.py
│       │   │   │   └── faq.py
│       │   ├── services/             # Business logic
│       │   │   ├── __init__.py
│       │   │   ├── kb_processor.py   # PDF/TXT/URL ingestion
│       │   │   ├── embedding.py      # Jina AI client
│       │   │   ├── llm.py            # NVIDIA NIM + Groq client
│       │   │   ├── rag.py            # RAG pipeline (search + generate)
│       │   │   ├── language.py       # Language detection
│       │   │   ├── escalation.py     # Email/Slack notifications
│       │   │   ├── lead_capture.py   # Lead form handling
│       │   │   └── faq_generator.py  # Weekly FAQ suggestion job
│       │   ├── workers/              # Vercel Edge Function handlers
│       │   │   ├── __init__.py
│       │   │   ├── process_kb.py     # KB processing job
│       │   │   └── weekly_faq.py     # Cron job for FAQ suggestions
│       │   ├── utils/                # Utilities
│       │   │   ├── __init__.py
│       │   │   ├── pdf.py            # PyMuPDF + pdfplumber helpers
│       │   │   ├── chunking.py       # Text splitting
│       │   │   └── validators.py
│       │   └── exceptions/           # Custom exceptions + handlers
│       │       ├── __init__.py
│       │       ├── http_exceptions.py
│       │       └── handlers.py
│       ├── tests/
│       │   ├── unit/
│       │   ├── integration/
│       │   └── fixtures/
│       ├── alembic/                  # Database migrations
│       │   ├── versions/
│       │   ├── env.py
│       │   └── script.py.mako
│       ├── requirements.txt
│       ├── requirements-dev.txt
│       ├── pyproject.toml
│       └── Dockerfile                # For local dev (optional)
│
├── packages/
│   └── shared-types/                 # Shared TypeScript/Python types (optional)
│       ├── package.json
│       └── src/
│
├── docs/
│   ├── PRD.md
│   ├── TECH_DESIGN.md
│   ├── API.md                        # Generated from OpenAPI
│   └── ARCHITECTURE.md
│
├── .github/
│   └── workflows/
│       ├── ci.yml                    # Lint, typecheck, test
│       ├── deploy-preview.yml        # Vercel preview deploy
│       └── deploy-prod.yml           # Vercel production deploy
│
├── turbo.json                        # Turborepo config (if monorepo)
├── package.json                      # Root package.json (workspaces)
├── pnpm-workspace.yaml               # pnpm workspaces
├── .env.example                      # Environment variable template
├── .gitignore
└── README.md
```

---

## 8. External Services & Secrets

### 8.1 Required External Services

| Service | Purpose | Integration Point | Mandatory |
|---------|---------|-------------------|-----------|
| **Supabase** | Auth, Postgres + pgvector, Realtime, Storage | All backend services | ✅ Yes |
| **NVIDIA NIM** | Primary LLM chat (Llama 3.1 70B / Nemotron) | `services/llm.py` | ✅ Yes |
| **Jina AI** | Embeddings (jina-embeddings-v3) | `services/embedding.py` | ✅ Yes |
| **Groq** | Fallback LLM chat | `services/llm.py` | ✅ Yes |
| **Resend / SendGrid** | Transactional emails (escalation, leads) | `services/escalation.py` | ✅ Yes |
| **Vercel** | Frontend + API hosting, Cron, Edge Functions | Deployment target | ✅ Yes |
| **Sentry** | Error tracking (frontend + backend) | `sentry.init()` in both apps | ✅ Yes |

### 8.2 Optional External Services

| Service | Purpose | Integration Point | Mandatory |
|---------|---------|-------------------|-----------|
| **Slack** | Escalation notifications | `services/escalation.py` | ❌ No |
| **Plausible / Matomo** | Privacy-friendly analytics | Frontend script tag | ❌ No |
| **Tesseract OCR** | Scanned PDF OCR (Urdu) | `utils/pdf.py` | ❌ No (local binary) |

### 8.3 Environment Variables

| Variable | Purpose | Required |
|----------|---------|----------|
| `SUPABASE_URL` | Supabase project URL | ✅ |
| `SUPABASE_ANON_KEY` | Supabase anonymous key (client) | ✅ |
| `SUPABASE_SERVICE_ROLE_KEY` | Supabase service role (server) | ✅ |
| `SUPABASE_JWT_SECRET` | JWT secret for token verification | ✅ |
| `NVIDIA_NIM_API_KEY` | NVIDIA NIM API key | ✅ |
| `NVIDIA_NIM_BASE_URL` | NVIDIA NIM base URL (e.g., `https://integrate.api.nvidia.com/v1`) | ✅ |
| `NVIDIA_NIM_MODEL` | Model identifier (e.g., `meta/llama-3.1-70b-instruct`) | ✅ |
| `GROQ_API_KEY` | Groq API key (fallback) | ✅ |
| `GROQ_BASE_URL` | Groq base URL (default: `https://api.groq.com/openai/v1`) | ✅ |
| `JINA_AI_API_KEY` | Jina AI API key | ✅ |
| `JINA_AI_BASE_URL` | Jina AI base URL (default: `https://api.jina.ai/v1`) | ✅ |
| `JINA_AI_MODEL` | Embedding model (default: `jina-embeddings-v3`) | ✅ |
| `RESEND_API_KEY` | Resend API key for emails | ✅ |
| `RESEND_FROM_EMAIL` | From email address | ✅ |
| `SLACK_WEBHOOK_URL` | Slack incoming webhook (optional) | ❌ |
| `SENTRY_DSN` | Sentry DSN | ✅ |
| `SENTRY_ENVIRONMENT` | `development` / `staging` / `production` | ✅ |
| `VERCEL_URL` | Auto-set by Vercel (for CORS) | ✅ |
| `NEXT_PUBLIC_API_URL` | Frontend API base URL | ✅ |
| `NEXT_PUBLIC_WIDGET_URL` | Widget CDN URL | ✅ |
| `NEXT_PUBLIC_SUPABASE_URL` | Supabase URL (client) | ✅ |
| `NEXT_PUBLIC_SUPABASE_ANON_KEY` | Supabase anon key (client) | ✅ |

---

## 9. Python Dependencies — requirements.txt

```txt
# ============================================
# Brainly Backend - Production Dependencies
# Python 3.11+
# Verified compatible versions as of 2024-01
# ============================================

# --- Core Framework ---
fastapi==0.111.0
uvicorn[standard]==0.30.1
pydantic==2.7.4
pydantic-settings==2.3.4
pydantic-extra-types==2.7.0

# --- Database & ORM ---
sqlalchemy==2.0.30
asyncpg==0.29.0
alembic==1.12.1
pgvector==0.2.5

# --- Supabase ---
supabase==2.8.0
gotrue==2.8.0

# --- HTTP Clients ---
httpx==0.27.0
openai==1.30.1          # Used for NVIDIA NIM / Groq (OpenAI-compatible)

# --- PDF Processing ---
pymupdf==1.23.7         # fitz - fast PDF text extraction
pdfplumber==0.11.4      # Table extraction
python-magic==0.4.27    # File type detection

# --- Text Processing ---
tiktoken==0.7.0         # Token counting (OpenAI-compatible)
langdetect==1.0.9       # Language detection fallback
# fasttext==0.9.2       # Optional: better language detection (requires binary)

# --- Background Jobs / Scheduling ---
# No Celery - using Vercel Cron + Edge Functions

# --- Email ---
resend==0.11.0

# --- Utilities ---
python-dotenv==1.0.1
python-multipart==0.0.9
structlog==24.1.0
tenacity==8.2.3

# --- Validation ---
email-validator==2.1.0.post1

# ============================================
# Development & Testing Dependencies
# ============================================

# --- Testing ---
pytest==8.2.2
pytest-asyncio==0.23.3
pytest-cov==4.1.0
pytest-mock==3.13.1
httpx==0.27.0           # For TestClient

# --- Type Checking ---
mypy==1.10.0
pylint==3.0.3
ruff==0.4.4

# --- Pre-commit ---
pre-commit==3.7.1

# --- Database Testing ---
# Uses Supabase local or test database - no extra deps needed
```

---

## 10. Testing Strategy

### 10.1 Unit Tests (Backend)

| Area | Coverage Target | Key Scenarios |
|------|-----------------|---------------|
| **Services: KB Processor** | 90% | PDF text extraction, chunking logic, table→markdown, error handling for corrupt files |
| **Services: Embedding** | 85% | Jina AI client, batching, retry/backoff, dimension validation |
| **Services: LLM** | 85% | NIM streaming, Groq fallback, token counting, citation extraction |
| **Services: RAG** | 90% | Vector search threshold, context assembly, fallback trigger, citation mapping |
| **Services: Language Detection** | 80% | Urdu/Roman Urdu/English classification accuracy |
| **Services: Chunking** | 95% | Token-based splitting, overlap handling, metadata preservation |
| **Utils: Validators** | 100% | File type, size, URL format, slug uniqueness |
| **Schemas: Pydantic** | 100% | Request/response validation, enum constraints |

**Framework:** `pytest` + `pytest-asyncio` + `pytest-mock`
**Mocking:** `httpx.AsyncClient` mocked for external APIs; `sqlalchemy.ext.asyncio.AsyncSession` mocked for DB
**Fixtures:** `tests/fixtures/` with sample PDFs, JSON payloads, expected outputs

### 10.2 Integration Tests (Backend)

| Area | Coverage Target | Key Scenarios |
|------|-----------------|---------------|
| **Auth + Workspace Isolation** | 100% | JWT validation, RLS enforcement, cross-workspace access denied |
| **KB CRUD + Processing** | 90% | Upload → process → ready/failed; reprocess; delete cascades vectors |
| **Chat Pipeline** | 85% | RAG flow, fallback flow, streaming, citation inclusion, conversation persistence |
| **Lead Capture** | 90% | Form submission, consent recording, conversation linking, realtime notification |
| **Escalation** | 85% | Email sent, Slack webhook, context assembly, conversation status transition |
| **FAQ Generation** | 80% | Cron job execution, suggestion creation, approve→add to KB flow |

**Database:** Supabase local development (Docker) or dedicated test project
**Test Data:** Seeded via SQL scripts + factory functions

### 10.3 Unit Tests (Frontend)

| Area | Coverage Target | Key Scenarios |
|------|-----------------|---------------|
| **Hooks** | 85% | `useKB`, `useConversations`, `useRealtime` state transitions |
| **Components: KB** | 80% | Upload zone, status badges, retry button, delete confirmation |
| **Components: Chat Viewer** | 80% | Message rendering, citations, pagination, language badges |
| **Forms** | 90% | Validation, submission, error states, Zod schema integration |

**Framework:** `Vitest` + `React Testing Library` + `@testing-library/user-event`
**Mocking:** `msw` (Mock Service Worker) for API; `Supabase Realtime` mocked

### 10.4 E2E Tests

| Journey | Priority | Scenarios |
|---------|----------|-----------|
| **Signup → Dashboard → KB Upload → Widget Test** | P0 | Full happy path; verify widget loads on test page |
| **Chat: RAG Answer with Citations** | P0 | Ask KB-covered question → verify citation links work |
| **Chat: Fallback + Escalation** | P0 | Ask unknown question → fallback → "Talk to human" → email received |
| **Lead Capture Flow** | P0 | Trigger lead form → submit → appears in dashboard |
| **Multi-language Chat** | P1 | Urdu input → Urdu response; Roman Urdu → Roman Urdu |
| **Widget Embed** | P1 | Widget loads on external HTML page; CSP compatible |
| **Auth: Session Persistence** | P1 | Refresh page → stays logged in; token refresh works |

**Framework:** `Playwright` (Chromium, Firefox, WebKit + mobile viewports)
**CI:** Run on GitHub Actions for every PR

### 10.5 Test Database Strategy

- **Local Dev:** Supabase CLI (`supabase start`) → local Postgres + pgvector + Auth + Realtime + Storage
- **CI:** GitHub Actions service container with Supabase Docker image or dedicated test Supabase project
- **Migrations:** Alembic applied before test run; rollback after
- **Data:** Factories using `factory_boy` for Python; `faker` for test data

### 10.6 Minimum Critical Coverage

| Layer | Minimum Coverage |
|-------|------------------|
| Backend Business Logic (services) | 85% |
| API Routes (happy + error paths) | 80% |
| Frontend Critical User Flows (E2E) | 100% of P0 journeys |
| RLS Policies | 100% (automated via integration tests) |

---

## 11. Deployment & Infrastructure

### 11.1 Deployment Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                      GitHub (main)                          │
└──────────────────────────┬──────────────────────────────────┘
                           │ Push / PR
                           ▼
┌─────────────────────────────────────────────────────────────┐
│                    GitHub Actions CI                        │
│  ┌─────────┐ ┌─────────┐ ┌─────────┐ ┌──────────────────┐  │
│  │ Lint    │ │ Typecheck│ │ Unit    │ │ Integration      │  │
│  │ (ruff)  │ │ (mypy)  │ │ Tests   │ │ Tests (Supabase) │  │
│  └────┬────┘ └────┬────┘ └────┬────┘ └────────┬─────────┘  │
└───────┼────────────┼──────────┼───────────────┼────────────┘
        │            │          │               │
        ▼            ▼          ▼               ▼
   ┌─────────────────────────────────────────────────────┐   │
   │              Vercel Preview Deployment               │   │
   │  ┌──────────────┐  ┌──────────────┐                  │   │
   │  │ Next.js Web  │  │ FastAPI API  │                  │   │
   │  │ (Dashboard)  │  │ (Edge Fns)   │                  │   │
   │  └──────────────┘  └──────────────┘                  │   │
   └──────────────────────────┬────────────────────────────┘   │
                              │ Manual "Promote to Production"  │
                              ▼                                  │
   ┌─────────────────────────────────────────────────────┐      │
   │            Vercel Production Deployment              │      │
   │  ┌──────────────┐  ┌──────────────┐                  │      │
   │  │ Next.js Web  │  │ FastAPI API  │                  │      │
   │  │ brainly.ai   │  │ api.brainly.ai             │      │
   │  └──────────────┘  └──────────────┘                  │      │
   └─────────────────────────────────────────────────────┘      │
                              │                                  │
                              ▼                                  │
   ┌─────────────────────────────────────────────────────┐      │
   │                  Supabase (Managed)                  │      │
   │  ┌──────────┐ ┌──────────┐ ┌──────────┐ ┌────────┐  │      │
   │  │ Postgres │ │ Auth     │ │ Realtime │ │ Storage│  │      │
   │  │ +pgvector│ │ (GoTrue) │ │          │ │        │  │      │
   │  └──────────┘ └──────────┘ └──────────┘ └────────┘  │      │
   └─────────────────────────────────────────────────────┘      │
```

### 11.2 Environment Separation

| Environment | Vercel | Supabase | Domain | Purpose |
|-------------|--------|----------|--------|---------|
| **Development** | Local (`vercel dev`) | Local (`supabase start`) | `localhost:3000` | Daily dev |
| **Preview** | Auto per PR | Preview branch (Supabase branching) | `pr-123.brainly.vercel.app` | PR review |
| **Staging** | `staging` branch | Staging project | `staging.brainly.ai` | QA, demos |
| **Production** | `main` branch | Production project | `brainly.ai` / `api.brainly.ai` | Live |

### 11.3 CI/CD Workflow (`.github/workflows/ci.yml`)

```yaml
name: CI
on: [push, pull_request]
jobs:
  lint-and-typecheck:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: pnpm/action-setup@v2
      - uses: actions/setup-node@v4
        with: { node-version: 20, cache: 'pnpm' }
      - run: pnpm install --frozen-lockfile
      - run: pnpm lint          # ruff + eslint
      - run: pnpm typecheck     # mypy + tsc

  backend-tests:
    runs-on: ubuntu-latest
    services:
      postgres:
        image: supabase/postgres:16-pgvector
        env: { POSTGRES_PASSWORD: test }
        ports: [5432:5432]
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v5
        with: { python-version: '3.11' }
      - run: pip install -r apps/api/requirements.txt -r apps/api/requirements-dev.txt
      - run: alembic upgrade head
        env: { DATABASE_URL: postgresql://postgres:test@localhost:5432/test }
      - run: pytest apps/api/tests -v --cov=src

  frontend-tests:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: pnpm/action-setup@v2
      - run: pnpm install --frozen-lockfile
      - run: pnpm test:unit       # vitest
      - run: pnpm test:e2e        # playwright

  deploy-preview:
    needs: [lint-and-typecheck, backend-tests, frontend-tests]
    if: github.event_name == 'pull_request'
    runs-on: ubuntu-latest
    steps:
      - uses: amondnet/vercel-action@v25
        with:
          vercel-token: ${{ secrets.VERCEL_TOKEN }}
          vercel-org-id: ${{ secrets.VERCEL_ORG_ID }}
          vercel-project-id: ${{ secrets.VERCEL_PROJECT_ID }}
          working-directory: ./apps/web
```

### 11.4 Database Migration Strategy

- **Tool:** Alembic (SQLAlchemy)
- **Workflow:** 
  1. Developer creates migration: `alembic revision --autogenerate -m "description"`
  2. Review SQL in PR
  3. On merge to `main`: GitHub Action runs `alembic upgrade head` against production Supabase
- **Rollback:** `alembic downgrade -1` (manual, requires DB access)
- **Zero-downtime:** Additive migrations only (new columns nullable, new tables); backfill in separate step

### 11.5 Logging & Monitoring

| Layer | Tool | Configuration |
|-------|------|---------------|
| **Backend Logs** | Structlog → JSON → Vercel Logs | `structlog` with `processor=JSONRenderer`; request ID correlation |
| **Frontend Logs** | Console + Sentry | `Sentry.init({ tracesSampleRate: 0.1 })` |
| **Error Tracking** | Sentry (Free tier: 5K events/mo) | Both apps; release tracking via `VERCEL_GIT_COMMIT_SHA` |
| **Database** | Supabase Dashboard + pg_stat_statements | Slow query detection; index advisor |
| **Uptime** | Vercel Analytics + UptimeRobot (free) | `/api/v1/health` endpoint |
| **Custom Metrics** | Supabase Realtime events → Plausible / custom | `conversation_started`, `fallback_triggered`, `lead_captured` |

### 11.6 Health Checks

| Endpoint | Purpose | Expected Response |
|----------|---------|-------------------|
| `GET /api/v1/health` | Load balancer / uptime | `{ "status": "ok", "version": "1.0.0", "checks": { "db": "ok", "nim": "ok", "jina": "ok" } }` |
| `GET /api/v1/health/ready` | Kubernetes-style readiness | Checks DB connectivity, external API reachability |

### 11.7 Backup & Recovery

| Data | Backup Method | RPO | RTO |
|------|---------------|-----|-----|
| **Postgres** | Supabase automated (daily + PITR) | 24h | < 1h |
| **Storage** | Supabase automated (cross-region) | 24h | < 4h |
| **Auth** | Supabase managed | N/A | N/A |
| **Configuration** | Git (Infrastructure as Code) | 0 | < 30m |

### 11.8 Scaling Considerations (Post-V1)

| Bottleneck | Trigger | Mitigation |
|------------|---------|------------|
| **pgvector IVFFlat** | > 100K vectors/workspace | Migrate to HNSW index; partition by workspace |
| **Edge Function Duration** | PDF processing > 30s | Move to Supabase Edge Functions (longer timeout) or background queue |
| **NIM Rate Limits** | > 100 req/min/workspace | Implement token bucket per workspace; queue + retry |
| **Realtime Connections** | > 200 concurrent/workspace | Supabase Pro plan; or dedicated WebSocket gateway |
| **Vercel Function Invocations** | > 1M/mo | Upgrade to Pro; optimize cold starts |

---

## 12. Top 5 Technical Risks & Mitigation

| # | Risk | Likelihood | Impact | Consequences | Mitigation | Validation | First Task |
|---|------|------------|--------|--------------|------------|------------|------------|
| **1** | **NVIDIA NIM rate limits / instability** | High | High | Chat fails silently; poor UX; no fallback visibility | Circuit breaker pattern; Groq fallback; per-workspace token bucket; explicit error codes | Load test NIM API (100 req/min); verify fallback triggers | Implement `LLMClient` with circuit breaker + Groq fallback |
| **2** | **pgvector performance at scale** | Medium | High | Slow queries (>2s); poor RAG quality; user churn | IVFFlat with tuned `lists`; monitor query plans; plan HNSW migration | Benchmark 10K/50K/100K vectors; measure p95 latency | Create `kb_chunks` with IVFFlat; add `EXPLAIN ANALYZE` test |
| **3** | **PDF extraction quality (Urdu/scanned)** | High | Medium | KB sources fail or produce garbage chunks; user loses trust | PyMuPDF + pdfplumber primary; Tesseract OCR fallback; manual review queue for failed | Test 20 real PDFs (Urdu, tables, scanned); measure extraction accuracy | Build `KBProcessor` with multi-extractor pipeline |
| **4** | **Widget CSP/compatibility issues** | Medium | High | Widget blocked on customer sites; adoption fails | Shadow DOM; no inline styles; CSP-friendly nonce support; test matrix | Test on WordPress, Shopify, Wix, static HTML, React apps | Build widget v1; run compatibility matrix |
| **5** | **Jina AI free tier token exhaustion** | Medium | Medium | Embeddings fail; new KB sources can't process | Token estimation per workspace; alert at 80% quota; batch efficiently | Calculate: 50MB KB ≈ 12M tokens → ~12 workspaces/month free tier | Implement token counter + alerting in embedding service |

---

## 13. Implementation Readiness Checklist

### Architecture Decisions
- [x] Monorepo structure defined (apps/web, apps/widget, apps/api)
- [x] Technology stack finalized with versions
- [x] Data model + RLS policies designed
- [x] API contracts specified (OpenAPI-ready)
- [x] Critical workflows sequence-diagrammed
- [x] External services identified + secrets listed
- [x] Deployment architecture documented

### Technology Versions Verified
- [x] Next.js 14.2.x + React 18 + TypeScript 5.4
- [x] FastAPI 0.111 + Pydantic 2.7 + SQLAlchemy 2.0
- [x] Supabase (Postgres 16 + pgvector 0.7 + GoTrue + Realtime)
- [x] NVIDIA NIM (OpenAI-compatible) + Groq + Jina AI v3
- [x] Vercel (Edge Functions, Cron, Python support)
- [x] Radix UI + Tailwind 3.4 + TanStack Query 5

### Database Schema
- [x] All tables defined with columns, types, constraints
- [x] Indexes specified (including pgvector IVFFlat)
- [x] RLS policies written for all tenant tables
- [x] Migration strategy (Alembic) defined
- [x] Soft-delete + retention policies documented

### API Contracts
- [x] All endpoints listed with method, path, auth, payloads
- [x] Streaming chat response format defined (SSE)
- [x] Error codes + response format standardized
- [x] Pagination/filtering conventions set
- [x] Widget public endpoints separated from authenticated

### Critical Workflows Documented
- [x] User registration + workspace creation
- [x] KB ingestion (PDF → chunks → embeddings → pgvector)
- [x] RAG chat with streaming + citations + fallback
- [x] Human escalation with context transfer
- [x] Lead capture + realtime dashboard notification

### Security Considerations
- [x] Multi-tenancy via RLS (not application-level only)
- [x] JWT validation on every authenticated request
- [x] Workspace isolation enforced at DB level
- [x] File upload validation (type, size, path traversal)
- [x] Rate limiting strategy defined (per-workspace)
- [x] GDPR: export, delete, consent capture
- [x] CSP-compatible widget (Shadow DOM)

### Environment Variables
- [x] All required variables listed (18)
- [x] Optional variables listed (3)
- [x] No secrets in repo (`.env.example` only)
- [x] Vercel + Supabase integration variables mapped

### Dependencies Finalized
- [x] `requirements.txt` created with pinned versions
- [x] All packages verified compatible (Python 3.11)
- [x] No duplicate responsibilities (e.g., single HTTP client)
- [x] Dev dependencies separated

### Testing Strategy Established
- [x] Unit / Integration / E2E layers defined
- [x] Frameworks selected (pytest, Vitest, Playwright)
- [x] Mocking strategy documented
- [x] Test database approach (Supabase local)
- [x] Minimum coverage targets set

### Deployment Approach Defined
- [x] Vercel + Supabase architecture
- [x] Preview / Staging / Production environments
- [x] CI/CD pipeline (GitHub Actions → Vercel)
- [x] Migration strategy (Alembic on merge)
- [x] Logging, monitoring, health checks
- [x] Backup/recovery documented

### Top Risks Assigned Initial Tasks
- [x] Risk 1 (NIM): Implement `LLMClient` with circuit breaker → **Week 1**
- [x] Risk 2 (pgvector): Benchmark IVFFlat with 10K vectors → **Week 1**
- [x] Risk 3 (PDF): Build multi-extractor `KBProcessor` → **Week 2**
- [x] Risk 4 (Widget): Build v1 widget + compatibility matrix → **Week 2**
- [x] Risk 5 (Jina): Token counter + alerting in embedding service → **Week 1**

---

**Document Status:** Ready for implementation  
**Next Step:** Begin Week 1 sprint — Project setup, database schema, auth integration, LLM client with fallback