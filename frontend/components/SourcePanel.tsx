"use client";
import { useEffect, useRef, useState } from "react";
import { getSource } from "@/lib/api";
import { sans, serif } from "@/lib/theme";
import type { LibraryItem } from "@/lib/types";
import type { Strings } from "@/lib/i18n";

export default function SourcePanel({ id, onClose, t }: { id: string | null; onClose: () => void; t: Strings }) {
  const [res, setRes] = useState<{ id: string; item?: LibraryItem; error?: boolean } | null>(null);
  const closeRef = useRef<HTMLButtonElement>(null);

  useEffect(() => {
    if (!id) return;
    let live = true;
    getSource(id).then((item) => { if (live) setRes({ id, item }); })
                 .catch(() => { if (live) setRes({ id, error: true }); });
    return () => { live = false; };
  }, [id]);

  useEffect(() => {
    if (!id) return;
    closeRef.current?.focus();
    const h = (e: KeyboardEvent) => e.key === "Escape" && onClose();
    window.addEventListener("keydown", h);
    return () => window.removeEventListener("keydown", h);
  }, [id, onClose]);

  if (!id) return null;
  const mine = res?.id === id ? res : null;     // ignore a result that belongs to a previously opened source
  const item = mine?.item ?? null;
  const state = mine?.item ? "ok" : mine?.error ? "error" : "loading";
  const needsCheck = item && item.source_confidence.trim().toLowerCase() !== "primary";

  return (
    <div className="fixed inset-0 z-40 flex items-end justify-center bg-black/60 sm:items-stretch sm:justify-end" onClick={onClose}>
      <aside role="dialog" aria-modal="true" aria-label={`${t.source} ${id}`} onClick={(e) => e.stopPropagation()} style={sans}
        className="flex max-h-[85dvh] w-full flex-col rounded-t-2xl border border-[#14B8A6]/40 bg-[#101828] text-neutral-100 shadow-xl sm:max-h-none sm:w-[28rem] sm:rounded-none sm:border-y-0 sm:border-r-0">
        <header className="flex items-start justify-between gap-3 border-b border-white/10 p-4">
          <div>
            <p className="text-xs font-semibold text-[#2DD4BF]">{t.source} · {id}</p>
            <h2 className="mt-0.5 text-base font-semibold" style={serif}>{item?.title ?? t.loading}</h2>
          </div>
          <button ref={closeRef} type="button" onClick={onClose} className="rounded-md px-2 py-1 text-sm text-neutral-300 hover:bg-white/10">{t.close}</button>
        </header>
        <div className="space-y-4 overflow-y-auto p-4 text-sm">
          {state === "loading" && <p className="text-neutral-400">{t.loading}</p>}
          {state === "error" && <p className="text-red-400">{t.loadError}</p>}
          {item && (<>
            <div className="flex flex-wrap items-center gap-2 text-xs">
              <span className="rounded bg-white/10 px-2 py-0.5">{t.verifiedOn}: {item.last_verified}</span>
              {needsCheck && <span className="rounded bg-amber-500/20 px-2 py-0.5 font-medium text-amber-200">{t.needsCheck}</span>}
            </div>
            <section>
              <h3 className="font-semibold text-[#2DD4BF]">{t.excerptTitle}</h3>
              <ul className="mt-1 space-y-2">
                {item.excerpt.map((q, i) => <li key={i} className="border-l-4 border-[#14B8A6] pl-3 text-neutral-300">{q}</li>)}
              </ul>
            </section>
            <section><h3 className="font-semibold text-[#2DD4BF]">{t.meaningTitle}</h3><p className="mt-1 text-neutral-300">{item.meaning}</p></section>
            <section><h3 className="font-semibold text-[#2DD4BF]">{t.limitsTitle}</h3><p className="mt-1 text-neutral-300">{item.limits}</p></section>
            <a href={item.source_url} target="_blank" rel="noopener noreferrer"
               className="inline-block rounded-lg bg-gradient-to-b from-[#2DD4BF] to-[#0D9488] px-3 py-2 font-semibold text-black hover:brightness-110">{t.openOfficial} ↗</a>
            <p className="text-xs text-neutral-500">{item.source_name}</p>
          </>)}
        </div>
      </aside>
    </div>
  );
}
