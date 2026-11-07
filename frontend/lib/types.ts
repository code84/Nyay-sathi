// Mirrors backend/core/schemas.py and backend/core/flow.py. Keep in sync.
export type Lang = "en" | "hi";
export type Severity = "info" | "warn" | "urgent";

export interface Citation { item_id: string; quote?: string | null }
export interface Flag { code: string; severity: Severity; message: string }
export interface Answer {
  text: string;
  citations: Citation[];
  flags: Flag[];
  confidence: "library" | "general" | "unsure";
}
export interface LibraryItem {
  id: string;
  title: string;
  source_name: string;
  source_url: string;
  source_confidence: string;
  last_verified: string;
  status: string;
  excerpt: string[];
  meaning: string;
  limits: string;
}

// Chat message — shared between ChatStream and history
export interface Msg {
  id: number;
  role: "user" | "bot";
  text: string;
  answer?: Answer;
  pending?: boolean;
  error?: boolean;
  file?: string;
}

// The case state carried between turns (CaseFile on the backend)
export type CaseState = Record<string, unknown> | null;

// What the frontend sends to POST /chat
export interface ChatRequest { message: string; language: Lang; case_state: CaseState }

// What POST /chat actually returns (TurnResult from backend/core/flow.py)
export interface TurnResult {
  route: "case" | "notice" | "none";
  case: CaseState;
  questions: string[];
  ready: boolean;
  flags: Flag[];
  forum: Record<string, unknown> | null;
  answer: Answer | null;
  message: string;
}

// POST /chat streams NDJSON: one JSON object per line.
export type ChatEvent =
  | { type: "token"; text: string }
  | { type: "final"; answer: Answer; case_state: CaseState };
