# PRD: Brainly — AI Customer Support Agent Platform

---

## Problem

Small and medium businesses lose customers and leads because they cannot answer repetitive questions (delivery, pricing, refunds, tracking) 24/7. Existing chatbots are English-centric, complex to set up, require coding, and don't support local Pakistani workflows (Urdu/Roman Urdu, WhatsApp, COD). Business owners need a **no-code, self-serve AI agent** that learns from their own data (PDFs, FAQs, website) and deploys on their website in minutes — with tri-language support and WhatsApp as a differentiator.

---

## Users

| Persona | Description | Pain Points |
|---------|-------------|-------------|
| **Primary: Business Owner / Founder** | Solo or small team (1-10), e-commerce, services, local retail in Pakistan and globally. Non-technical. | No time to answer repetitive chats; can't afford 24/7 staff; existing bots too complex/expensive; need Urdu + English. |
| **Secondary: Support Staff** | Handles escalations from AI agent. | Needs context when taking over; wants to reduce ticket volume. |
| **Tertiary: Website Visitor / Customer** | Asks questions pre-purchase or post-purchase. | Wants instant answers in their language (Urdu/Roman Urdu/English); hates waiting. |

---

## Goals

1. **Time-to-value < 15 minutes** — Sign up → upload KB → embed widget → live.
2. **Answer accuracy ≥ 80%** on questions covered by knowledge base.
3. **Fallback rate < 20%** — Agent gracefully admits ignorance and offers escalation.
4. **Resolution rate ≥ 60%** — Conversations end without human handoff.
5. **Setup completion ≥ 70%** — Signups upload at least 1 knowledge source.
6. **Widget loads < 2s** on mobile and desktop.
7. **Private beta with 5-10 businesses** — Validate, iterate, then public launch.

---

## Non-Goals (Explicitly Out of Scope for V1)

- Multiple agents per workspace (sales, support, billing)
- DOCX, CSV, Excel, PPT, cloud-drive ingestion
- Sitemap crawling & automatic retraining
- Instagram, Facebook, Telegram, email, voice channels
- Orders, payments, COD, courier tracking, booking workflows
- Human team inbox & advanced assignment rules
- Billing, subscriptions, usage-based credits
- White-labeling, custom domains, advanced branding
- Advanced analytics & AI-generated business insights
- A/B testing for agent prompts

---

## Features

### Must-Have (Core + Expected — 16 features)

| ID | Feature | Source | Effort |
|----|---------|--------|--------|
| A1 | Multi-tenant workspace authentication (register, login, logout, session mgmt) | Core | M |
| A2 | Knowledge base ingestion: PDF, TXT, manual FAQ, single-page URL | Core | M |
| A3 | Vector embedding (Jina AI v3) + semantic search (pgvector) | Core | M |
| A4 | RAG-based chat with source citations | Core | M |
| A5 | Web chat widget + JS embed snippet (responsive, mobile-first) | Core | M |
| A6 | Agent configuration: name, description, welcome message, instructions | Core | S |
| A7 | Conversation session management (create, continue, reset, retry) | Core | S |
| A8 | Fallback response when KB has no answer (polite, offers escalation) | Core | S |
| B1 | Dashboard: workspace overview, agent status, KB sources, recent conversations | Expected | M |
| B2 | Knowledge source management: list, delete, re-process, status (processing/ready/failed) | Expected | S |
| B3 | Conversation history with search & filter | Expected | M |
| B4 | Basic analytics: conversation volume, resolution rate, fallback rate | Expected | M |
| B5 | Brand customization: primary color, logo, welcome message, agent name | Expected | S |
| B6 | Mobile-responsive chat widget (tested on iOS Safari, Chrome Android) | Expected | S |
| B7 | Email/password auth + secure session management (Supabase Auth) | Expected | S |
| B8 | Error handling & user-friendly messages (toast, inline, widget error states) | Expected | S |

### Should-Have (Differentiators for V1 — 4 features, build in priority order)

| ID | Feature | Source | Effort |
|----|---------|--------|--------|
| C1 | **Urdu / Roman Urdu / English tri-language support** — auto-detect language, respond in same script | Differentiator | M |
| C3 | **Lead capture forms in chat** — configurable fields (name, phone, email, custom), stored in dashboard | Differentiator | M |
| C6 | **Human agent escalation with context transfer** — "Talk to human" button, sends conversation summary + KB context to email/Slack | Differentiator | M |
| C7 | **Smart FAQ auto-generation** — weekly job analyzes conversations, suggests new FAQ entries for review | Differentiator | M |

