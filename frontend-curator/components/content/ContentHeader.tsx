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

    <div className="space-y-5">

      {/* =====================================================
          META
      ===================================================== */}

      <div className="
        flex
        items-center
        gap-4
      ">

        {logoUrl && (

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
              shrink-0
            "
          >

            <img
              src={logoUrl}
              alt={content.title}
              className="
                w-full
                h-full
                object-contain
              "
            />

          </div>

        )}

        <div className="
          flex-1
          min-w-0
        ">

          {formattedDate && (

            <div className="
              text-xs
              text-gray-400
              mb-1
            ">

              {formattedDate}

            </div>

          )}

          <h1
            className="
              text-2xl
              font-semibold
              leading-tight
              text-gray-900
            "
          >

            {content.title}

          </h1>

          {content.source_title && (

            <div className="
              mt-2
              text-sm
              text-gray-500
            ">

              {content.source_title}

            </div>

          )}

        </div>

      </div>

      {/* =====================================================
          BADGES
      ===================================================== */}

      {content.badges &&
        content.badges.length > 0 && (

        <ContentBadges
          badges={content.badges}
        />

      )}

    </div>

  );

}
