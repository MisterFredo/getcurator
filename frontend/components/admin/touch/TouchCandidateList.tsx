"use client";

import type {
  TouchContentCandidate,
  TouchContentDecision,
  TouchContentRelevance,
} from "@/types/touch";


/* =========================================================
   PROPS
========================================================= */

type Props = {
  candidate: TouchContentCandidate;

  decision:
    TouchContentDecision | null;

  selected: boolean;
  dismissed: boolean;

  onToggle: () => void;
  onDismiss: () => void;
  onRestore: () => void;

  onOpen?: () => void;
};


/* =========================================================
   RELEVANCE LABEL
========================================================= */

function getRelevanceLabel(
  relevance: TouchContentRelevance,
): string {

  const labels:
    Record<
      TouchContentRelevance,
      string
    > = {

      DIRECT:
        "Direct",

      CONTEXT:
        "Context",

      RELATED:
        "Related",

      OUT_OF_SCOPE:
        "Out of scope",

    };

  return labels[
    relevance
  ];

}


/* =========================================================
   RELEVANCE CLASSES
========================================================= */

function getRelevanceClasses(
  relevance: TouchContentRelevance,
): string {

  const classes:
    Record<
      TouchContentRelevance,
      string
    > = {

      DIRECT:
        (
          "border-emerald-200 "
          + "bg-emerald-50 "
          + "text-emerald-700"
        ),

      CONTEXT:
        (
          "border-blue-200 "
          + "bg-blue-50 "
          + "text-blue-700"
        ),

      RELATED:
        (
          "border-amber-200 "
          + "bg-amber-50 "
          + "text-amber-700"
        ),

      OUT_OF_SCOPE:
        (
          "border-gray-200 "
          + "bg-gray-50 "
          + "text-gray-500"
        ),

    };

  return classes[
    relevance
  ];

}


/* =========================================================
   FORMAT DATE
========================================================= */

