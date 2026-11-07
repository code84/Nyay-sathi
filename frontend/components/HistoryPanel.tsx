"use client";
import type { Conversation } from "@/lib/useHistory";

function formatDate(ts: number) {
  const d = new Date(ts);
  const now = new Date();
  const diffDays = Math.floor((now.getTime() - d.getTime()) / 86400000);
  if (diffDays === 0) return "Today";
  if (diffDays === 1) return "Yesterday";
  if (diffDays < 7) return `${diffDays} days ago`;
  return d.toLocaleDateString("en-IN", { day: "numeric", month: "short" });
}

interface Props {
  open: boolean;
  onClose: () => void;
  conversations: Conversation[];
  activeId: string;
  onSelect: (conv: Conversation) => void;
  onNewCase: () => void;
  onDelete: (id: string) => void;
  isDark: boolean;
}

export default function HistoryPanel({ open, onClose, conversations, activeId, onSelect, onNewCase, onDelete, isDark }: Props) {
  const panel = isDark
    ? "bg-[#0d1526] border-r border-white/10 text-neutral-100"
    : "bg-white border-r border-slate-200 text-slate-900";
  const item = (active: boolean) => isDark
    ? active ? "bg-[#14B8A6]/15 border-[#14B8A6]/40 text-white" : "border-transparent text-neutral-300 hover:bg-white/5 hover:text-white"
    : active ? "bg-teal-50 border-teal-400 text-slate-900" : "border-transparent text-slate-600 hover:bg-slate-50 hover:text-slate-900";

  return (
    <>
      {/* Backdrop */}
      <div
        className={`fixed inset-0 z-40 bg-black/50 transition-opacity duration-300 ${open ? "opacity-100" : "pointer-events-none opacity-0"}`}
        onClick={onClose}
      />

      {/* Panel */}
      <aside className={`fixed left-0 top-0 z-50 flex h-full w-72 flex-col transition-transform duration-300 ${panel} ${open ? "translate-x-0" : "-translate-x-full"}`}>
        {/* Header */}
        <div className={`flex items-center justify-between px-4 py-4 border-b ${isDark ? "border-white/10" : "border-slate-200"}`}>
          <span className="text-sm font-semibold tracking-wide text-[#14B8A6]">Case History</span>
          <button onClick={onClose} aria-label="Close panel"
            className={`rounded-lg p-1.5 transition-colors ${isDark ? "hover:bg-white/10 text-neutral-400" : "hover:bg-slate-100 text-slate-500"}`}>
            <svg viewBox="0 0 24 24" className="h-4 w-4" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
              <path d="M18 6L6 18M6 6l12 12" />
            </svg>
          </button>
        </div>

        {/* New Case button */}
        <div className="px-3 pt-3">
          <button onClick={() => { onNewCase(); onClose(); }}
            className="flex w-full items-center gap-2.5 rounded-xl bg-gradient-to-r from-[#14B8A6] to-[#0D9488] px-4 py-2.5 text-sm font-semibold text-black transition-all hover:brightness-110">
            <svg viewBox="0 0 24 24" className="h-4 w-4" fill="none" stroke="currentColor" strokeWidth="2.5" strokeLinecap="round" strokeLinejoin="round">
              <path d="M12 5v14M5 12h14" />
            </svg>
            New Case
          </button>
        </div>

        {/* Conversation list */}
        <div className="flex-1 overflow-y-auto px-3 py-3 space-y-1">
          {conversations.length === 0 ? (
            <p className={`px-2 py-8 text-center text-xs ${isDark ? "text-neutral-500" : "text-slate-400"}`}>
              No saved cases yet.<br />Start a conversation to save it here.
            </p>
          ) : (
            conversations.map((conv) => (
              <div key={conv.id}
                className={`group flex items-start gap-2 rounded-xl border px-3 py-2.5 cursor-pointer transition-all ${item(conv.id === activeId)}`}
                onClick={() => { onSelect(conv); onClose(); }}>
                {/* Icon */}
                <svg viewBox="0 0 24 24" className="mt-0.5 h-4 w-4 shrink-0 text-[#14B8A6]" fill="none" stroke="currentColor" strokeWidth="1.8" strokeLinecap="round" strokeLinejoin="round">
                  <path d="M21 15a2 2 0 0 1-2 2H7l-4 4V5a2 2 0 0 1 2-2h14a2 2 0 0 1 2 2z" />
                </svg>
                {/* Text */}
                <div className="min-w-0 flex-1">
                  <p className="truncate text-sm font-medium leading-snug">{conv.title}</p>
                  <p className={`mt-0.5 text-xs ${isDark ? "text-neutral-500" : "text-slate-400"}`}>{formatDate(conv.updatedAt)}</p>
                </div>
                {/* Delete */}
                <button
                  onClick={(e) => { e.stopPropagation(); onDelete(conv.id); }}
                  aria-label="Delete conversation"
                  className={`mt-0.5 shrink-0 rounded p-0.5 opacity-0 transition-opacity group-hover:opacity-100 ${isDark ? "hover:bg-white/10 text-neutral-500 hover:text-red-400" : "hover:bg-slate-100 text-slate-400 hover:text-red-500"}`}>
                  <svg viewBox="0 0 24 24" className="h-3.5 w-3.5" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                    <path d="M3 6h18M8 6V4h8v2M19 6l-1 14H6L5 6" />
                  </svg>
                </button>
              </div>
            ))
          )}
        </div>

        {/* Footer */}
        <div className={`border-t px-4 py-3 text-xs ${isDark ? "border-white/10 text-neutral-600" : "border-slate-200 text-slate-400"}`}>
          Stored locally on your device
        </div>
      </aside>
    </>
  );
}
