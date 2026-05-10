"use client";

import { useState } from "react";

import {
  ChevronDown,
  ChevronUp,
} from "lucide-react";

import type {
  FeedItem,
  FeedBadge,
} from "@/types/feed";

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

  const [open, setOpen] =
    useState(false);

  /* =========================================================
     TOPIC BADGES ONLY
  ========================================================= */

  const topicBadges =
    (item.badges || []).filter(
      (b) => b.type === "topic"
    );

  /* =========================================================
     PRIMARY COMPANY
  ========================================================= */

  const primaryCompany =
    item.companies?.find(
      (c: any) =>
        c.id_company ===
        item.id_primary_company
    ) || item.companies?.[0];

  /* =========================================================
     LOGO
  ========================================================= */

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
     RENDER
  ========================================================= */

  return (

    <article
      className="
        border-b
        border-gray-100
        px-4
        py-4
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

        {/* LEFT */}

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
              rounded-lg
              border
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
                alt={
                  primaryCompany?.name ||
                  ""
                }
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
                  text-gray-400
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
            onChange={() =>
              onToggleSelect(item)
            }
            className="
              w-3.5
              h-3.5
            "
          />

        </div>

        {/* RIGHT */}

        <div className="flex-1 min-w-0">

          {/* META */}

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

              <div
                className="
                  text-[11px]
                  text-gray-400
                  shrink-0
                "
              >
                {formattedDate}
              </div>

            )}

            {/* TOPICS */}

            {topicBadges.map(
              (badge, idx) => (

                <button
                  key={`${badge.label}-${idx}`}
                  onClick={() =>
                    onClickBadge?.(
                      badge
                    )
                  }
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

          {/* HEADER */}

          <div
            className="
              flex
              items-start
              justify-between
              gap-4
            "
          >

            <div className="min-w-0">

              {/* TITLE */}

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

              {/* COMPANY */}

              <div
                className="
                  text-sm
                  text-gray-500
                  mt-1
                "
              >
                {primaryCompany?.name ||
                  "Unknown company"}
              </div>

            </div>

            {/* EXPAND */}

            <button
              onClick={() =>
                setOpen(!open)
              }
              className="
                w-7
                h-7
                rounded-md
                border
                flex
                items-center
                justify-center
                bg-white
                shrink-0
                hover:bg-gray-50
              "
            >

              {open ? (
                <ChevronUp size={14} />
              ) : (
                <ChevronDown size={14} />
              )}

            </button>

          </div>

          {/* EXPANDED */}

          {open && (

            <div
              className="
                mt-4
                pt-4
                border-t
                space-y-4
              "
            >

              {/* EXCERPT */}

              {item.excerpt && (

                <div
                  className="
                    text-sm
                    text-gray-700
                    leading-6
                  "
                >
                  {item.excerpt}
                </div>

              )}

              {/* CONTENT */}

              {item.content_body && (

                <div
                  className="
                    text-sm
                    text-gray-600
                    leading-7
                    whitespace-pre-wrap
                  "
                >
                  {item.content_body}
                </div>

              )}

            </div>

          )}

        </div>

      </div>

    </article>
  );
}
