"use client";

import type {
  TouchConsolidation,
  TouchCoverageDimension,
} from "@/types/touch";


/* =========================================================
   PROPS
========================================================= */

type Props = {
  consolidation:
    TouchConsolidation | null;

  onFollowUp: (
    query: string
  ) => void;
};


/* =========================================================
   FORMAT DIMENSION
========================================================= */

function formatDimension(
  dimension: TouchCoverageDimension,
): string {

  return dimension
    .toLowerCase()
    .replaceAll(
      "_",
      " ",
    )
    .replace(
      /^./,
      value =>
        value.toUpperCase(),
    );

}


/* =========================================================
   COMPONENT
========================================================= */

export default function TouchResearchCoverage({
  consolidation,
  onFollowUp,
}: Props) {

  if (!consolidation) {
    return null;
  }

  const {
    event_groups: eventGroups,
    coverage_analysis: coverage,
  } = consolidation;

  const hasCoverage = Boolean(

    coverage.summary

    || coverage
      .covered_dimensions
      .length

    || coverage
      .missing_dimensions
      .length

    || coverage.strengths.length

    || coverage.gaps.length

    || coverage
      .contradictions
      .length

    || coverage
      .suggested_follow_ups
      .length

    || eventGroups.length

  );

  if (!hasCoverage) {
    return null;
  }

  return (

    <section
      className="
        rounded-xl
        border
        border-gray-200
        bg-white
      "
    >

      {/* ================================================= */}
      {/* HEADER */}
      {/* ================================================= */}

      <div
        className="
          border-b
          border-gray-100
          px-5
          py-4
        "
      >

        <h2
          className="
            text-base
            font-semibold
            text-gray-900
          "
        >
          Research coverage
        </h2>

        <p className="mt-1 text-sm text-gray-500">
          What the proposed material covers and
          what may still be missing.
        </p>

      </div>

      <div className="p-5 space-y-6">

        {/* ================================================= */}
        {/* SUMMARY */}
        {/* ================================================= */}

        {coverage.summary && (

          <p
            className="
              text-sm
              leading-6
              text-gray-700
            "
          >
            {coverage.summary}
          </p>

        )}

        {/* ================================================= */}
        {/* DIMENSIONS */}
        {/* ================================================= */}

        {(
          coverage
            .covered_dimensions
            .length > 0

          || coverage
            .missing_dimensions
            .length > 0
        ) && (

          <div
            className="
              grid
              grid-cols-1
              gap-5
              md:grid-cols-2
            "
          >

            <DimensionGroup
              title="Covered"
              tone="covered"
              dimensions={
                coverage
                  .covered_dimensions
              }
            />

            <DimensionGroup
              title="Missing"
              tone="missing"
              dimensions={
                coverage
                  .missing_dimensions
              }
            />

          </div>

        )}

        {/* ================================================= */}
        {/* STRENGTHS */}
        {/* ================================================= */}

        {coverage.strengths.length > 0 && (

          <TextList
            title="Strengths"
            items={
              coverage.strengths
            }
          />

        )}

        {/* ================================================= */}
        {/* GAPS */}
        {/* ================================================= */}

        {coverage.gaps.length > 0 && (

          <TextList
            title="Research gaps"
            items={
              coverage.gaps
            }
          />

        )}

        {/* ================================================= */}
        {/* CONTRADICTIONS */}
        {/* ================================================= */}

        {(
          coverage
            .contradictions
            .length > 0
        ) && (

          <TextList
            title="Contradictions"
            items={
              coverage
                .contradictions
            }
            tone="warning"
          />

        )}

        {/* ================================================= */}
        {/* EVENT GROUPS */}
        {/* ================================================= */}

        {eventGroups.length > 0 && (

          <div>

            <h3
              className="
                text-sm
                font-semibold
                text-gray-900
              "
            >
              Identified events
            </h3>

            <div className="mt-3 space-y-3">

              {eventGroups.map(
                eventGroup => (

                  <details
                    key={
                      eventGroup.event_key
                    }
                    className="
                      rounded-lg
                      border
                      border-gray-200
                      bg-gray-50
                    "
                  >

                    <summary
                      className="
                        cursor-pointer
                        list-none
                        px-4
                        py-3
                      "
                    >

                      <div
                        className="
                          flex
                          items-center
                          justify-between
                          gap-3
                        "
                      >

                        <span
                          className="
                            text-sm
                            font-medium
                            text-gray-900
                          "
                        >
                          {eventGroup.label}
                        </span>

                        <span
                          className="
                            shrink-0
                            rounded-full
                            bg-white
                            px-2
                            py-1
                            text-xs
                            text-gray-500
                          "
                        >
                          {
                            eventGroup
                              .content_ids
                              .length
                          }
                          {" "}
                          sources
                        </span>

                      </div>

                    </summary>

                    <div
                      className="
                        border-t
                        border-gray-200
                        bg-white
                        px-4
                        py-4
                        space-y-4
                      "
                    >

                      {(
                        eventGroup
                          .shared_information
                          .length > 0
                      ) && (

                        <TextList
                          title="Shared information"
                          items={
                            eventGroup
                              .shared_information
                          }
                        />

                      )}

                      {(
                        eventGroup
                          .complementary_contributions
                          .length > 0
                      ) && (

                        <TextList
                          title="Complementary contributions"
                          items={
                            eventGroup
                              .complementary_contributions
                          }
                        />

                      )}

                      {(
                        eventGroup
                          .contradictions
                          .length > 0
                      ) && (

                        <TextList
                          title="Contradictions"
                          items={
                            eventGroup
                              .contradictions
                          }
                          tone="warning"
                        />

                      )}

                    </div>

                  </details>

                ),
              )}

            </div>

          </div>

        )}

        {/* ================================================= */}
        {/* FOLLOW UPS */}
        {/* ================================================= */}

        {(
          coverage
            .suggested_follow_ups
            .length > 0
        ) && (

          <div>

            <h3
              className="
                text-sm
                font-semibold
                text-gray-900
              "
            >
              Suggested follow-ups
            </h3>

            <div className="mt-3 space-y-2">

              {
                coverage
                  .suggested_follow_ups
                  .map(
                    (
                      followUp,
                      index,
                    ) => (

                      <button
                        key={
                          `${followUp}-${index}`
                        }
                        type="button"
                        onClick={() =>
                          onFollowUp(
                            followUp,
                          )
                        }
                        className="
                          w-full
                          rounded-lg
                          border
                          border-gray-200
                          bg-white
                          px-4
                          py-3
                          text-left
                          text-sm
                          leading-5
                          text-gray-700
                          hover:border-ratecard-blue
                          hover:bg-blue-50
                        "
                      >
                        {followUp}
                      </button>

                    ),
                  )
              }

            </div>

          </div>

        )}

      </div>

    </section>

  );

}


