"use client";

import type { FeedBadge } from "@/types/feed";

/* ========================================================= */

type Props = {
  topics?: any[];
  companies?: any[];
  solutions?: any[];
  className?: string;
};

/* ========================================================= */

export default function ContentBadges({
  topics,
  companies,
  solutions,
  className = "",
}: Props) {

  /* =========================================================
     SAFE ARRAYS (IDENTIQUE FEEDROW)
  ========================================================= */

  const safeTopics = Array.isArray(topics) ? topics : [];
  const safeCompanies = Array.isArray(companies) ? companies : [];
  const safeSolutions = Array.isArray(solutions) ? solutions : [];

  /* =========================================================
     BADGES (STRICTEMENT IDENTIQUE FEEDROW)
  ========================================================= */

  const badges: FeedBadge[] = [
    ...safeCompanies.map((c: any) => ({
      id: c.id_company,
      label: c.name,
      type: "company" as const,
    })),

    ...safeTopics.map((t: any) => ({
      id: t.id_topic,
      label: t.label,
      type: "topic" as const,
    })),

    ...safeSolutions.map((s: any) => ({
      id: s.id_solution,
      label: s.name,
      type: "solution" as const,
    })),
  ];

  if (badges.length === 0) return null;

  /* =========================================================
     STYLE (IDENTIQUE FEEDROW)
  ========================================================= */

  function getBadgeClass(type?: string) {
    switch (type) {
      case "company":
        return "bg-blue-50 text-blue-600 border border-blue-100";
      case "solution":
        return "bg-purple-50 text-purple-600 border border-purple-100";
      case "topic":
      default:
        return "bg-gray-100 text-gray-600";
    }
  }

  /* =========================================================
     RENDER (NON CLIQUABLE)
  ========================================================= */

  return (
    <div className={`flex flex-wrap gap-2 ${className}`}>
      {badges.map((b, i) => (
        <span
          key={`${b.type}-${b.id || b.label}-${i}`}
          className={`
            px-2 py-0.5 text-[10px] rounded-full uppercase tracking-wide
            ${getBadgeClass(b.type)}
          `}
        >
          {b.label}
        </span>
      ))}
    </div>
  );
}
