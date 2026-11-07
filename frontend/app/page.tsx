"use client";
import { useCallback, useEffect, useRef, useState } from "react";
import Link from "next/link";
import ChatStream from "@/components/ChatStream";
import DisclaimerBanner from "@/components/DisclaimerBanner";
import Fonts from "@/components/Fonts";
import HistoryPanel from "@/components/HistoryPanel";
import LangToggle from "@/components/LangToggle";
import ThemeToggle from "@/components/ThemeToggle";
import { homeCopy } from "@/lib/homeCopy";
import { strings } from "@/lib/i18n";
import { goldBtn, sans, serif } from "@/lib/theme";
import { useLang } from "@/lib/useLang";
import { useTheme } from "@/lib/useTheme";
import { makeConversation, useHistory, type Conversation } from "@/lib/useHistory";
import type { CaseState, Msg } from "@/lib/types";

const wrap = "mx-auto w-full max-w-6xl px-4";
const pillIcons = [
  "M21 15a2 2 0 0 1-2 2H7l-4 4V5a2 2 0 0 1 2-2h14a2 2 0 0 1 2 2z",
  "M12 21a9 9 0 1 0 0-18 9 9 0 0 0 0 18zM3 12h18M12 3a14 14 0 0 1 0 18 14 14 0 0 1 0-18",
  "M10 13a5 5 0 0 0 7 0l3-3a5 5 0 0 0-7-7l-1 1M14 11a5 5 0 0 0-7 0l-3 3a5 5 0 0 0 7 7l1-1",
  "M12 3l8 3v6c0 5-3.5 8-8 9-4.5-1-8-4-8-9V6l8-3zM9 12l2 2 4-4",
];

function Icon({ d, className = "h-4 w-4" }: { d: string; className?: string }) {
  return <svg viewBox="0 0 24 24" className={className} fill="none" stroke="currentColor" strokeWidth="1.8" strokeLinecap="round" strokeLinejoin="round" aria-hidden><path d={d} /></svg>;
}

