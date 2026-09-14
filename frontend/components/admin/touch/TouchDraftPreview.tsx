"use client";

import type {
  TouchDocumentSource,
  TouchOnePagerDraft,
} from "@/types/touch";


type Props = {
  draft: TouchOnePagerDraft;
  sources: TouchDocumentSource[];
};


function formatDate(
  value: string | null,
) {

  if (!value) {
    return "";
  }

  const date =
    new Date(value);

  if (
    Number.isNaN(
      date.getTime(),
    )
  ) {
    return "";
  }

  return new Intl.DateTimeFormat(
    "fr-FR",
    {
      day: "2-digit",
      month: "short",
      year: "numeric",
    },
  ).format(date);

}


export default function TouchDraftPreview({
  draft,
  sources,
}: Props) {

  const sourceNumberById =
    new Map<string, number>();

  sources.forEach(
    (
      source,
      index,
    ) => {

      sourceNumberById.set(
        source.content_id,
        index + 1,
      );

    },
  );

  function renderSourceReferences(
    contentIds: string[],
  ) {

    const references =
      contentIds
        .map(
          contentId => ({
            contentId,
            number:
              sourceNumberById.get(
                contentId,
              ),
          }),
        )
        .filter(
          reference =>
            reference.number
            !== undefined,
        );

    if (
      references.length === 0
    ) {
      return null;
    }

    return (

      <div className="mt-3 flex flex-wrap gap-1.5">

        {references.map(
          reference => (

            <a
              key={reference.contentId}
              href={
                `#touch-source-${reference.contentId}`
              }
              className="
                inline-flex
                h-6
                min-w-6
                items-center
                justify-center
                rounded-full
                bg-gray-100
                px-2
                text-xs
                font-medium
                text-gray-600
                hover:bg-blue-100
                hover:text-ratecard-blue
              "
            >
              {reference.number}
            </a>

          ),
        )}

      </div>

    );

  }

  return (

    <article
      className="
        overflow-hidden
        rounded-xl
        border
        border-gray-200
        bg-white
      "
    >

      {/* ================================================= */}
      {/* HEADER */}
      {/* ================================================= */}

      <header
        className="
          border-b
          border-gray-200
          px-8
          py-10
        "
      >

        <p
          className="
            text-xs
            font-semibold
            uppercase
            tracking-[0.2em]
            text-ratecard-blue
          "
        >
          GetCurator Touch
        </p>

        <h1
          className="
            mt-4
            max-w-4xl
            text-3xl
            font-semibold
            leading-tight
            text-gray-950
          "
        >
          {draft.title}
        </h1>

        <p
          className="
            mt-4
            max-w-3xl
            text-lg
            leading-7
            text-gray-600
          "
        >
          {draft.subtitle}
        </p>

      </header>

      <div className="px-8 py-8 space-y-10">

        {/* ================================================= */}
        {/* EXECUTIVE TAKEAWAYS */}
        {/* ================================================= */}

        {draft.executive_takeaways.length > 0 && (

          <section>

            <h2
              className="
                text-xl
                font-semibold
                text-gray-900
              "
            >
              Executive Takeaways
            </h2>

            <div
              className="
                mt-4
                grid
                grid-cols-1
                gap-4
                lg:grid-cols-2
              "
            >

              {draft.executive_takeaways.map(
                (
                  takeaway,
                  index,
                ) => (

                  <div
                    key={index}
                    className="
                      rounded-lg
                      border
                      border-blue-100
                      bg-blue-50
                      p-5
                    "
                  >

                    <div
                      className="
                        flex
                        items-start
                        gap-3
                      "
                    >

                      <span
                        className="
                          flex
                          h-7
                          w-7
                          shrink-0
                          items-center
                          justify-center
                          rounded-full
                          bg-ratecard-blue
                          text-xs
                          font-semibold
                          text-white
                        "
                      >
                        {index + 1}
                      </span>

                      <p
                        className="
                          text-sm
                          font-medium
                          leading-6
                          text-gray-800
                        "
                      >
                        {takeaway.statement}
                      </p>

                    </div>

                    {renderSourceReferences(
                      takeaway.source_content_ids,
                    )}

                  </div>

                ),
              )}

            </div>

          </section>

        )}

        {/* ================================================= */}
        {/* NARRATIVE SECTIONS */}
        {/* ================================================= */}

        {draft.sections.map(
          section => (

            <section
              key={
                section.section_type
              }
              className="
                border-t
                border-gray-100
                pt-8
              "
            >

              <p
                className="
                  text-xs
                  font-medium
                  uppercase
                  tracking-wide
                  text-gray-400
                "
              >
                {
                  section
                    .section_type
                    .toLowerCase()
                    .replaceAll(
                      "_",
                      " ",
                    )
                }
              </p>

              <h2
                className="
                  mt-2
                  text-2xl
                  font-semibold
                  text-gray-900
                "
              >
                {section.title}
              </h2>

              <div
                className="
                  mt-4
                  max-w-4xl
                  whitespace-pre-line
                  text-base
                  leading-7
                  text-gray-700
                "
              >
                {section.body}
              </div>

              {renderSourceReferences(
                section.source_content_ids,
              )}

            </section>

          ),
        )}

        {/* ================================================= */}
        {/* KEY NUMBERS */}
        {/* ================================================= */}

        {draft.key_numbers.length > 0 && (

          <section
            className="
              border-t
              border-gray-100
              pt-8
            "
          >

            <h2
              className="
                text-xl
                font-semibold
                text-gray-900
              "
            >
              Key Numbers
            </h2>

            <div
              className="
                mt-4
                grid
                grid-cols-1
                gap-4
                md:grid-cols-2
                xl:grid-cols-3
              "
            >

              {draft.key_numbers.map(
                (
                  number,
                  index,
                ) => (

                  <div
                    key={index}
                    className="
                      rounded-lg
                      border
                      border-gray-200
                      p-5
                    "
                  >

                    <p
                      className="
                        text-3xl
                        font-semibold
                        text-ratecard-blue
                      "
                    >
                      {number.value}
                    </p>

                    <p
                      className="
                        mt-2
                        text-sm
                        font-semibold
                        text-gray-900
                      "
                    >
                      {number.label}
                    </p>

                    <p
                      className="
                        mt-2
                        text-sm
                        leading-5
                        text-gray-600
                      "
                    >
                      {number.context}
                    </p>

                    {renderSourceReferences(
                      number.source_content_ids,
                    )}

                  </div>

                ),
              )}

            </div>

          </section>

        )}

        {/* ================================================= */}
        {/* WHAT TO WATCH */}
        {/* ================================================= */}

        {draft.what_to_watch.length > 0 && (

          <section
            className="
              border-t
              border-gray-100
              pt-8
            "
          >

            <h2
              className="
                text-xl
                font-semibold
                text-gray-900
              "
            >
              What to Watch
            </h2>

            <div className="mt-4 space-y-4">

              {draft.what_to_watch.map(
                (
                  watchPoint,
                  index,
                ) => (

                  <div
                    key={index}
                    className="
                      rounded-lg
                      border-l-4
                      border-ratecard-blue
                      bg-gray-50
                      px-5
                      py-4
                    "
                  >

                    <h3
                      className="
                        text-sm
                        font-semibold
                        text-gray-900
                      "
                    >
                      {watchPoint.label}
                    </h3>

                    <p
                      className="
                        mt-1
                        text-sm
                        leading-6
                        text-gray-600
                      "
                    >
                      {watchPoint.explanation}
                    </p>

                    {renderSourceReferences(
                      watchPoint.source_content_ids,
                    )}

                  </div>

                ),
              )}

            </div>

          </section>

        )}

        {/* ================================================= */}
        {/* SOURCES */}
        {/* ================================================= */}

        {sources.length > 0 && (

          <section
            className="
              border-t
              border-gray-100
              pt-8
            "
          >

            <h2
              className="
                text-xl
                font-semibold
                text-gray-900
              "
            >
              Sources
            </h2>

            <ol className="mt-4 space-y-3">

              {sources.map(
                (
                  source,
                  index,
                ) => {

                  const publishedAt =
                    formatDate(
                      source.published_at,
                    );

                  return (

                    <li
                      key={
                        source.content_id
                      }
                      id={
                        `touch-source-${source.content_id}`
                      }
                      className="
                        flex
                        scroll-mt-8
                        gap-3
                        text-sm
                      "
                    >

                      <span
                        className="
                          flex
                          h-6
                          min-w-6
                          shrink-0
                          items-center
                          justify-center
                          rounded-full
                          bg-gray-100
                          px-2
                          text-xs
                          font-medium
                          text-gray-600
                        "
                      >
                        {index + 1}
                      </span>

                      <div>

                        {source.source_url ? (

                          <a
                            href={
                              source.source_url
                            }
                            target="_blank"
                            rel="noreferrer"
                            className="
                              font-medium
                              text-gray-900
                              hover:text-ratecard-blue
                              hover:underline
                            "
                          >
                            {source.title}
                          </a>

                        ) : (

                          <p
                            className="
                              font-medium
                              text-gray-900
                            "
                          >
                            {source.title}
                          </p>

                        )}

                        <p className="mt-1 text-xs text-gray-500">

                          {
                            source.source_title
                          }

                          {(
                            source.source_title
                            && publishedAt
                          ) && " · "}

                          {publishedAt}

                        </p>

                      </div>

                    </li>

                  );

                },
              )}

            </ol>

          </section>

        )}

      </div>

    </article>

  );

}
