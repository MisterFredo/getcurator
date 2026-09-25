"use client";

import type {
  DigestDocument,
} from "@/types/digest";

import DigestSection from "./DigestSection";


/* =========================================================
   PROPS
========================================================= */

type Props = {

  document: DigestDocument;

};


/* =========================================================
   FORMAT DATE
========================================================= */

function formatDate(
  value?: string | null,
): string {

  if (!value) {
    return "";
  }

  const date = new Date(
    value,
  );

  if (
    Number.isNaN(
      date.getTime(),
    )
  ) {
    return "";
  }

  return new Intl.DateTimeFormat(
    "en-GB",
    {
      day: "2-digit",
      month: "short",
      year: "numeric",
    },
  ).format(
    date,
  );

}


/* =========================================================
   DIGEST PREVIEW
========================================================= */

export default function DigestPreview({
  document,
}: Props) {

  const additionalContents =
    document.additional_contents
    ?? [];

  return (

    <div className="space-y-6">

      {/* ================================================= */}
      {/* HEADER */}
      {/* ================================================= */}

      <div className="rounded-lg border bg-white p-6">

        <h1 className="text-3xl font-bold">

          {document.title}

        </h1>

        {document.subtitle && (

          <p className="mt-2 text-gray-600">

            {document.subtitle}

          </p>

        )}

        <div className="mt-4 text-sm text-gray-500">

          {document.period}

        </div>

      </div>

      {/* ================================================= */}
      {/* MAIN SECTIONS */}
      {/* ================================================= */}

      {document.sections.map(
        (
          section,
          index,
        ) => (

          <DigestSection
            key={`${section.title}-${index}`}
            section={section}
          />

        ),
      )}

      {/* ================================================= */}
      {/* ADDITIONAL CONTENTS */}
      {/* ================================================= */}

      {additionalContents.length > 0 && (

        <section
          className="
            rounded-lg
            border
            border-gray-200
            bg-white
            p-6
          "
        >

          <h2
            className="
              text-xl
              font-semibold
              text-gray-900
            "
          >

            Also on Your Radar

          </h2>

          <p
            className="
              mt-2
              text-sm
              text-gray-500
            "
          >

            Additional signals identified during
            this week&apos;s review.

          </p>

          <div
            className="
              mt-5
              divide-y
              divide-gray-200
            "
          >

            {additionalContents.map(
              card => {

                const publishedAt =
                  formatDate(
                    card.published_at,
                  );

                const metadata = [

                  card.source_title,

                  publishedAt,

                ]
                  .filter(Boolean)
                  .join(" • ");

                return (

                  <article
                    key={card.id}
                    className="py-4 first:pt-0 last:pb-0"
                  >

                    <h3
                      className="
                        text-base
                        font-semibold
                        text-gray-900
                      "
                    >

                      <a
                        href={card.url}
                        target="_blank"
                        rel="noopener noreferrer"
                        className="
                          transition-colors
                          hover:text-ratecard-blue
                          hover:underline
                        "
                      >

                        {card.title}

                      </a>

                    </h3>

                    {metadata && (

                      <p
                        className="
                          mt-1
                          text-xs
                          text-gray-500
                        "
                      >

                        {metadata}

                      </p>

                    )}

                    {card.selection_reason && (

                      <p
                        className="
                          mt-2
                          text-sm
                          leading-6
                          text-gray-600
                        "
                      >

                        {card.selection_reason}

                      </p>

                    )}

                    <a
                      href={card.url}
                      target="_blank"
                      rel="noopener noreferrer"
                      className="
                        mt-3
                        inline-block
                        text-sm
                        font-medium
                        text-ratecard-blue
                        hover:underline
                      "
                    >

                      Read on GetCurator →

                    </a>

                  </article>

                );

              },
            )}

          </div>

        </section>

      )}

    </div>

  );

}
