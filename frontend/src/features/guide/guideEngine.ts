export type GuideLink = { label: string; to: string };

export type GuideReply = {
  text: string;
  links?: GuideLink[];
  followUpChips?: string[];
};

export type GuideMessage = {
  id: string;
  keywords: string[];
  phrases?: string[];
  reply: GuideReply;
};

export const WELCOME_TEXT =
  "Hi! I'm your Research Desk Guide. I can explain this website and help you get started.";

export const WELCOME_REPLY: GuideReply = {
  text: WELCOME_TEXT,
  links: [
    { label: "Open Library", to: "/library" },
    { label: "Start Research", to: "/" },
  ],
};

export const SUGGESTED_CHIPS = [
  "What does this website do?",
  "How do I upload documents?",
  "How do I ask questions?",
  "What are citations?",
  "Why does it say insufficient evidence?",
];

export const FAQ_ENTRIES: GuideMessage[] = [
  {
    id: "about",
    keywords: ["what", "website", "app", "grounded", "research", "desk", "platform", "purpose", "do"],
    phrases: ["what does this website do", "what is this website", "what is this app"],
    reply: {
      text:
        "Grounded Research Desk lets you upload Markdown or plain text files, find relevant document chunks, and ask questions. " +
        "Answers include citations to those chunks. If nothing in your library supports the question, the app refuses instead of guessing.",
      links: [
        { label: "Start Research", to: "/" },
        { label: "Open Library", to: "/library" },
      ],
    },
  },
  {
    id: "upload",
    keywords: ["upload", "library", "file", "document", "ingest", "md", "markdown", "txt"],
    phrases: ["how do i upload", "add document"],
    reply: {
      text:
        "Go to Library → Upload documents (or drag a file onto the drop zone). Supported types are .md and .txt, with a size limit shown on that page (typically 5 MB). " +
        "When ingestion finishes, status shows completed and chunk count appears. PDF is not supported in this version.",
      links: [{ label: "Open Library", to: "/library" }],
    },
  },
  {
    id: "chunking",
    keywords: ["chunk", "chunking", "embed", "embedding", "vector", "ingest", "pipeline"],
    phrases: ["how does chunk", "what are embeddings"],
    reply: {
      text:
        "After upload, text is cleaned and split into overlapping chunks (configurable chunk size/overlap on the server). " +
        "Each chunk gets an embedding vector for similarity search. Demo mode often uses a fake embedder for offline tests; optional local models use real vectors.",
      links: [{ label: "Open Settings", to: "/settings" }],
    },
  },
  {
    id: "ask",
    keywords: ["ask", "question", "research", "query", "answer", "rag"],
    phrases: ["how do i ask questions", "how do i ask", "how to ask"],
    reply: {
      text:
        "Open Research, type a question about content in your uploaded documents, and submit. " +
        "The backend retrieves passages, checks whether evidence is strong enough, then generates an answer with citations. " +
        "I cannot answer from your documents — use Research for that.",
      links: [{ label: "Start Research", to: "/" }],
    },
  },
  {
    id: "citations",
    keywords: ["citation", "citations", "cite", "source", "snippet", "chunk", "evidence"],
    phrases: ["what are citations", "open source", "evidence rail"],
    reply: {
      text:
        "Citations are links to the document chunks the app retrieved for your answer — filename, excerpt, and sometimes a score. " +
        "Use Open source in the Evidence panel to view the passage in the document inspector.",
      links: [{ label: "Start Research", to: "/" }],
    },
  },
  {
    id: "insufficient",
    keywords: ["insufficient", "evidence", "weak", "refuse", "no answer", "mars"],
    phrases: [
      "why does it say insufficient evidence",
      "insufficient evidence",
      "not enough evidence",
    ],
    reply: {
      text:
        "Insufficient evidence means no chunk in your library strongly matched your question. " +
        "The app will not invent an answer — you get a clear message and no citations. Upload related docs or rephrase, then try Research again.",
      links: [
        { label: "Start Research", to: "/" },
        { label: "Open Library", to: "/library" },
      ],
    },
  },
  {
    id: "search",
    keywords: ["search", "semantic", "retrieval", "top", "similarity"],
    reply: {
      text:
        "Search runs semantic retrieval over indexed chunks (cosine similarity). You see matching excerpts and can open the document inspector. " +
        "Hybrid search and reranking are not implemented.",
      links: [{ label: "Open Search", to: "/search" }],
    },
  },
  {
    id: "history",
    keywords: ["history", "session", "saved", "conversation"],
    reply: {
      text:
        "Research History lists sessions created when you submit questions on the Research page. Open a session to review saved Q&A. " +
        "Deleting a session removes stored messages only, not your documents.",
      links: [{ label: "View History", to: "/history" }],
    },
  },
  {
    id: "collections",
    keywords: ["collection", "group", "organize"],
    reply: {
      text:
        "Collections let you name groups and attach library documents via the API/UI. They help organize corpora; membership counts come from the server.",
      links: [{ label: "Open Collections", to: "/collections" }],
    },
  },
  {
    id: "observatory",
    keywords: ["observatory", "evaluation", "eval", "recall", "precision", "mrr", "golden"],
    reply: {
      text:
        "Evaluation Observatory runs retrieval metrics (Recall@k, Precision@k, MRR) on the committed golden fixture. " +
        "Runs start only when you click the button — not on page load. Metrics measure ranking quality, not factual truth.",
      links: [{ label: "Open Observatory", to: "/observatory" }],
    },
  },
  {
    id: "agent",
    keywords: ["agent", "research", "tool", "automation", "enabled"],
    phrases: ["agent activity"],
    reply: {
      text:
        "Agent Activity runs a bounded research agent with a fixed tool allowlist and limits (tool count, wall-clock timeout). " +
        "It is off unless AGENT_ENABLED=true on the server (restart required). It is not a general chatbot and uses the same evidence ideas as /ask.",
      links: [
        { label: "Open Agent", to: "/agent" },
        { label: "Open Settings", to: "/settings" },
      ],
    },
  },
  {
    id: "settings",
    keywords: ["settings", "config", "environment", "ollama", "mock", "provider", "api"],
    reply: {
      text:
        "Settings shows read-only public configuration: embedding provider (fake vs local), LLM (mock vs Ollama), upload limits, and agent flag. " +
        "Change .env on the server and restart the API — the UI cannot write config. No authentication in this MVP.",
      links: [{ label: "Open Settings", to: "/settings" }],
    },
  },
  {
    id: "start",
    keywords: ["start", "new", "begin", "first", "get started"],
    phrases: ["where to start", "how to start"],
    reply: {
      text:
        "New user path: (1) Start API + UI, (2) Library → upload sample.md, (3) Research → ask about your doc, (4) check Evidence and try an off-topic question to see insufficient evidence.",
      links: [
        { label: "Open Library", to: "/library" },
        { label: "Start Research", to: "/" },
      ],
    },
  },
  {
    id: "limitations",
    keywords: ["limit", "limitation", "pdf", "auth", "production", "security"],
    reply: {
      text:
        "Known limits: no PDF ingest, no login/auth, not public-production-ready, no document graph, mock/fake providers for offline demo. " +
        "Intended for localhost or trusted private network.",
      links: [{ label: "Open Settings", to: "/settings" }],
    },
  },
  {
    id: "document_question",
    keywords: ["my document", "my file", "rollback", "flyway", "what does my"],
    phrases: ["in my document", "from my upload"],
    reply: {
      text:
        "Questions about your actual file content need the Research assistant, not this guide. Upload in Library if needed, then ask on Research — you'll get citations from retrieved chunks.",
      links: [{ label: "Start Research", to: "/" }],
    },
  },
];

