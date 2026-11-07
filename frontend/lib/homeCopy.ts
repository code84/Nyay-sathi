import type { Lang } from "./types";

type Status = "live" | "soon" | "support";
type Law = { t: string; act: string; d: string; n: number; s: Status };

const en = {
  tagline: "Legal help, with sources",
  navFeatures: "Features", navHow: "How it works", navFaq: "FAQs", navCta: "Try it",
  badge: "Verified sources · No guesswork",
  h1a: "Nyay Saathi:", h1b: "Verified legal help for your problems",
  sub1: "Refund not paid? Cheque bounce notice? Loan-recovery notice?",
  sub2: "Ask in plain Hindi or English. Get clear answers with the source linked.",
  pills: ["Ask in your words", "Hindi & English", "Every point sourced", "Says when to see a lawyer"],
  greeting: "Hello, how can I help you today?",
  chips: [
    "My seller refused a Rs 20,000 refund. Where do I complain?",
    "My cheque bounced and I got a legal notice. What should I do?",
    "I received a loan recovery notice from a bank. How do I respond?",
  ],
  note: "General information, not legal advice.",
  featuresTitle: "Laws we cover",
  featuresSub: "No matter your situation, we've got you covered. Pick a topic, ask your question, and get clear answers you can actually act on.",
  laws: [
    { t: "Online refunds", act: "Consumer Protection Act, 2019", d: "Where to complain, which commission hears it, the time limit, the filing fee and e-commerce refund rules.", n: 10, s: "live" },
    { t: "Cheque bounce", act: "Negotiable Instruments Act, 1881", d: "The section 138 offence, the 30-day notice and 15-day payment window, and where to file.", n: 8, s: "live" },
    { t: "Loan-recovery notice", act: "SARFAESI Act, 2002", d: "The 60-day notice, what it must say, how to object and how to challenge the lender.", n: 6, s: "live" },
    { t: "Time limits", act: "Limitation Act, 1963", d: "When a claim is too late, when a delay can be excused and what restarts the clock.", n: 5, s: "support" },
  ] as Law[],
  status: { live: "Available now", soon: "Coming next", support: "Used for deadlines" },
  sourcesWord: "library sources",
  howTitle: "How it works", howSub: "No jargon. No guessing.",
  steps: [
    ["Tell your story", "Write what happened in your own words, in Hindi or English."],
    ["We check the library", "Answers use only a small library of official legal texts. Nothing from outside guessing."],
    ["See sources and next steps", "Every legal point has a source chip you can open. If it is not sure, it says so and points you to a lawyer."],
  ],
  wontTitle: "⚖️ Important Boundaries to Know",
  wont: [
    "Guarantee outcomes or predict your chances of winning",
    "Fabricate legal sections, statutes, or court precedents",
    "Substitute professional legal counsel for complex or high-stakes matters",
  ],
  faqTitle: "Frequently asked questions",
  faqs: [
    ["Is this legal advice?", "No. It gives general information from a small library of official texts. For large amounts, threats or court deadlines, please talk to a lawyer or a free legal-aid service."],
    ["How do I know an answer is real?", "Click any gold source chip. It opens the exact quoted text and a link to the official source. Answers that cannot be matched to the library are blocked."],
    ["What if it does not know?", "It says so plainly and suggests a lawyer or free legal aid, instead of guessing."],
    ["Is the library complete?", "No, it is small on purpose. Some figures are still being checked against official gazettes. Those sources show an amber badge."],
    ["Which languages work?", "English and Hindi."],
  ],
  ctaTitle: "Have a refund problem?", ctaBtn: "Ask now",
  foot: "Prototype built for a take-home assignment. Not legal advice.",
};

