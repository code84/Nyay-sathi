import type { Answer, ChatEvent, ChatRequest, LibraryItem } from "./types";

const verified = { status: "VERIFIED", last_verified: "2026-11-07" };
const ACT = "India Code, Consumer Protection Act 2019 (Act 35 of 2019)";
const ACT_URL = "https://www.indiacode.nic.in/bitstream/123456789/16939/1/a2019-35.pdf";

export const MOCK_SOURCES: Record<string, LibraryItem> = {
  "C-003": { id: "C-003", title: "Where and how to file: local limits, who can file, electronic filing (s.34(2), s.35(1))",
    source_name: ACT, source_url: ACT_URL, source_confidence: "primary", ...verified,
    excerpt: ['s.34(2)(c): "the cause of action, wholly or in part, arises"', 's.34(2)(d): "the complainant resides or personally works for gain"',
      's.35(1) proviso: "the complaint under this sub-section may be filed electronically in such manner as may be prescribed"'],
    meaning: "A complaint can be filed in the District Commission where the seller is based, where the problem arose, or where YOU live or work. The Act allows online filing.",
    limits: "The Act does not name the online portal; that comes from the Rules, not yet verified." },
  "C-004": { id: "C-004", title: "Which commission hears the case: the Act's limits and the 2021 Rules",
    source_name: ACT, source_url: ACT_URL, source_confidence: "act=primary, numbers=secondary", ...verified,
    excerpt: ['s.34(1) District Commission: "the District Commission shall have jurisdiction to entertain complaints where the value of the goods or services paid as consideration does not exceed one crore rupees"'],
    meaning: "The Act's default limits were District up to Rs 1 crore, but the Central Government prescribed other values in 2021. Current working limit: District up to Rs 50 lakh.",
    limits: "The 2021 numbers have not been checked against the Gazette. The limit depends on the price paid, not the compensation claimed." },
  "C-005": { id: "C-005", title: "Time limit to file: two years (s.69)",
    source_name: ACT, source_url: ACT_URL, source_confidence: "primary", ...verified,
    excerpt: ['s.69(1): "shall not admit a complaint unless it is filed within two years from the date on which the cause of action has arisen"',
      's.69(2) proviso: "records its reasons for condoning such delay"'],
    meaning: "Generally you have two years from when the cause of action arose. A late complaint can still be heard if you show a good reason, but the Commission decides.",
    limits: "What date the cause of action arose can be argued. Do not treat it as a guaranteed deadline." },
};

const REFUND: Answer = {
  text: "You can file a consumer complaint with the District Consumer Disputes Redressal Commission because the amount of Rs 20,000 is well below the district limit of Rs 50 lakh [C-004]. The complaint may be filed in the district where the seller is located, where the problem arose, or where you reside or work, and you may also file it electronically [C-003]. The complaint must be filed within two years from the date the refund was refused, although the commission may condone a later filing if you show sufficient cause [C-005].",
  citations: [{ item_id: "C-004" }, { item_id: "C-003" }, { item_id: "C-005" }],
  flags: [{ code: "forum", severity: "info", message: "Amount fits the District Commission." }],
  confidence: "library",
};
const URGENT: Answer = {
  text: "I cannot safely advise on threats or a possible crime. Please contact a lawyer or your State Legal Services Authority for free legal aid, and call the police helpline if you are in danger.",
  citations: [], confidence: "unsure",
  flags: [{ code: "needs_lawyer", severity: "urgent", message: "Threats or a possible criminal angle: speak to a lawyer or legal-aid service now." }],
};
const UNSURE: Answer = {
  text: "I do not have verified information on this. Please speak to a lawyer or a free legal-aid service.",
  citations: [], flags: [{ code: "fallback", severity: "warn", message: "No verified source covers this question." }], confidence: "unsure",
};

const sleep = (ms: number) => new Promise((r) => setTimeout(r, ms));

export async function* mockChat(req: ChatRequest): AsyncGenerator<ChatEvent> {
  const m = req.message.toLowerCase();
  const answer = /threat|police|धमकी|मारने/.test(m) ? URGENT : /refund|seller|रिफंड|विक्रेता/.test(m) ? REFUND : UNSURE;
  await sleep(500);
  for (const w of answer.text.split(" ")) { yield { type: "token", text: w + " " }; await sleep(25); }
  await sleep(300);
  yield { type: "final", answer, case_state: req.case_state };
}

export async function mockSource(id: string): Promise<LibraryItem> {
  await sleep(300);
  const s = MOCK_SOURCES[id];
  if (!s) throw new Error(`Source ${id} not found`);
  return s;
}