const FALLBACK: GuideReply = {
  text:
    "I'm not sure about that. I'm a fixed FAQ guide, not a live LLM. Try one of the suggestions or ask about upload, Research, citations, insufficient evidence, or a page name (Library, Search, History, Agent, Settings).",
  followUpChips: [...SUGGESTED_CHIPS],
};

function normalize(text: string): string {
  return text
    .toLowerCase()
    .replace(/[^\w\s]/g, " ")
    .replace(/\s+/g, " ")
    .trim();
}

function scoreEntry(query: string, entry: GuideMessage): number {
  let score = 0;
  for (const phrase of entry.phrases ?? []) {
    if (query.includes(normalize(phrase))) score += 10;
  }
  const tokens = new Set(query.split(" ").filter((t) => t.length > 1));
  for (const kw of entry.keywords) {
    if (tokens.has(kw) || query.includes(kw)) score += 2;
  }
  return score;
}

export function matchGuideQuery(raw: string): GuideReply {
  const query = normalize(raw);
  if (!query) return WELCOME_REPLY;

  let best: GuideMessage | null = null;
  let bestScore = 0;
  for (const entry of FAQ_ENTRIES) {
    const s = scoreEntry(query, entry);
    if (s > bestScore) {
      bestScore = s;
      best = entry;
    }
  }
  if (best && bestScore >= 3) {
    return best.reply;
  }
  return FALLBACK;
}