/* =========================================================
   DIMENSION GROUP
========================================================= */

type DimensionGroupProps = {
  title: string;

  tone:
    | "covered"
    | "missing";

  dimensions:
    TouchCoverageDimension[];
};


function DimensionGroup({
  title,
  tone,
  dimensions,
}: DimensionGroupProps) {

  if (
    dimensions.length === 0
  ) {
    return null;
  }

  return (

    <div>

      <h3
        className="
          text-xs
          font-medium
          uppercase
          tracking-wide
          text-gray-500
        "
      >
        {title}
      </h3>

      <div className="mt-2 flex flex-wrap gap-2">

        {dimensions.map(
          dimension => (

            <span
              key={dimension}
              className={`
                rounded-full
                border
                px-2.5
                py-1
                text-xs
                ${
                  tone === "covered"
                    ? (
                        "border-emerald-200 "
                        + "bg-emerald-50 "
                        + "text-emerald-700"
                      )
                    : (
                        "border-amber-200 "
                        + "bg-amber-50 "
                        + "text-amber-700"
                      )
                }
              `}
            >
              {
                formatDimension(
                  dimension,
                )
              }
            </span>

          ),
        )}

      </div>

    </div>

  );

}


/* =========================================================
   TEXT LIST
========================================================= */

type TextListProps = {
  title: string;
  items: string[];

  tone?:
    | "default"
    | "warning";
};


function TextList({
  title,
  items,
  tone = "default",
}: TextListProps) {

  if (
    items.length === 0
  ) {
    return null;
  }

  return (

    <div>

      <h3
        className="
          text-xs
          font-medium
          uppercase
          tracking-wide
          text-gray-500
        "
      >
        {title}
      </h3>

      <ul className="mt-2 space-y-2">

        {items.map(
          (
            item,
            index,
          ) => (

            <li
              key={
                `${item}-${index}`
              }
              className={`
                flex
                gap-2
                text-sm
                leading-5
                ${
                  tone === "warning"
                    ? "text-amber-800"
                    : "text-gray-700"
                }
              `}
            >

              <span
                className={`
                  mt-2
                  h-1
                  w-1
                  shrink-0
                  rounded-full
                  ${
                    tone === "warning"
                      ? "bg-amber-500"
                      : "bg-gray-400"
                  }
                `}
              />

              <span>
                {item}
              </span>

            </li>

          ),
        )}

      </ul>

    </div>

  );

}