### Could-Have (Differentiators — start in V1, may complete in V1.1)

| ID | Feature | Source | Effort |
|----|---------|--------|--------|
| C2 | **WhatsApp Business API integration** — same agent, same KB, WhatsApp chat window | Differentiator | L |
| C8 | **Voice message support (STT/TTS)** — Whisper for STT, ElevenLabs/Coqui for TTS, Urdu + English | Differentiator | L |

---

## User Stories

### Authentication & Workspace
- **As a business owner**, I can register with email/password so that I get a secure workspace.
  - Acceptance: Email verification sent; password ≥ 8 chars; redirect to dashboard on success.
- **As a business owner**, I can log in and only see my workspace data (users, sources, conversations, vectors).
  - Acceptance: Two test workspaces cannot access each other's data via API or UI.

### Knowledge Base
- **As a business owner**, I can upload a PDF/TXT file and see its processing status (processing → ready / failed).
  - Acceptance: File appears in list within 5s; status updates in realtime; failed shows error reason.
- **As a business owner**, I can add manual FAQ entries (question + answer) that are immediately searchable.
  - Acceptance: FAQ appears in KB list; agent cites it in responses.
- **As a business owner**, I can ingest a single website URL (or controlled set) as a knowledge source.
  - Acceptance: Page content extracted, chunked, embedded; status shown.
- **As a business owner**, I can delete a knowledge source and its indexed vectors are removed.
  - Acceptance: Source gone from list; agent no longer cites it; vectors deleted from pgvector.

### AI Chat (RAG)
- **As a website visitor**, I can ask a question and get an answer grounded in the business KB with source citations.
  - Acceptance: Answer includes [1], [2] links to source chunks; clicking opens source preview.
- **As a website visitor**, if my question isn't in the KB, I get a polite fallback with escalation option.
  - Acceptance: Fallback triggers < 20% of time on KB-covered topics; message offers "Talk to human".
- **As a website visitor**, I can chat in Urdu, Roman Urdu, or English and get replies in the same language.
  - Acceptance: Auto-detect works ≥ 90% accuracy; response script matches input script.
- **As a website visitor**, my conversation persists across page reloads (session cookie).
  - Acceptance: Refresh page → chat history restored.

### Web Chat Widget
- **As a business owner**, I get a JS embed snippet to paste in my website `<head>`.
  - Acceptance: Snippet < 2 KB gzipped; loads async; no render-blocking.
- **As a website visitor**, the widget opens, shows welcome message, and lets me type.
  - Acceptance: Opens in < 300ms; typing indicator while agent thinks; error toast on network failure.
- **As a business owner**, I can customize widget primary color, agent name, welcome message, logo/avatar.
  - Acceptance: Changes reflect in widget within 10s (realtime or refetch).

### Dashboard
- **As a business owner**, I see an overview: agent status, KB source count, conversation count (today/week/month).
  - Acceptance: Data loads in < 1s; realtime updates via Supabase Realtime.
- **As a business owner**, I can configure agent name, description, instructions, welcome message.
  - Acceptance: Changes saved; agent uses new instructions on next conversation.
- **As a business owner**, I can view conversation history with search (by date, language, resolution).
  - Acceptance: Search returns results in < 500ms; pagination works.
- **As a business owner**, I see basic analytics: total conversations, resolution rate, fallback rate, lead captures.
  - Acceptance: Metrics update daily; export CSV button.

### Differentiators (C1, C3, C6, C7)
- **As a website visitor**, I can chat in Urdu/Roman Urdu/English and get native-script responses.
  - Acceptance: Urdu Nastaliq renders correctly; Roman Urdu treated as distinct from English.
- **As a website visitor**, I may be prompted for name/phone/email to capture a lead.
  - Acceptance: Form appears contextually; data saved to dashboard; GDPR consent checkbox.
- **As a website visitor**, I can click "Talk to human" and get an email/Slack notification with full context.
  - Acceptance: Notification sent < 5s; includes conversation transcript + relevant KB chunks.
