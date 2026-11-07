import type { Flag } from "@/lib/types";

// Internal checker codes — never shown to users
const INTERNAL_CODES = new Set([
  "bad_quote", "unknown_citation", "no_citation",
  "unsupported_section", "unsupported_act", "unsupported_case",
  "unsupported_number", "uncited_legal_claim", "fallback",
]);

// Only show flags the user can genuinely act on
export default function EscalationCard({ flags, urgentTitle, warnTitle }: { flags: Flag[]; urgentTitle: string; warnTitle: string }) {
  const shown = flags.filter((f) => f.severity !== "info" && !INTERNAL_CODES.has(f.code));
  if (!shown.length) return null;
  const urgent = shown.some((f) => f.severity === "urgent");
  const tone = urgent ? "border-red-500/60 bg-red-950/60 text-red-200" : "border-amber-500/60 bg-amber-500/10 text-amber-200";
  return (
    <div role={urgent ? "alert" : "note"} className={`mt-2 rounded-lg border p-3 text-sm ${tone}`}>
      <p className="font-semibold">{urgent ? urgentTitle : warnTitle}</p>
      <ul className="mt-1 list-disc space-y-0.5 pl-5">
        {shown.map((f, i) => <li key={i}>{f.message}</li>)}
      </ul>
    </div>
  );
}