const hi: typeof en = {
  tagline: "स्रोतों के साथ कानूनी मदद",
  navFeatures: "सुविधाएँ", navHow: "कैसे काम करता है", navFaq: "सवाल", navCta: "आज़माइए",
  badge: "सत्यापित स्रोत · कोई अंदाज़ा नहीं",
  h1a: "न्याय साथी:", h1b: "पैसों की समस्याओं पर सत्यापित कानूनी मदद",
  sub1: "रिफंड नहीं मिला? चेक बाउंस नोटिस? लोन वसूली नोटिस?",
  sub2: "सरल हिंदी या अंग्रेज़ी में पूछिए। साफ़ जवाब पाइए, स्रोत के लिंक के साथ।",
  pills: ["अपने शब्दों में पूछिए", "हिंदी और अंग्रेज़ी", "हर बात का स्रोत", "वकील से मिलने की सलाह भी देता है"],
  greeting: "नमस्ते, आज मैं आपकी क्या मदद कर सकता हूँ?",
  chips: [
    "विक्रेता ने ₹20,000 का रिफंड देने से मना कर दिया। शिकायत कहाँ करूँ?",
    "मेरा चेक बाउंस हो गया और मुझे कानूनी नोटिस मिला। मुझे क्या करना चाहिए?",
    "बैंक से लोन वसूली का नोटिस मिला है। मैं इसका जवाब कैसे दूँ?",
  ],
  note: "सामान्य जानकारी, कानूनी सलाह नहीं।",
  featuresTitle: "हम कौन-से कानून कवर करते हैं",
  featuresSub: "चाहे आपकी समस्या कुछ भी हो, हम आपके साथ हैं। कोई भी विषय चुनिए, सवाल पूछिए और ऐसे स्पष्ट जवाब पाइए जिन पर आप तुरंत अमल कर सकें।",
  laws: [
    { t: "ऑनलाइन रिफंड", act: "उपभोक्ता संरक्षण अधिनियम, 2019", d: "शिकायत कहाँ करें, कौन-सा आयोग सुनेगा, समय-सीमा, फ़ाइलिंग शुल्क और ई-कॉमर्स रिफंड नियम।", n: 10, s: "live" },
    { t: "चेक बाउंस", act: "परक्राम्य लिखत अधिनियम, 1881", d: "धारा 138 का अपराध, 30 दिन का नोटिस और 15 दिन की भुगतान अवधि, और कहाँ दर्ज करें।", n: 8, s: "live" },
    { t: "लोन वसूली नोटिस", act: "सरफेसी अधिनियम, 2002", d: "60 दिन का नोटिस, उसमें क्या होना चाहिए, आपत्ति कैसे करें और ऋणदाता को चुनौती कैसे दें।", n: 6, s: "live" },
    { t: "समय-सीमा", act: "परिसीमा अधिनियम, 1963", d: "दावा कब देर से माना जाता है, देरी कब माफ़ हो सकती है और समय-सीमा कब दोबारा शुरू होती है।", n: 5, s: "support" },
  ],
  status: { live: "अभी उपलब्ध", soon: "जल्द आ रहा है", support: "समय-सीमा के लिए उपयोग" },
  sourcesWord: "लाइब्रेरी स्रोत",
  howTitle: "कैसे काम करता है", howSub: "कोई कठिन शब्द नहीं। कोई अंदाज़ा नहीं।",
  steps: [
    ["अपनी बात बताइए", "जो हुआ, अपने शब्दों में हिंदी या अंग्रेज़ी में लिखिए।"],
    ["हम लाइब्रेरी में जाँचते हैं", "जवाब सिर्फ़ आधिकारिक कानूनी पाठों की छोटी लाइब्रेरी से बनते हैं। बाहर का कोई अंदाज़ा नहीं।"],
    ["स्रोत और अगले कदम देखिए", "हर कानूनी बात के साथ एक स्रोत चिप है जिसे आप खोल सकते हैं। पक्का न हो तो यह साफ़ कहता है और वकील का सुझाव देता है।"],
  ],
  wontTitle: "⚖️ ज़रूरी सीमाएँ जो आपको जाननी चाहिए",
  wont: [
    "परिणाम की गारंटी देना या जीतने की संभावना बताना",
    "कानूनी धाराएँ, क़ानून या अदालती मिसाल गढ़ना",
    "जटिल या जोखिम भरे मामलों में पेशेवर वकील की जगह लेना",
  ],
  faqTitle: "अक्सर पूछे जाने वाले सवाल",
  faqs: [
    ["क्या यह कानूनी सलाह है?", "नहीं। यह आधिकारिक पाठों की छोटी लाइब्रेरी से सामान्य जानकारी देता है। बड़ी रकम, धमकी या अदालती समय-सीमा हो तो वकील या मुफ़्त कानूनी सहायता से मिलें।"],
    ["कैसे पता चले कि जवाब सही है?", "किसी भी सुनहरे स्रोत चिप पर क्लिक कीजिए। वह सटीक उद्धृत पाठ और आधिकारिक स्रोत का लिंक खोलता है। जो जवाब लाइब्रेरी से मेल नहीं खाते, वे रोक दिए जाते हैं।"],
    ["अगर इसे पता न हो तो?", "यह साफ़ कहता है और अंदाज़ा लगाने की बजाय वकील या मुफ़्त कानूनी सहायता का सुझाव देता है।"],
    ["क्या लाइब्रेरी पूरी है?", "नहीं, यह जानबूझकर छोटी है। कुछ आँकड़े अभी सरकारी राजपत्र से जाँचे जा रहे हैं। ऐसे स्रोतों पर पीला बैज दिखता है।"],
    ["कौन-सी भाषाएँ चलती हैं?", "अंग्रेज़ी और हिंदी।"],
  ],
  ctaTitle: "रिफंड की समस्या है?", ctaBtn: "अभी पूछिए",
  foot: "यह एक असाइनमेंट के लिए बनाया गया प्रोटोटाइप है। कानूनी सलाह नहीं।",
};

export const homeCopy = (lang: Lang) => (lang === "hi" ? hi : en);