- **As a business owner**, I get weekly suggested FAQs from real conversations to approve/reject.
  - Acceptance: Job runs weekly; suggestions appear in dashboard; one-click adds to KB.

---

## Success Metrics

| Metric | Target | Measurement |
|--------|--------|-------------|
| Time-to-value (signup → live widget) | < 15 min | Analytics funnel |
| Answer accuracy (KB-covered questions) | ≥ 80% | Human eval on 100 test Qs |
| Fallback rate | < 20% | `fallback_triggered` / `message_received` |
| Resolution rate (no escalation) | ≥ 60% | Conversations without `escalation_requested` |
| Setup completion (upload ≥ 1 source) | ≥ 70% | Signups with `kb_sources_count > 0` |
| Widget load time (p95) | < 2s | Web Vitals (LCP) |
| Private beta activation | 5-10 businesses | Manual tracking |
| 30-day retention (beta) | ≥ 40% | Active workspaces / total |

---

## Constraints

| Category | Decision |
|----------|----------|
| **Budget** | Bootstrap / self-funded — minimize paid services |
| **Deadline** | 4-6 weeks to deployed V1 (private beta) |
| **Hosting** | Vercel (frontend + edge functions) + Supabase (Postgres + pgvector + Auth + Realtime + Storage) |
| **LLM Chat** | NVIDIA NIM (Llama 3.1 70B / Nemotron 3 Ultra) — free, OpenAI-compatible |
| **LLM Embeddings** | Jina AI (jina-embeddings-v3) — free tier, 89 languages including Urdu |
| **Backup Chat** | Groq (Llama 3.1 70B) — ultra-fast, free tier |
| **Team** | 2 people: You (full-stack + AI/ML), Friend (frontend + AI/ML) |
| **Launch** | Private beta (5-10 hand-picked businesses) |
| **Compliance** | Pakistan data residency (Supabase Singapore); GDPR-ready (export, delete, consent) |
| **Domain** | brainly.ai (global), brainly.pk (Pakistan redirect) |
| **Branding** | Indigo-violet gradient (#6366F1 → #8B5CF6), "Your Business. AI-Powered." |

---

## Parking Lot (Ideas Not Accepted for V1)

- Multiple agents per workspace
- DOCX, CSV, Excel, PPT, Google Drive/Notion ingestion
- Sitemap crawling & scheduled retraining
- Instagram, Facebook, Telegram, email, voice channels
- Orders, payments, COD, courier tracking, booking workflows
- Human team inbox with assignment rules & SLAs
- Billing, subscriptions, usage credits, Stripe integration
- White-labeling, custom domains, advanced branding
- Advanced analytics dashboard, AI business insights
- A/B testing for prompts, model comparison
- Webhook/API for custom integrations
- Multi-language beyond Urdu/English (Arabic, Punjabi, etc.)

---

## Open Questions

1. **PDF OCR for Urdu**: Tesseract + Urdu model accuracy on scanned Nastaliq — may need commercial OCR (Google Vision, Azure) if quality insufficient.
2. **NVIDIA NIM rate limits**: Free tier limits unpublished — need monitoring + Groq fallback logic.
3. **Jina AI v3 token limits**: Free tier ~1M tokens/mo — estimate KB size per workspace to ensure headroom.
4. **Widget CSP/compatibility**: Test on WordPress, Shopify, Wix, custom HTML — iframe vs shadow DOM decision.
5. **WhatsApp Business API verification**: Requires Meta Business Verification — timeline uncertainty for V1.1.
6. **Voice STT/TTS cost**: Whisper (free/local) vs ElevenLabs (paid) — decide for C8.
7. **Analytics privacy**: Matomo/Plausible vs Supabase events — finalize before beta.

---

## 5-Line Summary

**Brainly** is a no-code AI customer support platform where businesses upload their data (PDFs, FAQs, URLs) to create a custom agent that answers questions 24/7 on their website. V1 delivers multi-tenant workspaces, RAG chat with citations, a lightweight embeddable widget, and a dashboard — all deployable in < 15 minutes. Differentiators: tri-language (Urdu/Roman Urdu/English), lead capture, human escalation, and auto-FAQ generation. Stack: Vercel + Supabase + NVIDIA NIM (chat) + Jina AI (embeddings) — fully free-tier compatible. Private beta in 4-6 weeks with 5-10 Pakistani and global SMBs.

---

**What would you like to change?**