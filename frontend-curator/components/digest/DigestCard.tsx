"use client";

import type {
  DigestHistoryItem,
} from "@/types/digest";

/* ========================================================= */

type Props = {
  digest: DigestHistoryItem;

  onClick: (
    digest: DigestHistoryItem,
  ) => void;
};

/* ========================================================= */

function formatDate(
  value?: string | null,
) {

  if (!value) return "";

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

/* ========================================================= */

export default function DigestCard({
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

  return (

    <button

      type="button"

      onClick={() =>
        onClick(digest)
      }

      className="
        w-full
        rounded-xl
        border
        border-ratecard-border
        bg-white
        p-5
        text-left
        shadow-card
        transition
        hover:shadow-cardHover
      "

    >

      <div
        className="
          flex
          items-start
          justify-between
          gap-4
        "
      >

        <div>

          <div
            className="
              text-xs
              font-semibold
              uppercase
              tracking-wide
              text-gray-400
            "
          >
            {
              digest.FREQUENCY ??
              "Digest"
            }
          </div>

          <div
            className="
              mt-2
              text-base
              font-semibold
              text-gray-900
            "
          >
            {displayName}
          </div>

          {digest.COMPANY && (

            <div
              className="
                mt-1
                text-sm
                text-gray-500
              "
            >
              {digest.COMPANY}
            </div>

          )}

        </div>

        {typeof digest.TOTAL_CONTENTS ===
          "number" && (

          <div
            className="
              shrink-0
              rounded-full
              bg-gray-100
              px-3
              py-1
              text-xs
              text-gray-600
            "
          >
            {
              digest.TOTAL_CONTENTS
            }{" "}
            contents
          </div>

        )}

      </div>

      {(periodStart || periodEnd) && (

        <div
          className="
            mt-5
            border-t
            border-gray-100
            pt-4
            text-sm
            text-gray-500
          "
        >
          {periodStart}

          {periodStart &&
            periodEnd &&
            " → "}

          {periodEnd}
        </div>

      )}

    </button>

  );

}
