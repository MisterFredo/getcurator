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
     TOPIC BADGES ONLY
  ========================================================= */

  const topicBadges =
    (item.badges || []).filter(
      (b) => b.type === "topic"
    );

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
     RENDER
  ========================================================= */

  return (

    <div
      onClick={handleOpen}
      className="
        border-b
        border-gray-100
        py-5
        cursor-pointer
        hover:bg-gray-50
        transition
      "
    >

      <div
        className="
          flex
          items-start
          gap-4
        "
      >

        {/* =====================================================
            LEFT COLUMN
        ===================================================== */}

        <div
          className="
            flex
            flex-col
            items-center
            gap-2
            shrink-0
          "
        >

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

        </div>

        {/* =====================================================
            CONTENT
        ===================================================== */}

        <div className="
          flex-1
          min-w-0
        ">

          {/* ===================================================
              META
          =================================================== */}

          <div
            className="
              flex
              flex-wrap
              items-center
              gap-2
              mb-2
            "
          >

            {/* DATE */}

            {formattedDate && (

              <span
                className="
                  text-[11px]
                  text-gray-400
                  shrink-0
                "
              >
                {formattedDate}
              </span>

            )}

            {/* TOPICS */}

            {topicBadges.map(
              (badge, idx) => (

                <button
                  key={`${badge.label}-${idx}`}
                  onClick={(e) => {

                    e.stopPropagation();

                    onClickBadge?.(
                      badge
                    );
                  }}
                  className="
                    px-2
                    py-[3px]
                    rounded-full
                    text-[10px]
                    uppercase
                    tracking-wide
                    bg-gray-100
                    text-gray-600
                    hover:bg-gray-200
                    transition
                  "
                >
                  {badge.label}
                </button>

              )
            )}

          </div>

          {/* ===================================================
              TITLE
          =================================================== */}

          <h2
            className="
              text-[15px]
              font-semibold
              text-gray-900
              leading-snug
            "
          >
            {item.title}
          </h2>

          {/* ===================================================
              EXCERPT
          =================================================== */}

          {item.excerpt && (

            <p
              className="
                mt-3
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
