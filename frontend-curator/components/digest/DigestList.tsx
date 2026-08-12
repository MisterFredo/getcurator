"use client";

import {
  ChevronRight,
} from "lucide-react";

import type {
  DigestHistoryItem,
} from "@/types/digest";

/* =========================================================
   TYPES
========================================================= */

type Props = {
  digest: DigestHistoryItem;

  onClick: (
    digest: DigestHistoryItem,
  ) => void;
};

/* =========================================================
   DATE
========================================================= */

function formatDate(
  value?: string | null,
) {

  if (!value) {
    return "";
  }

  return new Intl.DateTimeFormat(
    "en",
    {
      day: "numeric",
      month: "short",
      year: "numeric",
    },
  ).format(
    new Date(value),
  );

}

/* =========================================================
   COMPONENT
========================================================= */

export default function DigestList({
  digest,
  onClick,
}: Props) {

  const displayName =
    digest.DISPLAY_NAME ??
    digest.NAME ??
    "GetCurator";

  const periodStart =
    formatDate(
      digest.PERIOD_START,
    );

  const periodEnd =
    formatDate(
      digest.PERIOD_END,
    );

  const frequency =
    digest.FREQUENCY
      ? `${digest.FREQUENCY
          .charAt(0)
          .toUpperCase()}${digest.FREQUENCY
          .slice(1)
          .toLowerCase()} Digest`
      : "Digest";

  /* =========================================================
     RENDER
  ========================================================= */

  return (

    <button

      type="button"

      onClick={() =>
        onClick(
          digest,
        )
      }

      className="
        group
        w-full
        rounded-xl
        border
        border-ratecard-border
        bg-white
        px-5
        py-4
        text-left
        transition
        hover:bg-gray-50
      "

    >

      <div
        className="
          flex
          items-center
          gap-5
        "
      >

        {/* =================================================
            LEFT
        ================================================= */}

        <div
          className="
            min-w-0
            flex-1
          "
        >

          {/* EXPERT */}

          <div
            className="
              mb-2
            "
          >

            <span
              className="
                inline-flex
                rounded-full
                bg-emerald-50
                px-2.5
                py-1
                text-xs
                font-medium
                text-emerald-700
              "
            >
              {displayName}
            </span>

          </div>

          {/* DIGEST */}

          <div
            className="
              flex
              flex-wrap
              items-center
              gap-x-2
              gap-y-1
            "
          >

            <span
              className="
                text-sm
                font-semibold
                text-gray-900
                group-hover:underline
              "
            >
              {frequency}
            </span>

            {(periodStart ||
              periodEnd) && (

              <>

                <span
                  className="
                    text-gray-300
                  "
                >
                  •
                </span>

                <span
                  className="
                    text-sm
                    text-gray-500
                  "
                >
                  {periodStart}

                  {periodStart &&
                    periodEnd &&
                    " → "}

                  {periodEnd}

                </span>

              </>

            )}

          </div>

          {/* COMPANY */}

          {digest.COMPANY && (

            <div
              className="
                mt-2
                text-sm
                text-gray-500
              "
            >
              {digest.COMPANY}
            </div>

          )}

        </div>

        {/* =================================================
            CONTENT COUNT
        ================================================= */}

        {typeof digest.TOTAL_CONTENTS ===
          "number" && (

          <div
            className="
              hidden
              shrink-0
              rounded-full
              bg-gray-100
              px-3
              py-1
              text-xs
              text-gray-600
              md:block
            "
          >
            {digest.TOTAL_CONTENTS} contents
          </div>

        )}

        {/* =================================================
            OPEN
        ================================================= */}

        <ChevronRight
          size={18}
          className="
            shrink-0
            text-gray-300
            transition
            group-hover:translate-x-0.5
            group-hover:text-gray-500
          "
        />

      </div>

    </button>

  );

}
