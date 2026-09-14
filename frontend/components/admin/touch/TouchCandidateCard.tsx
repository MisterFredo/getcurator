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
   RELEVANCE STYLES
========================================================= */

const RELEVANCE_STYLES: Record<
  TouchContentRelevance,
  string
> = {

  DIRECT:
    "bg-emerald-100 text-emerald-800",

  CONTEXT:
    "bg-blue-100 text-blue-800",

  RELATED:
    "bg-amber-100 text-amber-800",

  OUT_OF_SCOPE:
    "bg-gray-100 text-gray-600",

};


/* =========================================================
   RELEVANCE LABELS
========================================================= */

const RELEVANCE_LABELS: Record<
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


/* =========================================================
   FORMAT DATE
========================================================= */

function formatDate(
  value: string | null,
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
   ENTITY LABEL
========================================================= */

function getEntityLabel(
  entity: Record<string, unknown>,
): string {

  const value = (
    entity.name
    ?? entity.label
    ?? entity.canonical_label
    ?? entity.title
  );

  return (
    typeof value === "string"
      ? value
      : ""
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

  const date = formatDate(
    candidate.published_at,
  );

  const companyLabels =
    candidate.companies
      .map(getEntityLabel)
      .filter(Boolean)
      .slice(0, 5);

  /* =======================================================
     DISMISSED
  ======================================================= */

  if (dismissed) {

    return (

      <div
        className="
          flex
          items-center
          justify-between
          gap-4
          rounded-lg
          border
          border-gray-200
          bg-gray-50
          px-4
          py-3
        "
      >

        <div className="min-w-0">

          <p
            className="
              truncate
              text-sm
              text-gray-500
              line-through
            "
          >
            {candidate.title}
          </p>

        </div>

        <button
          type="button"
          onClick={onRestore}
          className="
            shrink-0
            text-sm
            font-medium
            text-ratecard-blue
            hover:underline
          "
        >
          Restore
        </button>

      </div>

    );

  }

  /* =======================================================
     RENDER
  ======================================================= */

  return (

    <article
      className={`
        rounded-xl
        border
        bg-white
        p-5
        transition
        ${
          selected
            ? (
                "border-ratecard-blue "
                + "ring-2 ring-blue-100"
              )
            : (
                "border-gray-200 "
                + "hover:border-gray-300"
              )
        }
      `}
    >

      <div className="flex items-start gap-4">

        {/* ================================================= */}
        {/* CHECKBOX */}
        {/* ================================================= */}

        <div className="pt-1">

          <input
            type="checkbox"
            checked={selected}
            onChange={onToggle}
            aria-label={
              `Select ${candidate.title}`
            }
            className="
              h-4
              w-4
              cursor-pointer
              rounded
              border-gray-300
              text-ratecard-blue
              focus:ring-ratecard-blue
            "
          />

        </div>

        {/* ================================================= */}
        {/* CONTENT */}
        {/* ================================================= */}

        <div className="min-w-0 flex-1">

          {/* =============================================== */}
          {/* META */}
          {/* =============================================== */}

          <div
            className="
              mb-3
              flex
              flex-wrap
              items-center
              gap-2
            "
          >

            {decision && (

              <span
                className={`
                  rounded-full
                  px-2.5
                  py-1
                  text-xs
                  font-medium
                  ${RELEVANCE_STYLES[
                    decision.relevance
                  ]}
                `}
              >
                {
                  RELEVANCE_LABELS[
                    decision.relevance
                  ]
                }
              </span>

            )}

            {decision && (

              <span
                className="
                  rounded-full
                  bg-gray-100
                  px-2.5
                  py-1
                  text-xs
                  font-medium
                  text-gray-700
                "
              >
                {decision.relevance_score}/100
              </span>

            )}

            {date && (

              <span className="text-xs text-gray-500">
                {date}
              </span>

            )}

          </div>

          {/* =============================================== */}
          {/* TITLE */}
          {/* =============================================== */}

          <h3
            className="
              text-lg
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

          {/* =============================================== */}
          {/* EXCERPT */}
          {/* =============================================== */}

          {candidate.excerpt && (

            <p
              className="
                mt-3
                text-sm
                leading-6
                text-gray-600
              "
            >
              {candidate.excerpt}
            </p>

          )}

          {/* =============================================== */}
          {/* COMPANIES */}
          {/* =============================================== */}

          {companyLabels.length > 0 && (

            <div
              className="
                mt-3
                flex
                flex-wrap
                gap-2
              "
            >

              {companyLabels.map(
                label => (

                  <span
                    key={label}
                    className="
                      rounded
                      bg-gray-100
                      px-2
                      py-1
                      text-xs
                      text-gray-600
                    "
                  >
                    {label}
                  </span>

                ),
              )}

            </div>

          )}

          {/* =============================================== */}
          {/* REASON */}
          {/* =============================================== */}

          {decision?.reason && (

            <div
              className="
                mt-4
                rounded-lg
                border
                border-gray-100
                bg-gray-50
                px-4
                py-3
              "
            >

              <p
                className="
                  text-xs
                  font-semibold
                  uppercase
                  tracking-wide
                  text-gray-500
                "
              >
                Why it matters
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

          {/* =============================================== */}
          {/* CONTRIBUTIONS */}
          {/* =============================================== */}

          {
            decision
            && decision
              .key_contributions
              .length > 0
            && (

              <div className="mt-4">

                <p
                  className="
                    text-xs
                    font-semibold
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
                    space-y-1
                    text-sm
                    text-gray-700
                  "
                >

                  {
                    decision
                      .key_contributions
                      .map(
                        contribution => (

                          <li
                            key={contribution}
                            className="flex gap-2"
                          >

                            <span
                              className="
                                mt-2
                                h-1
                                w-1
                                shrink-0
                                rounded-full
                                bg-ratecard-blue
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

            )
          }

          {/* =============================================== */}
          {/* DIMENSIONS */}
          {/* =============================================== */}

          {
            decision
            && decision
              .coverage_dimensions
              .length > 0
            && (

              <div
                className="
                  mt-4
                  flex
                  flex-wrap
                  gap-2
                "
              >

                {
                  decision
                    .coverage_dimensions
                    .map(
                      dimension => (

                        <span
                          key={dimension}
                          className="
                            rounded-full
                            border
                            border-gray-200
                            px-2.5
                            py-1
                            text-xs
                            text-gray-600
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

            )
          }

          {/* =============================================== */}
          {/* ACTIONS */}
          {/* =============================================== */}

          <div
            className="
              mt-5
              flex
              flex-wrap
              items-center
              gap-4
            "
          >

            <button
              type="button"
              onClick={onToggle}
              className="
                text-sm
                font-medium
                text-ratecard-blue
                hover:underline
              "
            >
              {
                selected
                  ? "Remove from corpus"
                  : "Add to corpus"
              }
            </button>

            {onOpen && (

              <button
                type="button"
                onClick={onOpen}
                className="
                  text-sm
                  text-gray-600
                  hover:text-gray-900
                  hover:underline
                "
              >
                Open content
              </button>

            )}

            <button
              type="button"
              onClick={onDismiss}
              className="
                text-sm
                text-gray-500
                hover:text-red-600
              "
            >
              Dismiss
            </button>

          </div>

        </div>

      </div>

    </article>

  );

}
