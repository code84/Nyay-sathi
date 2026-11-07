import type { ChatEvent, ChatRequest, LibraryItem, TurnResult } from "./types";
import { mockChat, mockSource } from "./mock";

// Empty NEXT_PUBLIC_API_URL = mock mode (no backend needed).
const BASE = (process.env.NEXT_PUBLIC_API_URL ?? "").replace(/\/$/, "");
export const isMock = BASE === "";

export class ApiError extends Error {}

export async function* chat(req: ChatRequest): AsyncGenerator<ChatEvent> {
  if (isMock) { yield* mockChat(req); return; }

  const res = await fetch(`${BASE}/chat`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    // Backend expects { message, case } — map case_state → case
    body: JSON.stringify({ message: req.message, case: req.case_state }),
  });
  if (!res.ok) {
    if (res.status === 429) throw new ApiError("rate_limit");
    if (res.status === 503) throw new ApiError("unavailable");
    throw new ApiError(`chat failed: ${res.status}`);
  }

  // Backend returns a single TurnResult JSON (not a stream)
  const result: TurnResult = await res.json();

  // Merge any top-level danger flags into the answer flags
  const extraFlags = result.flags ?? [];

  if (result.answer) {
    const answer = {
      ...result.answer,
      flags: [...(result.answer.flags ?? []), ...extraFlags],
    };
    yield { type: "final", answer, case_state: result.case };
  } else {
    // Bot is asking follow-up questions, or query is out of scope / notice redirect
    const text =
      result.questions.length > 0
        ? result.questions.join("\n\n")
        : result.message || "Could you tell me a bit more about your situation?";
    yield {
      type: "final",
      answer: { text, citations: [], flags: extraFlags, confidence: "general" },
      case_state: result.case,
    };
  }
}

export async function getSource(id: string): Promise<LibraryItem> {
  if (isMock) return mockSource(id);
  const res = await fetch(`${BASE}/sources/${encodeURIComponent(id)}`);
  if (!res.ok) throw new ApiError(`source ${id}: ${res.status}`);
  return res.json();
}