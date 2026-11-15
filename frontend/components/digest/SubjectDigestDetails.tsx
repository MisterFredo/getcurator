"use client";

export type Badge = string | { type: string; label: string };

const colors: Record<string, { backgroundColor: string; color: string }> = {
  company: { backgroundColor: "#dbeafe", color: "#1e40af" },
  topic: { backgroundColor: "#dcfce7", color: "#166534" },
  solution: { backgroundColor: "#ede9fe", color: "#5b21b6" },
  keyword: { backgroundColor: "#f1f5f9", color: "#334155" },
};

export function Badge({ badge }: { badge: Badge }) {
  const { type, label } = typeof badge === "string" ? { type: "keyword", label: badge } : badge;
  return <span className="rounded-full px-2.5 py-1 text-xs" style={colors[type] ?? colors.keyword}>{label}</span>;
}

export function sourceLink(value?: string | null): string | undefined {
  if (!value) return;
  try {
    const url = new URL(value);
    if (url.protocol === "https:" || url.protocol === "http:") return url.href;
  } catch {
    return;
  }
}
