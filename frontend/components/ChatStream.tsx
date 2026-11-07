"use client";
import { Fragment, useEffect, useRef, useState } from "react";
import { chat } from "@/lib/api";
import type { Answer, CaseState, Lang, Msg } from "@/lib/types";
import type { Strings } from "@/lib/i18n";
import CitationChip from "./CitationChip";
import EscalationCard from "./EscalationCard";
import SourcePanel from "./SourcePanel";

const TAG = /(\[[A-Z]-\d{3}\])/g;
// Strip citation tags and extra whitespace before speaking
function toSpeakable(text: string) {
  return text.replace(TAG, "").replace(/\s+/g, " ").trim();
}

function MessageText({ text, onOpen }: { text: string; onOpen: (id: string) => void }) {
  return <>{text.split(TAG).map((part, i) => {
    const m = part.match(/^\[([A-Z]-\d{3})\]$/);
    return m ? <CitationChip key={i} id={m[1]} onOpen={onOpen} /> : <Fragment key={i}>{part}</Fragment>;
  })}</>;
}

type Props = {
  lang: Lang; t: Strings; greeting?: string; suggestions?: string[]; note?: string;
  initialMsgs?: Msg[]; initialCaseState?: CaseState;
  onUpdate?: (msgs: Msg[], caseState: CaseState) => void;
};

