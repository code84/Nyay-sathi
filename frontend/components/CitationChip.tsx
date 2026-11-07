"use client";
export default function CitationChip({ id, onOpen }: { id: string; onOpen: (id: string) => void }) {
  return (
    <button type="button" onClick={() => onOpen(id)} aria-label={`Open source ${id}`}
      className="mx-0.5 inline-flex items-center rounded-md border border-[#14B8A6]/60 bg-[#14B8A6]/15 px-1.5 py-0.5 align-baseline text-xs font-semibold text-[#99F6E4] hover:bg-[#14B8A6]/30 focus:outline-none focus:ring-2 focus:ring-[#2DD4BF]">
      {id}
    </button>
  );
}
