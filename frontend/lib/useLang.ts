"use client";
import { useEffect, useSyncExternalStore } from "react";
import type { Lang } from "./types";

// Language choice, remembered across pages. Storage can fail (private mode), so keep an in-memory copy too.
let current: Lang | null = null;
const listeners = new Set<() => void>();
const read = (): Lang => {
  if (current) return current;
  try { return localStorage.getItem("lang") === "hi" ? "hi" : "en"; } catch { return "en"; }
};
const subscribe = (cb: () => void) => { listeners.add(cb); return () => { listeners.delete(cb); }; };
const write = (l: Lang) => {
  current = l;
  try { localStorage.setItem("lang", l); } catch {}
  listeners.forEach((cb) => cb());
};

export function useLang(): [Lang, (l: Lang) => void] {
  const lang = useSyncExternalStore(subscribe, read, () => "en" as Lang);
  useEffect(() => { document.documentElement.lang = lang; }, [lang]);
  return [lang, write];
}
