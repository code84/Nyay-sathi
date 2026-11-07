export default function DisclaimerBanner({ text, mock, isDark = true }: { text: string; mock?: string; isDark?: boolean }) {
  return (
    <div className={`border-b px-4 py-2 text-center text-xs ${isDark ? "border-[#14B8A6]/25 bg-[#0a1c1b] text-[#99F6E4]" : "border-teal-200 bg-teal-50 text-teal-700"}`}>
      {text}
      {mock && <div className="mt-0.5 font-semibold">{mock}</div>}
    </div>
  );
}
