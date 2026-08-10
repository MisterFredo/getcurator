"use client";

import ContentBadges from "./ContentBadges";

import type {
  Content,
} from "@/types/watch";

/* ========================================================= */

const GCS_BASE_URL =
  process.env
    .NEXT_PUBLIC_GCS_BASE_URL || "";

/* ========================================================= */

type Props = {

  content: Content;

};

/* ========================================================= */

export default function ContentHeader({

  content,

}: Props) {

  const formattedDate =

    content.published_at

      ? new Date(
          content.published_at,
        ).toLocaleDateString(
          "fr-FR",
        )

      : null;

  const logoUrl =

    content.primary_company_logo

      ? `${GCS_BASE_URL}/companies/${content.primary_company_logo}`

      : null;

  return (

    <header className="space-y-5">

      {/* DATE */}

      {formattedDate && (

        <div
          className="
            text-xs
            uppercase
            tracking-wide
            text-gray-400
          "
        >

          {formattedDate}

        </div>

      )}

      {/* TITLE */}

      <div
        className="
          flex
          items-start
          gap-4
        "
      >

        {logoUrl && (

          <img
            src={logoUrl}
            alt=""
            className="
              w-12
              h-12
              rounded-lg
              object-contain
              shrink-0
              border
              border-gray-200
              bg-white
            "
          />

        )}

        <div className="flex-1">

          <h1
            className="
              text-[38px]
              leading-tight
              font-semibold
              text-gray-900
            "
          >

            {content.title}

          </h1>

        </div>

      </div>

      {/* BADGES */}

      {content.badges &&
        content.badges.length > 0 && (

        <ContentBadges
          badges={content.badges}
        />

      )}

      {/* SOURCE */}

      {content.source_title && (

        <div
          className="
            text-sm
            text-gray-500
          "
        >

          {content.source_title}

        </div>

      )}

    </header>

  );

}
