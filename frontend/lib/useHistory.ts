"use client";
import { useCallback, useEffect, useState } from "react";
import type { CaseState, Lang, Msg } from "./types";

export interface Conversation {
  id: string;
  title: string;
  createdAt: number;
  updatedAt: number;
  messages: Msg[];
  caseState: CaseState;
  lang: Lang;
}

const KEY = "ns-history";
const MAX = 30;

function newId(): string {
  // crypto.randomUUID is available in both browser and Node.js — no Date.now needed
  try { return crypto.randomUUID(); }
  catch { return Math.random().toString(36).slice(2) + Math.random().toString(36).slice(2); }
}

function now(): number {
  // Safe timestamp — only called client-side (inside useEffect or event handlers)
  return typeof performance !== "undefined" ? Math.floor(performance.timeOrigin + performance.now()) : 0;
}

function load(): Conversation[] {
  try { return JSON.parse(localStorage.getItem(KEY) ?? "[]"); }
  catch { return []; }
}

function persist(list: Conversation[]) {
  localStorage.setItem(KEY, JSON.stringify(list));
}

export function makeConversation(lang: Lang): Conversation {
  const ts = now();
  return { id: newId(), title: "New case", createdAt: ts, updatedAt: ts, messages: [], caseState: null, lang };
}

export function useHistory() {
  const [conversations, setConversations] = useState<Conversation[]>([]);

  useEffect(() => { setConversations(load()); }, []);

  const save = useCallback((conv: Conversation) => {
    if (conv.messages.length === 0) return;
    setConversations((prev) => {
      const idx = prev.findIndex((c) => c.id === conv.id);
      const updated = idx >= 0
        ? prev.map((c) => (c.id === conv.id ? conv : c))
        : [conv, ...prev].slice(0, MAX);
      persist(updated);
      return updated;
    });
  }, []);

  const remove = useCallback((id: string) => {
    setConversations((prev) => {
      const updated = prev.filter((c) => c.id !== id);
      persist(updated);
      return updated;
    });
  }, []);

  const clear = useCallback(() => {
    persist([]);
    setConversations([]);
  }, []);

  return { conversations, save, remove, clear };
}
