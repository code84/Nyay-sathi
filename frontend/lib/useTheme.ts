"use client";
import { useEffect, useState } from "react";

export type Theme = "dark" | "light";

export function useTheme(): [Theme, () => void] {
  const [theme, setTheme] = useState<Theme>("dark");

  useEffect(() => {
    const stored = localStorage.getItem("ns-theme") as Theme | null;
    if (stored === "light" || stored === "dark") setTheme(stored);
  }, []);

  const toggle = () => {
    setTheme((t) => {
      const next: Theme = t === "dark" ? "light" : "dark";
      localStorage.setItem("ns-theme", next);
      return next;
    });
  };

  return [theme, toggle];
}
