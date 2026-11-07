import type { CSSProperties } from "react";

// Dark + gold theme. Colours are written out in the components so Tailwind can see them.
export const sans: CSSProperties = { fontFamily: 'Inter, "Noto Sans Devanagari", system-ui, "Segoe UI", Arial, sans-serif' };
export const serif: CSSProperties = { fontFamily: '"Merriweather", "Noto Serif Devanagari", Georgia, "Times New Roman", serif' };
export const goldBtn = "bg-gradient-to-b from-[#2DD4BF] to-[#0D9488] font-semibold text-black shadow-[0_6px_20px_rgba(20,184,166,0.25)] hover:brightness-110 focus:outline-none focus:ring-2 focus:ring-[#2DD4BF] focus:ring-offset-2 focus:ring-offset-[#0b1220]";
