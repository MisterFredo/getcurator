"use client";

import type { FeedBadge } from "@/types/feed";

/* ========================================================= */

const GCS_BASE_URL =
  process.env
    .NEXT_PUBLIC_GCS_BASE_URL || "";

/* ========================================================= */

type FeedItem = {
  id: string;

  type: "news" | "analysis";
  id_primary_company?: string | null;

  title: string;

  excerpt?: string | null;

  published_at?: string;

  topics?: any[];

  companies?: any[];

  solutions?: any[];

  universes?: any[];

  news_type?: string | null;
};

type Props = {
  item: FeedItem;

  onClick: () => void;

  // 🔥 NEW
  isFavorite?: boolean;
  onToggleFavorite?: (id: string, isFav: boolean) => void;
};

/* =========================================================
   BADGES
========================================================= */

function getBadgeClass(type?: string) {

  switch (type) {

    case "news_type":
      return `
        bg-black
        text-white
      `;

    case "company":
      return `
        bg-blue-50
        text-blue-600
        border
        border-blue-100
      `;

    case "solution":
      return `
        bg-purple-50
        text-purple-600
        border
        border-purple-100
      `;

    case "universe":
      return `
        bg-emerald-50
        text-emerald-600
        border
        border-emerald-100
      `;

    case "topic":
    default:
      return `
        bg-gray-100
        text-gray-600
      `;
  }
}

/* ========================================================= */

function buildBadges(
  item: FeedItem
): FeedBadge[] {

  const topics = Array.isArray(item.topics)
    ? item.topics
    : [];

  const companies = Array.isArray(item.companies)
    ? item.companies
    : [];

  const solutions = Array.isArray(item.solutions)
    ? item.solutions
    : [];

  const universes = Array.isArray(item.universes)
    ? item.universes
    : [];

  return [

    ...(item.news_type
      ? [{
          label: item.news_type,
          type: "news_type" as const,
        }]
      : []),

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
}

/* =========================================================
   COMPONENT
========================================================= */

export default function FeedItemCard({
  item,
  onClick,
  isFavorite = false,
  onToggleFavorite,
}: Props) {

  const badges =
    buildBadges(item);

  const formattedDate =
    item.published_at
      ? new Date(
          item.published_at
        ).toLocaleDateString("fr-FR")
      : null;

  const isNews =
    item.type === "news";

  /* =========================================================
     FAVORITE HANDLER
  ========================================================= */

  function handleFavoriteClick(e: React.MouseEvent) {
    e.stopPropagation();

    if (!onToggleFavorite) return;

    onToggleFavorite(item.id, isFavorite);
  }

  /* =========================================================
     LOGO
  ========================================================= */

  const primaryCompany =
    item.id_primary_company

      ? item.companies?.find(
          (c: any) =>
            c.id_company === item.id_primary_company
        )

      : null;

  const logoUrl =
    primaryCompany?.media_logo_rectangle_id

      ? `${GCS_BASE_URL}/companies/${primaryCompany.media_logo_rectangle_id}`

      : null;

  /* =========================================================
     RENDER
  ========================================================= */

  return (

    <div
      onClick={onClick}
      className="
        relative
        cursor-pointer
        py-4
        transition
        hover:bg-gray-50
      "
    >

      {/* ⭐ FAVORITE */}
      <button
        onClick={handleFavoriteClick}
        className="
          absolute
          top-2
          right-2
          text-sm
          z-10
        "
      >
        {isFavorite ? "⭐" : "☆"}
      </button>

      <div className="
        flex
        items-start
        gap-5
      ">

        {/* ===================================================
            LEFT COLUMN
        =================================================== */}

        <div className="
          w-[72px]
          shrink-0
          flex
          flex-col
          items-center
          gap-2
          pt-0.5
        ">

          {/* DATE */}

          {formattedDate && (

            <div className="
              text-[11px]
              text-gray-400
              text-center
              leading-none
            ">
              {formattedDate}
            </div>

          )}

          {/* LOGO */}

            {logoUrl && (

              <div
                className="
                  w-12
                  h-12
                  rounded-xl
                  border
                  border-gray-200
                  bg-white
                  overflow-hidden
                  flex
                  items-center
                  justify-center
                "
              >

                <img
                  src={logoUrl}
                  alt={item.title}
                  className="
                    w-full
                    h-full
                    object-contain
                  "
                />

              </div>

            )}

        </div>

        {/* ===================================================
            CONTENT
        =================================================== */}

        <div className="
          flex-1
          min-w-0
        ">

          {/* =================================================
              TYPE
          ================================================= */}

          <div className="
            mb-2
          ">

            <span
              className={`
                inline-flex
                items-center
                text-[10px]
                uppercase
                tracking-wide
                px-2
                py-[3px]
                rounded-full
                font-medium

                ${
                  isNews
                    ? `
                      bg-blue-50
                      text-blue-700
                    `
                    : `
                      bg-gray-100
                      text-gray-700
                    `
                }
              `}
            >
              {isNews
                ? "News"
                : "Analysis"}
            </span>

          </div>

          {/* =================================================
              TITLE
          ================================================= */}

          <h3
            className="
              text-[14px]
              font-medium
              text-gray-900
              leading-snug
            "
          >
            {item.title}
          </h3>

          {/* =================================================
              EXCERPT
          ================================================= */}

          {item.excerpt && (

            <p className="
              mt-2
              text-sm
              text-gray-600
              leading-relaxed
            ">
              {item.excerpt}
            </p>

          )}

          {/* =================================================
              BADGES
          ================================================= */}

          {badges.length > 0 && (

            <div className="
              flex
              flex-wrap
              gap-1.5
              mt-3
            ">

              {badges.map((b, i) => {

                const keyValue =
                  "id" in b && b.id
                    ? b.id
                    : b.label;

                return (

                  <span
                    key={`${b.type}-${keyValue}-${i}`}
                    className={`
                      px-2
                      py-[3px]
                      text-[10px]
                      rounded-full
                      uppercase
                      tracking-wide
                      ${getBadgeClass(b.type)}
                    `}
                  >
                    {b.label}
                  </span>

                );
              })}

            </div>

          )}

        </div>

      </div>

    </div>
  );
}
