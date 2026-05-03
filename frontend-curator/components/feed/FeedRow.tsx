"use client";

import type { FeedItem, FeedBadge } from "@/types/feed";

/* ========================================================= */

type Props = {
  item: FeedItem;
  onClick: () => void;
  onClickBadge?: (badge: FeedBadge) => void;
  loading?: boolean;
};

/* ========================================================= */

export default function FeedRow({
  item,
  onClick,
  onClickBadge,
  loading = false,
}: Props) {
  /* =========================================================
     DATE
  ========================================================= */

  let formattedDate: string | null = null;

  try {
    formattedDate = item.published_at
      ? new Date(item.published_at).toLocaleDateString("fr-FR")
      : null;
  } catch {
    formattedDate = null;
  }

  /* =========================================================
     SAFE ARRAYS
  ========================================================= */

  const topics = Array.isArray(item.topics) ? item.topics : [];
  const companies = Array.isArray(item.companies) ? item.companies : [];
  const solutions = Array.isArray(item.solutions) ? item.solutions : [];
  const universes = Array.isArray((item as any).universes)
    ? (item as any).universes
    : [];

  /* =========================================================
     BADGES (UNIFIÉ)
  ========================================================= */

  const badges: FeedBadge[] = [
    ...universes.map((u: any) => ({
      id: u.id_universe,
      label: u.label,
      type: "universe" as const,
    })),
    ...companies.map((c: any) => ({
      id: c.id_company,
      label: c.name,
      type: "company" as const,
    })),
    ...topics.map((t: any) => ({
      id: t.id_topic,
      label: t.label,
      type: "topic" as const,
    })),
    ...solutions.map((s: any) => ({
      id: s.id_solution,
      label: s.name,
      type: "solution" as const,
    })),
  ];

  /* =========================================================
     DEDUP BADGES
  ========================================================= */

  const uniqueBadges: FeedBadge[] = Array.from(
    new Map(
      badges.map((b) => [`${b.type}-${b.id || b.label}`, b])
    ).values()
  );

  /* =========================================================
     BADGE STYLE
  ========================================================= */

  function getBadgeClass(type?: string) {
    switch (type) {
      case "universe":
        return "bg-black text-white";

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
     RENDER
  ========================================================= */

  return (
    <article
      onClick={!loading ? onClick : undefined}
      className={`
        cursor-pointer
        px-4 py-4
        transition
        ${
          loading
            ? "opacity-50 pointer-events-none"
            : "hover:bg-gray-50"
        }
      `}
    >
      <div className="flex gap-4 items-start">
        <div className="flex-1 space-y-2">

          {/* META */}
          <div className="flex items-center justify-between text-[11px] text-gray-400">
            <div className="flex items-center gap-2">
              <span>{formattedDate || ""}</span>

              {loading && (
                <span className="animate-pulse text-gray-400">
                  • Loading…
                </span>
              )}
            </div>
          </div>

          {/* BADGES */}
          {uniqueBadges.length > 0 && (
            <div className="flex flex-wrap gap-2">
              {uniqueBadges.map((b, i) => (
                <button
                  key={`${b.type}-${b.id || b.label}-${i}`}
                  onClick={(e) => {
                    e.stopPropagation();
                    if (!loading) onClickBadge?.(b);
                  }}
                  className={`
                    px-2 py-0.5 text-[10px] rounded-full uppercase tracking-wide
                    ${getBadgeClass(b.type)}
                    hover:opacity-80 transition
                  `}
                >
                  {b.label}
                </button>
              ))}
            </div>
          )}

          {/* TITLE */}
          <h2 className="text-[15px] font-medium leading-snug text-gray-900">
            {item.title}
          </h2>

          {/* EXCERPT */}
          {item.excerpt && (
            <p className="text-sm text-gray-600 line-clamp-2">
              {item.excerpt}
            </p>
          )}
        </div>
      </div>
    </article>
  );
}
