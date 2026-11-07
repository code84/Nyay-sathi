"use client";
import type { Lang } from "@/lib/types";

export default function LangToggle({ lang, onChange, label }: { lang: Lang; onChange: (l: Lang) => void; label: string }) {
  const base = "px-3 py-1.5 text-sm font-medium transition-colors";
  const on = "bg-[#14B8A6] text-black";
  const off = "text-neutral-300 hover:bg-white/10";
  return (
    <div role="group" aria-label={label} className="inline-flex overflow-hidden rounded-lg border border-[#14B8A6]/50">
      <button type="button" aria-pressed={lang === "en"} onClick={() => onChange("en")} className={`${base} ${lang === "en" ? on : off}`}>EN</button>
      <button type="button" aria-pressed={lang === "hi"} onClick={() => onChange("hi")} className={`${base} ${lang === "hi" ? on : off}`}>हिं</button>
    </div>
  );
}