export default function ChatStream({ lang, t, greeting, suggestions = [], note, initialMsgs, initialCaseState, onUpdate }: Props) {
  const [msgs, setMsgs] = useState<Msg[]>(initialMsgs ?? []);
  const [input, setInput] = useState("");
  const [busy, setBusy] = useState(false);
  const [source, setSource] = useState<string | null>(null);
  const [attachedFile, setAttachedFile] = useState<File | null>(null);
  const [isListening, setIsListening] = useState(false);
  const [voiceSupported, setVoiceSupported] = useState(false);
  const [ttsSupported, setTtsSupported] = useState(false);
  const [speakingId, setSpeakingId] = useState<number | null>(null);
  const caseState = useRef<CaseState>(initialCaseState ?? null);
  const nextId = useRef((initialMsgs?.length ?? 0) + 1);
  const bottom = useRef<HTMLDivElement>(null);
  const fileRef = useRef<HTMLInputElement>(null);
  // eslint-disable-next-line @typescript-eslint/no-explicit-any
  const recognitionRef = useRef<any>(null);

  useEffect(() => {
    bottom.current?.scrollIntoView({ behavior: "smooth", block: "end" });
  }, [msgs]);

  // Call onUpdate when a response finishes (busy â†’ false)
  const prevBusy = useRef(false);
  useEffect(() => {
    if (prevBusy.current && !busy && msgs.length > 0) {
      onUpdate?.(msgs, caseState.current);
    }
    prevBusy.current = busy;
  }, [busy, msgs, onUpdate]);

  useEffect(() => {
    // eslint-disable-next-line @typescript-eslint/no-explicit-any
    const SR = (window as any).SpeechRecognition || (window as any).webkitSpeechRecognition;
    setVoiceSupported(!!SR);
    setTtsSupported(!!window.speechSynthesis);
  }, []);

  // â”€â”€ TTS â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€
  function speak(msgId: number, text: string) {
    if (!window.speechSynthesis) return;
    if (speakingId === msgId) {
      window.speechSynthesis.cancel();
      setSpeakingId(null);
      return;
    }
    window.speechSynthesis.cancel();
    const utt = new SpeechSynthesisUtterance(toSpeakable(text));
    utt.lang = lang === "hi" ? "hi-IN" : "en-IN";
    utt.rate = 0.92;
    utt.pitch = 1;
    // Pick a natural-sounding voice if available
    const voices = window.speechSynthesis.getVoices();
    const preferred = voices.find(v =>
      v.lang.startsWith(lang === "hi" ? "hi" : "en") && !v.name.toLowerCase().includes("google")
    ) || voices.find(v => v.lang.startsWith(lang === "hi" ? "hi" : "en"));
    if (preferred) utt.voice = preferred;
    utt.onend = () => setSpeakingId(null);
    utt.onerror = () => setSpeakingId(null);
    setSpeakingId(msgId);
    window.speechSynthesis.speak(utt);
  }

  function stopSpeaking() {
    window.speechSynthesis?.cancel();
    setSpeakingId(null);
  }

  // â”€â”€ STT â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€
  function startListening() {
    // eslint-disable-next-line @typescript-eslint/no-explicit-any
    const SR = (window as any).SpeechRecognition || (window as any).webkitSpeechRecognition;
    if (!SR) return;
    stopSpeaking(); // stop TTS if speaking
    const recognition = new SR();
    recognition.lang = lang === "hi" ? "hi-IN" : "en-IN";
    recognition.continuous = false;
    recognition.interimResults = true;
    // eslint-disable-next-line @typescript-eslint/no-explicit-any
    recognition.onresult = (e: any) => {
      const transcript = Array.from(e.results as any[])
        // eslint-disable-next-line @typescript-eslint/no-explicit-any
        .map((r: any) => r[0].transcript)
        .join("");
      setInput(transcript);
    };
    recognition.onend = () => setIsListening(false);
    recognition.onerror = () => setIsListening(false);
    recognitionRef.current = recognition;
    recognition.start();
    setIsListening(true);
  }

  function stopListening() {
    recognitionRef.current?.stop();
    setIsListening(false);
  }

  function toggleVoice() {
    isListening ? stopListening() : startListening();
  }

  async function send(override?: string) {
    const message = (override ?? input).trim();
    if (!message || busy) return;
    stopSpeaking();
    const fileLabel = attachedFile ? ` [Attached: ${attachedFile.name}]` : "";
    const botId = nextId.current + 1;
    setMsgs((m) => [
      ...m,
      { id: nextId.current, role: "user", text: message, file: attachedFile?.name },
      { id: botId, role: "bot", text: "", pending: true },
    ]);
    nextId.current += 2;
    setInput("");
    setAttachedFile(null);
    setBusy(true);
    const patch = (p: Partial<Msg>) => setMsgs((m) => m.map((x) => (x.id === botId ? { ...x, ...p } : x)));
    try {
      let draft = "";
      for await (const ev of chat({ message: message + fileLabel, language: lang, case_state: caseState.current })) {
        if (ev.type === "token") { draft += ev.text; patch({ text: draft }); }
        else { caseState.current = ev.case_state; patch({ text: ev.answer.text, answer: ev.answer, pending: false }); }
      }
      patch({ pending: false });
    } catch (err) {
      const msg = err instanceof Error && err.message === "rate_limit"
        ? "You've sent too many messages. Please wait a moment and try again."
        : err instanceof Error && err.message === "unavailable"
        ? "The assistant is temporarily unavailable. Please try again in a few seconds."
        : t.error;
      patch({ text: msg, pending: false, error: true });
    } finally {
      setBusy(false);
    }
  }

  return (
    <div className="flex min-h-0 flex-1 flex-col">
      {/* Messages */}
      <div className="flex-1 space-y-4 overflow-y-auto px-4 py-5" aria-live="polite">
        {msgs.length === 0 && (
          <div className="mx-auto mt-6 max-w-2xl text-center sm:mt-12">
            <h2 className="text-xl font-semibold text-white">{greeting ?? t.emptyTitle}</h2>
            <div className="mt-6 flex flex-wrap justify-center gap-3">
              {(suggestions.length ? suggestions : [t.example]).map((s) => (
                <button key={s} type="button" onClick={() => send(s)}
                  className="rounded-xl border border-white/10 bg-[#0e1626] px-4 py-2.5 text-left text-sm text-neutral-100 transition-colors hover:border-[#14B8A6]/60 hover:bg-[#16223a]">
                  {s}
                </button>
              ))}
            </div>
          </div>
        )}
        {msgs.map((m) => (
          <div key={m.id} className={m.role === "user" ? "flex justify-end" : "flex justify-start"}>
            <div className={`group relative max-w-[88%] rounded-2xl px-4 py-2.5 text-sm leading-relaxed sm:max-w-[75%] ${
              m.role === "user"
                ? "bg-gradient-to-b from-[#2DD4BF] to-[#0D9488] font-medium text-black"
                : m.error
                  ? "bg-red-950/60 text-red-200"
                  : "bg-[#1b2740] text-neutral-100"
            }`}>
              {/* Attached file chip */}
              {m.file && (
                <div className="mb-2 flex items-center gap-1.5 rounded-lg bg-black/20 px-2.5 py-1.5 text-xs">
                  <svg viewBox="0 0 24 24" className="h-3.5 w-3.5 shrink-0" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                    <path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z" />
                    <polyline points="14,2 14,8 20,8" />
                  </svg>
                  <span className="max-w-[180px] truncate">{m.file}</span>
                </div>
              )}
              {m.pending ? (
                <>
                  {m.text && <p className="opacity-50">{m.text}</p>}
                  <p className="mt-1 text-xs italic opacity-70">{t.checking}</p>
                </>
              ) : (
                <>
                  <p className="whitespace-pre-wrap"><MessageText text={m.text} onOpen={setSource} /></p>
                  {m.answer?.confidence === "unsure" && !m.answer.flags.length && (
                    <p className="mt-2 text-xs italic opacity-80">{t.unsure}</p>
                  )}
                  {m.answer && (
                    <EscalationCard flags={m.answer.flags} urgentTitle={t.urgentTitle} warnTitle={t.warnTitle} />
                  )}
                  {/* TTS button â€” only on bot messages with text */}
                  {m.role === "bot" && !m.error && m.text && ttsSupported && (
                    <button
                      type="button"
                      onClick={() => speak(m.id, m.text)}
                      aria-label={speakingId === m.id ? "Stop speaking" : "Read aloud"}
                      title={speakingId === m.id ? "Stop" : "Read aloud"}
                      className={`mt-2 flex items-center gap-1.5 rounded-lg px-2 py-1 text-xs transition-colors ${
                        speakingId === m.id
                          ? "bg-[#14B8A6]/20 text-[#2DD4BF]"
                          : "text-neutral-500 hover:bg-white/5 hover:text-[#14B8A6]"
                      }`}
                    >
                      {speakingId === m.id ? (
                        <>
                          <svg viewBox="0 0 24 24" className="h-3.5 w-3.5 animate-pulse" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                            <rect x="6" y="4" width="4" height="16"/><rect x="14" y="4" width="4" height="16"/>
                          </svg>
                          Stop
                        </>
                      ) : (
                        <>
                          <svg viewBox="0 0 24 24" className="h-3.5 w-3.5" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                            <polygon points="11 5 6 9 2 9 2 15 6 15 11 19 11 5"/>
                            <path d="M19.07 4.93a10 10 0 0 1 0 14.14M15.54 8.46a5 5 0 0 1 0 7.07"/>
                          </svg>
                          Listen
                        </>
                      )}
                    </button>
                  )}
                </>
              )}
            </div>
          </div>
        ))}
        <div ref={bottom} />
      </div>

      {/* Attached file preview bar */}
      {attachedFile && (
        <div className="mx-4 mb-2 flex items-center gap-2 rounded-xl border border-[#14B8A6]/40 bg-[#0e1626] px-3 py-2 text-xs text-[#2DD4BF]">
          <svg viewBox="0 0 24 24" className="h-4 w-4 shrink-0" fill="none" stroke="currentColor" strokeWidth="1.8" strokeLinecap="round" strokeLinejoin="round">
            <path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z" />
            <polyline points="14,2 14,8 20,8" />
          </svg>
          <span className="flex-1 truncate">{attachedFile.name}</span>
          <span className="text-neutral-500">({(attachedFile.size / 1024).toFixed(1)} KB)</span>
          <button type="button" onClick={() => setAttachedFile(null)} aria-label="Remove attachment"
            className="ml-1 rounded px-1 hover:text-white">âœ•</button>
        </div>
      )}

      {/* Listening indicator */}
      {isListening && (
        <div className="mx-4 mb-2 flex items-center gap-2 rounded-xl border border-red-500/40 bg-red-950/40 px-3 py-2 text-xs text-red-300">
          <span className="relative flex h-2.5 w-2.5 shrink-0">
            <span className="absolute inline-flex h-full w-full animate-ping rounded-full bg-red-400 opacity-75" />
            <span className="relative inline-flex h-2.5 w-2.5 rounded-full bg-red-500" />
          </span>
          {lang === "hi" ? "à¤¸à¥à¤¨ à¤°à¤¹à¤¾ à¤¹à¥‚à¤â€¦ à¤¬à¥‹à¤²à¤¿à¤" : "Listeningâ€¦ speak now"}
        </div>
      )}

      {/* Speaking indicator */}
      {speakingId !== null && (
        <div className="mx-4 mb-2 flex items-center gap-2 rounded-xl border border-[#14B8A6]/40 bg-[#0e1626] px-3 py-2 text-xs text-[#2DD4BF]">
          <span className="relative flex h-2.5 w-2.5 shrink-0">
            <span className="absolute inline-flex h-full w-full animate-ping rounded-full bg-[#14B8A6] opacity-75" />
            <span className="relative inline-flex h-2.5 w-2.5 rounded-full bg-[#14B8A6]" />
          </span>
          {lang === "hi" ? "à¤¬à¥‹à¤² à¤°à¤¹à¤¾ à¤¹à¥‚à¤â€¦" : "Speakingâ€¦"}
          <button type="button" onClick={stopSpeaking} className="ml-auto text-neutral-400 hover:text-white">âœ•</button>
        </div>
      )}

      {/* Input bar */}
      <div className="px-4 pb-[max(0.75rem,env(safe-area-inset-bottom))] pt-2">
        <input
          ref={fileRef}
          type="file"
          accept=".pdf,.png,.jpg,.jpeg,.doc,.docx,.txt"
          className="hidden"
          onChange={(e) => {
            const f = e.target.files?.[0];
            if (f) setAttachedFile(f);
            e.target.value = "";
          }}
        />
        <form
          onSubmit={(e) => { e.preventDefault(); send(); }}
          className="flex items-center gap-2 rounded-full border border-[#14B8A6]/70 bg-[#0e1626] p-1.5 pl-2"
        >
          {/* Star icon */}
          <span aria-hidden className="flex h-9 w-9 shrink-0 items-center justify-center rounded-full bg-[#14B8A6] text-black">
            <svg viewBox="0 0 24 24" className="h-5 w-5" fill="none" stroke="currentColor" strokeWidth="1.8" strokeLinecap="round" strokeLinejoin="round">
              <path d="M12 3l1.8 4.7L18.5 9.5l-4.7 1.8L12 16l-1.8-4.7L5.5 9.5l4.7-1.8L12 3z" />
              <path d="M19 15l.8 2.2L22 18l-2.2.8L19 21l-.8-2.2L16 18l2.2-.8L19 15z" />
            </svg>
          </span>

          <input
            value={input}
            onChange={(e) => setInput(e.target.value)}
            placeholder={t.placeholder}
            aria-label={t.placeholder}
            className="min-w-0 flex-1 bg-transparent px-1 py-2 text-base text-neutral-100 placeholder:text-neutral-500 focus:outline-none"
          />

          {/* Attach button */}
          <button type="button" onClick={() => fileRef.current?.click()} aria-label="Attach document"
            title="Attach document"
            className="flex h-9 w-9 shrink-0 items-center justify-center rounded-full text-neutral-400 transition-colors hover:bg-white/10 hover:text-[#14B8A6]">
            <svg viewBox="0 0 24 24" className="h-5 w-5" fill="none" stroke="currentColor" strokeWidth="1.8" strokeLinecap="round" strokeLinejoin="round">
              <path d="M21.44 11.05l-9.19 9.19a6 6 0 0 1-8.49-8.49l9.19-9.19a4 4 0 0 1 5.66 5.66l-9.2 9.19a2 2 0 0 1-2.83-2.83l8.49-8.48" />
            </svg>
          </button>

          {/* Voice input button */}
          {voiceSupported && (
            <button type="button" onClick={toggleVoice}
              aria-label={isListening ? "Stop listening" : "Speak your question"}
              title={isListening ? "Stop listening" : "Speak your question"}
              className={`flex h-9 w-9 shrink-0 items-center justify-center rounded-full transition-colors ${
                isListening ? "bg-red-500 text-white" : "text-neutral-400 hover:bg-white/10 hover:text-[#14B8A6]"
              }`}>
              <svg viewBox="0 0 24 24" className="h-5 w-5" fill="none" stroke="currentColor" strokeWidth="1.8" strokeLinecap="round" strokeLinejoin="round">
                <path d="M12 1a3 3 0 0 0-3 3v8a3 3 0 0 0 6 0V4a3 3 0 0 0-3-3z" />
                <path d="M19 10v2a7 7 0 0 1-14 0v-2" />
                <line x1="12" y1="19" x2="12" y2="23" />
                <line x1="8" y1="23" x2="16" y2="23" />
              </svg>
            </button>
          )}

          {/* Send button */}
          <button type="submit" disabled={busy || !input.trim()} aria-label={t.send}
            className="flex h-10 w-10 shrink-0 items-center justify-center rounded-full bg-[#14B8A6] text-black hover:brightness-110 disabled:cursor-not-allowed disabled:opacity-40">
            <svg viewBox="0 0 24 24" className="h-5 w-5" fill="none" stroke="currentColor" strokeWidth="1.8" strokeLinecap="round" strokeLinejoin="round">
              <path d="M22 2L11 13" /><path d="M22 2l-7 20-4-9-9-4 20-7z" />
            </svg>
          </button>
        </form>
        {note && <p className="mt-2 text-center text-xs text-neutral-500">{note}</p>}
      </div>

      <SourcePanel id={source} onClose={() => setSource(null)} t={t} />
    </div>
  );
}