function formatDate(
  value: string | null,
): string {

  if (!value) {
    return "";
  }

  const date =
    new Date(
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
    "fr-FR",
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
   GET ENTITY LABEL
========================================================= */

function getEntityLabel(
  entity: TouchContentCandidate[
    "companies"
  ][number],
): string {

  return (

    entity.name

    || entity.label

    || entity.canonical_label

    || entity.title

    || ""

  );

}


/* =========================================================
   COMPONENT
========================================================= */

export default function TouchCandidateCard({
  candidate,
  decision,
  selected,
  dismissed,
  onToggle,
  onDismiss,
  onRestore,
  onOpen,
}: Props) {

  const publishedAt =
    formatDate(
      candidate.published_at,
    );

  const companyLabels =
    candidate.companies
      .map(
        getEntityLabel,
      )
      .filter(
        Boolean,
      )
      .slice(
        0,
        5,
      );

  /* =======================================================
     RENDER
  ======================================================= */

  return (

    <article
      className={`
        rounded-xl
        border
        bg-white
        transition
        ${
          selected
            ? (
                "border-ratecard-blue "
                + "ring-1 "
                + "ring-ratecard-blue"
              )
            : "border-gray-200"
        }
        ${
          dismissed
            ? "opacity-50"
            : ""
        }
      `}
    >

      <div className="p-5 space-y-4">

        {/* ================================================= */}
        {/* HEADER */}
        {/* ================================================= */}

        <div
          className="
            flex
            items-start
            gap-4
          "
        >

          <input
            type="checkbox"
            checked={selected}
            disabled={dismissed}
            onChange={onToggle}
            aria-label={
              `Select ${candidate.title}`
            }
            className="
              mt-1
              h-4
              w-4
              rounded
              border-gray-300
              text-ratecard-blue
              focus:ring-ratecard-blue
            "
          />

          <div className="min-w-0 flex-1">

            <div
              className="
                flex
                flex-wrap
                items-center
                gap-2
                mb-2
              "
            >

              {decision && (

                <span
                  className={`
                    inline-flex
                    items-center
                    rounded-full
                    border
                    px-2.5
                    py-1
                    text-xs
                    font-medium
                    ${getRelevanceClasses(
                      decision.relevance,
                    )}
                  `}
                >
                  {
                    getRelevanceLabel(
                      decision.relevance,
                    )
                  }
                </span>

              )}

              {decision && (

                <span
                  className="
                    inline-flex
                    items-center
                    rounded-full
                    bg-gray-100
                    px-2.5
                    py-1
                    text-xs
                    font-medium
                    text-gray-700
                  "
                >
                  Score&nbsp;
                  {decision.relevance_score}
                </span>

              )}

              {!decision && (

                <span
                  className="
                    inline-flex
                    items-center
                    rounded-full
                    bg-gray-100
                    px-2.5
                    py-1
                    text-xs
                    text-gray-500
                  "
                >
                  Not evaluated
                </span>

              )}

              {publishedAt && (

                <span className="text-xs text-gray-500">
                  {publishedAt}
                </span>

              )}

            </div>

            <h3
              className="
                text-base
                font-semibold
                leading-snug
                text-gray-900
              "
            >
              {candidate.title}
            </h3>

            {candidate.source_title && (

              <p className="mt-1 text-xs text-gray-500">
                {candidate.source_title}
              </p>

            )}

          </div>

        </div>

        {/* ================================================= */}
        {/* EXCERPT */}
        {/* ================================================= */}

        {candidate.excerpt && (

          <p
            className="
              text-sm
              leading-6
              text-gray-600
            "
          >
            {candidate.excerpt}
          </p>

        )}

        {/* ================================================= */}
        {/* DECISION */}
        {/* ================================================= */}

        {decision?.reason && (

          <div
            className="
              rounded-lg
              bg-gray-50
              px-4
              py-3
            "
          >

            <p
              className="
                text-xs
                font-medium
                uppercase
                tracking-wide
                text-gray-500
              "
            >
              Editorial relevance
            </p>

            <p
              className="
                mt-1
                text-sm
                leading-6
                text-gray-700
              "
            >
              {decision.reason}
            </p>

          </div>

        )}

        {/* ================================================= */}
        {/* CONTRIBUTIONS */}
        {/* ================================================= */}

        {(
          decision
          && decision
            .key_contributions
            .length > 0
        ) && (

          <div>

            <p
              className="
                text-xs
                font-medium
                uppercase
                tracking-wide
                text-gray-500
              "
            >
              Contribution
            </p>

            <ul
              className="
                mt-2
                space-y-1.5
                text-sm
                text-gray-700
              "
            >

              {
                decision
                  .key_contributions
                  .map(
                    (
                      contribution,
                      index,
                    ) => (

                      <li
                        key={
                          `${candidate.content_id}-${index}`
                        }
                        className="flex gap-2"
                      >

                        <span
                          className="
                            mt-2
                            h-1
                            w-1
                            shrink-0
                            rounded-full
                            bg-gray-400
                          "
                        />

                        <span>
                          {contribution}
                        </span>

                      </li>

                    ),
                  )
              }

            </ul>

          </div>

        )}

        {/* ================================================= */}
        {/* DIMENSIONS */}
        {/* ================================================= */}

        {(
          decision
          && decision
            .coverage_dimensions
            .length > 0
        ) && (

          <div className="flex flex-wrap gap-2">

            {
              decision
                .coverage_dimensions
                .map(
                  dimension => (

                    <span
                      key={dimension}
                      className="
                        rounded
                        bg-slate-100
                        px-2
                        py-1
                        text-xs
                        text-slate-600
                      "
                    >
                      {
                        dimension
                          .toLowerCase()
                          .replaceAll(
                            "_",
                            " ",
                          )
                      }
                    </span>

                  ),
                )
            }

          </div>

        )}

        {/* ================================================= */}
        {/* COMPANIES */}
        {/* ================================================= */}

        {companyLabels.length > 0 && (

          <div className="flex flex-wrap gap-2">

            {companyLabels.map(
              label => (

                <span
                  key={label}
                  className="
                    rounded-full
                    bg-blue-50
                    px-2.5
                    py-1
                    text-xs
                    text-blue-700
                  "
                >
                  {label}
                </span>

              ),
            )}

          </div>

        )}

        {/* ================================================= */}
        {/* MATCHES */}
        {/* ================================================= */}

        {candidate.matched_terms.length > 0 && (

          <p className="text-xs text-gray-400">

            Found through:&nbsp;

            {
              candidate
                .matched_terms
                .join(
                  ", ",
                )
            }

          </p>

        )}

        {/* ================================================= */}
        {/* ACTIONS */}
        {/* ================================================= */}

        <div
          className="
            flex
            flex-wrap
            items-center
            justify-between
            gap-3
            border-t
            border-gray-100
            pt-4
          "
        >

          <div>

            {onOpen && (

              <button
                type="button"
                onClick={onOpen}
                className="
                  text-sm
                  font-medium
                  text-ratecard-blue
                  hover:underline
                "
              >
                Open content
              </button>

            )}

          </div>

          <div>

            {dismissed ? (

              <button
                type="button"
                onClick={onRestore}
                className="
                  text-sm
                  text-gray-600
                  hover:text-gray-900
                "
              >
                Restore
              </button>

            ) : (

              <button
                type="button"
                onClick={onDismiss}
                className="
                  text-sm
                  text-gray-400
                  hover:text-red-600
                "
              >
                Dismiss
              </button>

            )}

          </div>

        </div>

      </div>

    </article>

  );

}
