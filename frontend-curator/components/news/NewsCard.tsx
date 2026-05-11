"use client";

import type {
  FeedItem,
  FeedBadge,
} from "@/types/feed";

import { useDrawer } from "@/contexts/DrawerContext";

/* ========================================================= */

const GCS_BASE_URL =
  process.env
    .NEXT_PUBLIC_GCS_BASE_URL || "";

/* ========================================================= */

type Props = {
  item: FeedItem;

  selected?: boolean;

  onToggleSelect: (
    item: FeedItem
  ) => void;

  onClickBadge?: (
    badge: FeedBadge
  ) => void;
};

/* =========================================================
   BADGES
========================================================= */

function getBadgeClass(type?: string) {

  switch (type) {

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

  return [

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

export default function NewsCard({
  item,
  selected = false,
  onToggleSelect,
  onClickBadge,
}: Props) {

  const {
    openRightDrawer,
  } = useDrawer();

  const badges =
    buildBadges(item);

  /* =========================================================
     LOGO
  ========================================================= */

  const primaryCompany =
    item.companies?.[0];

  const logoUrl =
    primaryCompany
      ?.media_logo_rectangle_id

      ? `${GCS_BASE_URL}/companies/${primaryCompany.media_logo_rectangle_id}`

      : null;

  /* =========================================================
     DATE
  ========================================================= */

  const formattedDate =
    item.published_at
      ? new Date(
          item.published_at
        ).toLocaleDateString("fr-FR")
      : null;

  /* =========================================================
     OPEN
  ========================================================= */

  function handleOpen() {

    openRightDrawer(
      "news",
      item.id,
      "silent"
    );
  }

  /* =========================================================
     RENDER
  ========================================================= */

  return (

    <div
      onClick={handleOpen}
      className="
        cursor-pointer
        py-4
        border-b
        border-gray-100
        hover:bg-gray-50
        transition
      "
    >

      <div className="
        flex
        items-start
        gap-4
      ">

        {/* ===================================================
            LEFT
        =================================================== */}

        <div className="
          flex
          flex-col
          items-center
          gap-3
          shrink-0
          pt-1
        ">

          {/* SELECT */}

          <input
            type="checkbox"
            checked={selected}
            onChange={(e) => {

              e.stopPropagation();

              onToggleSelect(item);
            }}
            className="
              w-4
              h-4
              cursor-pointer
            "
          />

          {/* LOGO */}

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

            {logoUrl ? (

              <img
                src={logoUrl}
                alt={item.title}
                className="
                  w-full
                  h-full
                  object-contain
                "
              />

            ) : (

              <div
                className="
                  text-[10px]
                  text-gray-300
                "
              >
                —
              </div>

            )}

          </div>

        </div>

        {/* ===================================================
            CONTENT
        =================================================== */}

        <div className="
          flex-1
          min-w-0
        ">

          {/* =================================================
              DATE
          ================================================= */}

          {formattedDate && (

            <div className="
              text-[11px]
              text-gray-400
              mb-2
            ">
              {formattedDate}
            </div>

          )}

          {/* =================================================
              BADGES
          ================================================= */}

          {badges.length > 0 && (

            <div className="
              flex
              flex-wrap
              gap-1.5
              mb-2
            ">

              {badges.map((b, i) => {

                const keyValue =
                  "id" in b && b.id
                    ? b.id
                    : b.label;

                return (

                  <button
                    key={`${b.type}-${keyValue}-${i}`}
                    onClick={(e) => {

                      e.stopPropagation();

                      onClickBadge?.(b);
                    }}
                    className={`
                      px-2
                      py-[3px]
                      text-[10px]
                      rounded-full
                      uppercase
                      tracking-wide
                      transition
                      ${getBadgeClass(b.type)}
                    `}
                  >
                    {b.label}
                  </button>

                );
              })}

            </div>

          )}

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

        </div>

      </div>

    </div>
  );
}
