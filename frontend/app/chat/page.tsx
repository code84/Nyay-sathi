"use client";
import Link from "next/link";
import ChatStream from "@/components/ChatStream";
import DisclaimerBanner from "@/components/DisclaimerBanner";
import Fonts from "@/components/Fonts";
import LangToggle from "@/components/LangToggle";
import { isMock } from "@/lib/api";
import { homeCopy } from "@/lib/homeCopy";
import { strings } from "@/lib/i18n";
import { sans, serif } from "@/lib/theme";
import { useLang } from "@/lib/useLang";

export default function ChatPage() {
  const [lang, setLang] = useLang();
  const t = strings(lang);
  const c = homeCopy(lang);
  return (
    <div className="bg-[#0b1220] text-neutral-100" style={sans}>
      <Fonts />
      <div className="mx-auto flex h-dvh max-w-3xl flex-col">
        <header className="flex items-center justify-between gap-3 px-4 py-3">
          <Link href="/" className="text-sm text-neutral-400 hover:text-white">← {t.back}</Link>
          <h1 className="text-lg font-bold text-[#5EEAD4]" style={serif}>{t.appName}</h1>
          <LangToggle lang={lang} onChange={setLang} label={t.language} />
        </header>
        <DisclaimerBanner text={t.disclaimer} mock={isMock ? t.mock : undefined} />
        <ChatStream key={lang} lang={lang} t={t} greeting={c.greeting} suggestions={c.chips} note={c.note} />
      </div>
    </div>
  );
}
