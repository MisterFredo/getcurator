"use client";

import { useRouter } from "next/navigation";

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

/* ========================================================= */

export default function NewsCard({
  item,
  selected = false,
  onToggleSelect,
  onClickBadge,
}: Props) {

  const router = useRouter();

  const {
    openRightDrawer,
  } = useDrawer();

  /* =========================================================
     BADGES
  ========================================================= */

  const badges =
    item.badges || [];

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
        ).toLocaleDateString(
          "fr-FR"
        )
      : null;

  /* =========================================================
     OPEN DRAWER
  ========================================================= */

  function handleOpen() {

    openRightDrawer(
      "analysis",
      item.id,
      "silent"
    );
  }

  /* =========================================================
     BADGE COLORS
  ========================================================= */

  function getBadgeClasses(
    badge: FeedBadge
  ) {

    switch (badge.type) {

      case "company":
        return `
          bg-blue-50
          text-blue-600
          hover:bg-blue-100
        `;

      case "solution":
        return `
          bg-violet-50
          text-violet-600
          hover:bg-violet-100
        `;

      default:
        return `
          bg-gray-100
          text-gray-600
          hover:bg-gray-200
        `;
    }
  }

  /* =========================================================
     RENDER
  ========================================================= */

  return (

    <div
      onClick={handleOpen}
      className={`
        group
        relative
        rounded-2xl
        border
        transition-all
        cursor-pointer
        overflow-hidden

        ${
          selected
            ? `
              border-[#99C221]
              bg-[#F7FAEF]
            `
            : `
              border-gray-200
              bg-white
              hover:border-gray-300
            `
        }
      `}
    >

      {/* =====================================================
          SELECT
      ===================================================== */}

      <div className="
        absolute
        top-4
        left-4
        z-10
      ">

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

      </div>

      {/* =====================================================
          MAIN
      ===================================================== */}

      <div className="
        flex
        items-stretch
      ">

        {/* ===================================================
            LOGO COLUMN
        =================================================== */}

        <div className="
          w-[88px]
          shrink-0
          bg-gray-50
          border-r
          border-gray-100
          flex
          items-center
          justify-center
          px-4
          py-6
        ">

          <div
            className="
              w-14
              h-14
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
          px-6
          py-5
        ">

          {/* =================================================
              DATE
          ================================================= */}

          {formattedDate && (

            <div className="
              text-[11px]
              text-gray-400
              mb-3
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
              gap-2
              mb-4
            ">

              {badges.map(
                (badge, idx) => (

                  <button
                    key={`${badge.label}-${idx}`}
                    onClick={(e) => {

                      e.stopPropagation();

                      onClickBadge?.(
                        badge
                      );
                    }}
                    className={`
                      px-2.5
                      py-[5px]
                      rounded-full
                      text-[10px]
                      font-medium
                      uppercase
                      tracking-wide
                      transition

                      ${getBadgeClasses(
                        badge
                      )}
                    `}
                  >
                    {badge.label}
                  </button>

                )
              )}

            </div>

          )}

          {/* =================================================
              TITLE
          ================================================= */}

          <h2
            className="
              text-[17px]
              font-semibold
              text-gray-900
              leading-snug
            "
          >
            {item.title}
          </h2>

          {/* =================================================
              EXCERPT
          ================================================= */}

          {item.excerpt && (

            <p
              className="
                mt-4
                text-sm
                text-gray-600
                leading-relaxed
              "
            >
              {item.excerpt}
            </p>

          )}

        </div>

      </div>

    </div>
  );
}