export default function Home() {
  const [lang, setLang] = useLang();
  const [theme, toggleTheme] = useTheme();
  const isDark = theme === "dark";
  const t = strings(lang);
  const c = homeCopy(lang);
  const { conversations, save, remove } = useHistory();
  const [sidebarOpen, setSidebarOpen] = useState(false);
  // Use a stable SSR-safe placeholder; replaced with a real ID on client mount
  const [activeConv, setActiveConv] = useState<Conversation>({
    id: "initial", title: "New case", createdAt: 0, updatedAt: 0,
    messages: [], caseState: null, lang,
  });
  useEffect(() => { setActiveConv(makeConversation(lang)); }, []);
  const chatRef = useRef<HTMLElement>(null);

  const handleUpdate = useCallback((msgs: Msg[], caseState: CaseState) => {
    if (msgs.length === 0) return;
    const title = msgs.find((m) => m.role === "user")?.text.slice(0, 50) ?? "New case";
    save({ ...activeConv, title, messages: msgs, caseState, updatedAt: 0, lang });
  }, [activeConv, lang, save]);

  const handleNewCase = useCallback(() => {
    setActiveConv(makeConversation(lang));
    setTimeout(() => chatRef.current?.scrollIntoView({ behavior: "smooth", block: "start" }), 100);
  }, [lang]);

  const handleSelect = useCallback((conv: Conversation) => {
    setActiveConv(conv);
    setTimeout(() => chatRef.current?.scrollIntoView({ behavior: "smooth", block: "start" }), 100);
  }, []);

  const navLink = isDark ? "text-neutral-300 hover:text-white" : "text-slate-600 hover:text-slate-900";

  return (
    <div className={`min-h-dvh scroll-smooth ${isDark ? "dark bg-[#0b1220] text-neutral-100" : "bg-slate-50 text-slate-900"}`} style={sans}>
      <Fonts />

      <HistoryPanel
        open={sidebarOpen}
        onClose={() => setSidebarOpen(false)}
        conversations={conversations}
        activeId={activeConv.id}
        onSelect={handleSelect}
        onNewCase={handleNewCase}
        onDelete={remove}
        isDark={isDark}
      />

      <DisclaimerBanner text={t.disclaimer} isDark={isDark} />

      <header className={`sticky top-0 z-30 border-b backdrop-blur ${isDark ? "border-white/5 bg-[#0b1220]/85" : "border-slate-200 bg-slate-50/90"}`}>
        <nav className={`${wrap} flex items-center justify-between gap-3 py-3`}>
          <div className="flex items-center gap-3">
            {/* Sidebar toggle */}
            <button onClick={() => setSidebarOpen(true)} aria-label="Open history"
              className={`flex h-9 w-9 items-center justify-center rounded-lg border transition-colors ${isDark ? "border-white/10 text-neutral-400 hover:bg-white/10 hover:text-white" : "border-slate-200 text-slate-500 hover:bg-slate-100 hover:text-slate-900"}`}>
              <svg viewBox="0 0 24 24" className="h-5 w-5" fill="none" stroke="currentColor" strokeWidth="1.8" strokeLinecap="round" strokeLinejoin="round">
                <path d="M3 12h18M3 6h18M3 18h18" />
              </svg>
            </button>
            <Link href="/" className="flex items-center gap-3">
              <Icon className="h-9 w-9 text-[#14B8A6]" d="M12 3v18M4 21h16M6 7H4l-1 5a3 3 0 0 0 6 0L8 7H6zM18 7h-2l-1 5a3 3 0 0 0 6 0l-1-5h-2zM6 9h2M18 9h2" />
              <span className="leading-tight">
                <span className="block text-xl font-bold">{t.appName}</span>
                <span className="block text-[11px] text-[#2DD4BF]">{c.tagline}</span>
              </span>
            </Link>
          </div>
          <div className="hidden items-center gap-8 text-[15px] font-medium md:flex">
            <a href="#features" className={navLink}>{c.navFeatures}</a>
            <a href="#how" className={navLink}>{c.navHow}</a>
            <a href="#faq" className={navLink}>{c.navFaq}</a>
          </div>
          <div className="flex items-center gap-3">
            <ThemeToggle theme={theme} onToggle={toggleTheme} />
            <LangToggle lang={lang} onChange={setLang} label={t.language} />
            <a href="#chat" className={`hidden rounded-xl px-5 py-2.5 text-sm sm:inline-block ${goldBtn}`}>{c.navCta}</a>
          </div>
        </nav>
      </header>

      <main>
        {/* Hero */}
        <section className={`${wrap} pt-10 text-center sm:pt-14`}>
          <span className={`inline-flex items-center gap-2 rounded-full border px-3 py-1 text-xs font-medium text-[#2DD4BF] ${isDark ? "border-white/10 bg-[#0e1626]" : "border-teal-200 bg-teal-50"}`}>
            <span className="h-2 w-2 rounded-full bg-emerald-500" />{c.badge}
          </span>
          <h1 className="mx-auto mt-5 max-w-4xl text-3xl font-bold leading-tight sm:text-5xl" style={serif}>
            {c.h1a} <span className="text-[#5EEAD4]">{c.h1b}</span>
          </h1>
          <p className={`mx-auto mt-5 max-w-2xl text-base sm:text-lg ${isDark ? "text-neutral-400" : "text-slate-500"}`}>{c.sub1}<br />{c.sub2}</p>
          <ul className="mt-7 flex flex-wrap justify-center gap-3">
            {c.pills.map((p, i) => (
              <li key={p} className={`inline-flex items-center gap-2 rounded-full border px-3.5 py-1.5 text-sm ${isDark ? "border-white/10 bg-[#0e1626] text-neutral-300" : "border-slate-200 bg-white text-slate-600"}`}>
                <span className="text-[#14B8A6]"><Icon d={pillIcons[i]} /></span>{p}
              </li>
            ))}
          </ul>
        </section>

        {/* Chat */}
        <section id="chat" ref={chatRef as React.RefObject<HTMLElement>} className={`${wrap} scroll-mt-24 py-10`}>
          <div className={`mx-auto flex h-[34rem] max-w-4xl flex-col overflow-hidden rounded-3xl border border-[#14B8A6]/70 shadow-[0_0_50px_rgba(20,184,166,0.12)] ${isDark ? "bg-[#111a2e]" : "bg-white"}`}>
            <ChatStream
              key={activeConv.id}
              lang={lang} t={t}
              greeting={c.greeting} suggestions={c.chips} note={c.note}
              initialMsgs={activeConv.messages}
              initialCaseState={activeConv.caseState}
              onUpdate={handleUpdate}
            />
          </div>
        </section>

        {/* Features */}
        <section id="features" className={`${wrap} scroll-mt-24 py-12`}>
          <h2 className="text-center text-3xl font-bold sm:text-4xl" style={serif}>{c.featuresTitle}</h2>
          <p className={`mx-auto mt-3 max-w-2xl text-center ${isDark ? "text-neutral-400" : "text-slate-500"}`}>{c.featuresSub}</p>
          <ul className="mt-10 grid gap-5 sm:grid-cols-2 lg:grid-cols-4">
            {c.laws.map((law) => (
              <li key={law.t} className={`flex flex-col rounded-2xl border p-6 transition-colors hover:border-[#14B8A6]/60 ${isDark ? "border-white/10 bg-[#101828]" : "border-slate-200 bg-white"}`}>
                <span className={`w-fit rounded-full px-2.5 py-0.5 text-xs font-semibold ${law.s === "live" ? "bg-emerald-500/15 text-emerald-500" : law.s === "soon" ? "bg-sky-500/15 text-sky-500" : "bg-slate-500/15 text-slate-500"}`}>{c.status[law.s]}</span>
                <h3 className="mt-4 text-xl font-semibold" style={serif}>{law.t}</h3>
                <p className="mt-1 text-sm font-medium text-[#2DD4BF]">{law.act}</p>
                <p className={`mt-3 flex-1 text-sm ${isDark ? "text-neutral-400" : "text-slate-500"}`}>{law.d}</p>
                <p className={`mt-4 border-t pt-3 text-xs ${isDark ? "border-white/10 text-neutral-500" : "border-slate-100 text-slate-400"}`}>{law.n} {c.sourcesWord}</p>
              </li>
            ))}
          </ul>
        </section>

        {/* How it works */}
        <section id="how" className={`${wrap} scroll-mt-24 py-12`}>
          <h2 className="text-center text-3xl font-bold sm:text-4xl" style={serif}>{c.howTitle}</h2>
          <p className={`mt-3 text-center ${isDark ? "text-neutral-400" : "text-slate-500"}`}>{c.howSub}</p>
          <ol className="mt-10 grid gap-5 md:grid-cols-3">
            {c.steps.map(([title, body], i) => (
              <li key={title} className={`rounded-2xl border p-6 ${isDark ? "border-white/10 bg-[#101828]" : "border-slate-200 bg-white"}`}>
                <span className="text-4xl font-bold text-[#14B8A6]/70" style={serif}>0{i + 1}</span>
                <h3 className="mt-3 text-lg font-semibold">{title}</h3>
                <p className={`mt-2 text-sm ${isDark ? "text-neutral-400" : "text-slate-500"}`}>{body}</p>
              </li>
            ))}
          </ol>
          <div className="mx-auto mt-8 max-w-3xl rounded-2xl border border-red-500/40 bg-red-950/40 p-6">
            <h3 className="text-lg font-semibold text-red-200">{c.wontTitle}</h3>
            <ul className="mt-3 space-y-1.5 text-red-200/90">
              {c.wont.map((w) => <li key={w} className="flex gap-2"><span aria-hidden>✕</span>{w}</li>)}
            </ul>
          </div>
        </section>

        {/* FAQ */}
        <section id="faq" className={`${wrap} scroll-mt-24 max-w-3xl py-12`}>
          <h2 className="text-center text-3xl font-bold sm:text-4xl" style={serif}>{c.faqTitle}</h2>
          <div className={`mt-8 divide-y rounded-2xl border ${isDark ? "divide-white/10 border-white/10 bg-[#101828]" : "divide-slate-100 border-slate-200 bg-white"}`}>
            {c.faqs.map(([q, a]) => (
              <details key={q} className="group p-5">
                <summary className="cursor-pointer list-none font-medium marker:hidden">
                  <span className="mr-2 inline-block text-[#14B8A6] transition-transform group-open:rotate-90" aria-hidden>›</span>{q}
                </summary>
                <p className={`mt-2 pl-5 text-sm ${isDark ? "text-neutral-400" : "text-slate-500"}`}>{a}</p>
              </details>
            ))}
          </div>
        </section>

        {/* CTA */}
        <section className={`${wrap} py-16 text-center`}>
          <h2 className="text-3xl font-bold" style={serif}>{c.ctaTitle}</h2>
          <a href="#chat" className={`mt-6 inline-block rounded-xl px-7 py-3 text-base ${goldBtn}`}>{c.ctaBtn}</a>
        </section>
      </main>

      <footer className={`border-t py-6 text-center text-xs ${isDark ? "border-white/5 text-neutral-500" : "border-slate-200 text-slate-400"}`}>{c.foot}</footer>
    </div>
  );
}
