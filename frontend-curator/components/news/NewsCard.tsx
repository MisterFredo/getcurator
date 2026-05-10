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
     COMPANY
  ========================================================= */

  const companyName =
    primaryCompany?.name ||
    item.primary_company_name ||
    "Unknown company";

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

    <div
      className="
        border-b
        border-gray-100
        py-5
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
                alt={companyName}
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
            onChange={() =>
              onToggleSelect(item)
            }
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
              TOP ROW
          =================================================== */}

          <div
            className="
              flex
              items-start
              justify-between
              gap-4
            "
          >

            <div className="min-w-0">

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
                {companyName}
              </div>

            </div>

            {/* =================================================
                EXPAND
            ================================================= */}

            <button
              onClick={() =>
                setOpen(!open)
              }
              className="
                w-8
                h-8
                rounded-lg
                border
                border-gray-200
                flex
                items-center
                justify-center
                bg-white
                hover:bg-gray-50
                transition
                shrink-0
              "
            >

              {open ? (
                <ChevronUp size={16} />
              ) : (
                <ChevronDown size={16} />
              )}

            </button>

          </div>

          {/* ===================================================
              EXCERPT PREVIEW
          =================================================== */}

          {item.excerpt && (

            <p
              className={`
                mt-3
                text-sm
                text-gray-600
                leading-relaxed
                transition-all

                ${
                  open
                    ? ""
                    : "line-clamp-2"
                }
              `}
            >
              {item.excerpt}
            </p>

          )}

          {/* ===================================================
              EXPANDED BODY
          =================================================== */}

          {open &&
            item.content_body && (

            <div
              className="
                mt-4
                pt-4
                border-t
                border-gray-100
              "
            >

              <div
                className="
                  text-sm
                  text-gray-700
                  leading-7
                  whitespace-pre-wrap
                "
              >
                {item.content_body}
              </div>

            </div>

          )}

        </div>

      </div>

    </div>
  );
}
