"use client";

import type {
  TouchGuidedEntityMention,
  TouchGuidedResearchPlan,
} from "@/types/touch";


/* =========================================================
   PROPS
========================================================= */

type Props = {
  plan:
    TouchGuidedResearchPlan;

  unresolvedEntityMentions:
    TouchGuidedEntityMention[];

  onValidate:
    () => void;

  validating?:
    boolean;
};


/* =========================================================
   FORMAT DATE
========================================================= */

function formatDate(
  value: string | null,
): string {

  if (!value) {
    return "Open";
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
    return value;
  }

  return date.toLocaleDateString(
    undefined,
    {
      year:
        "numeric",

      month:
        "short",

      day:
        "numeric",
    },
  );

}


/* =========================================================
   LIST BLOCK
========================================================= */

type ListBlockProps = {
  title:
    string;

  values:
    string[];

  emptyLabel?:
    string;
};


function ListBlock({
  title,
  values,
  emptyLabel = "None",
}: ListBlockProps) {

  return (

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
        {title}
      </p>

      {
        values.length > 0
          ? (

              <ul
                className="
                  mt-2
                  space-y-1.5
                  text-sm
                  leading-6
                  text-gray-700
                "
              >

                {values.map(
                  (
                    value,
                    index,
                  ) => (

                    <li
                      key={
                        `${value}-${index}`
                      }
                      className="
                        flex
                        items-start
                        gap-2
                      "
                    >

                      <span
                        aria-hidden="true"
                        className="
                          mt-2
                          h-1.5
                          w-1.5
                          shrink-0
                          rounded-full
                          bg-gray-400
                        "
                      />

                      <span>
                        {value}
                      </span>

                    </li>

                  ),
                )}

              </ul>

            )
          : (

              <p
                className="
                  mt-2
                  text-sm
                  text-gray-400
                "
              >
                {emptyLabel}
              </p>

            )
      }

    </div>

  );

}


/* =========================================================
   COMPONENT
========================================================= */

export default function TouchGuidedResearchPlan({
  plan,
  unresolvedEntityMentions,
  onValidate,
  validating = false,
}: Props) {

  const canValidate =
    plan.ready_for_search
    && unresolvedEntityMentions.length === 0
    && !validating;

  return (

    <section
      className="
        rounded-xl
        border
        border-blue-200
        bg-white
        overflow-hidden
      "
    >

      {/* ================================================= */}
      {/* HEADER */}
      {/* ================================================= */}

      <div
        className="
          border-b
          border-blue-100
          bg-blue-50
          px-6
          py-5
        "
      >

        <div
          className="
            flex
            flex-wrap
            items-start
            justify-between
            gap-4
          "
        >

          <div>

            <p
              className="
                text-xs
                font-medium
                uppercase
                tracking-wide
                text-blue-600
              "
            >
              Guided research plan
            </p>

            <h2
              className="
                mt-1
                text-xl
                font-semibold
                text-gray-900
              "
            >
              {
                plan.subject
                || "Provisional research plan"
              }
            </h2>

            {
              plan.scope_summary
              && (

                <p
                  className="
                    mt-2
                    max-w-4xl
                    text-sm
                    leading-6
                    text-gray-700
                  "
                >
                  {plan.scope_summary}
                </p>

              )
            }

          </div>

          <span
            className="
              rounded-full
              border
              border-blue-200
              bg-white
              px-3
              py-1
              text-xs
              font-medium
              text-blue-700
            "
          >
            {
              plan.research_type
                .replaceAll(
                  "_",
                  " ",
                )
            }
          </span>

        </div>

      </div>

      <div
        className="
          space-y-8
          p-6
        "
      >

        {/* ================================================= */}
        {/* CENTRAL QUESTION */}
        {/* ================================================= */}

        <div
          className="
            grid
            grid-cols-1
            gap-6
            lg:grid-cols-2
          "
        >

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
              Central question
            </p>

            <p
              className="
                mt-2
                text-base
                font-medium
                leading-7
                text-gray-900
              "
            >
              {
                plan.central_question
                || "Not defined yet"
              }
            </p>

          </div>

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
              Research objective
            </p>

            <p
              className="
                mt-2
                text-sm
                leading-6
                text-gray-700
              "
            >
              {
                plan.objective
                || "Not defined yet"
              }
            </p>

          </div>

        </div>

        {/* ================================================= */}
        {/* SCOPE */}
        {/* ================================================= */}

        <div
          className="
            grid
            grid-cols-1
            gap-5
            rounded-lg
            border
            border-gray-200
            bg-gray-50
            p-5
            sm:grid-cols-2
            xl:grid-cols-4
          "
        >

          <div>

            <p className="text-xs font-medium text-gray-500">
              From
            </p>

            <p className="mt-1 text-sm font-medium text-gray-900">
              {formatDate(plan.period_start)}
            </p>

          </div>

          <div>

            <p className="text-xs font-medium text-gray-500">
              To
            </p>

            <p className="mt-1 text-sm font-medium text-gray-900">
              {formatDate(plan.period_end)}
            </p>

          </div>

          <div>

            <p className="text-xs font-medium text-gray-500">
              Target context
            </p>

            <p className="mt-1 text-sm font-medium text-gray-900">
              {
                plan.target_context
                || "Not specified"
              }
            </p>

          </div>

          <div>

            <p className="text-xs font-medium text-gray-500">
              Geographies
            </p>

            <p className="mt-1 text-sm font-medium text-gray-900">
              {
                plan.geographies.length > 0
                  ? plan.geographies.join(", ")
                  : "Open"
              }
            </p>

          </div>

        </div>

        {/* ================================================= */}
        {/* ENTITIES */}
        {/* ================================================= */}

        <div>

          <h3
            className="
              text-base
              font-semibold
              text-gray-900
            "
          >
            Research entities
          </h3>

          {
            plan.resolved_entities.length > 0
              ? (

                  <div
                    className="
                      mt-3
                      flex
                      flex-wrap
                      gap-2
                    "
                  >

                    {plan.resolved_entities.map(
                      entity => (

                        <span
                          key={
                            `${
                              entity.entity_type
                            }-${
                              entity.entity_id
                            }`
                          }
                          className="
                            rounded-full
                            border
                            border-emerald-200
                            bg-emerald-50
                            px-3
                            py-1.5
                            text-xs
                            font-medium
                            text-emerald-800
                          "
                        >
                          {entity.entity_label}
                          {" · "}
                          {entity.entity_type}
                        </span>

                      ),
                    )}

                  </div>

                )
              : (

                  <p
                    className="
                      mt-2
                      text-sm
                      text-gray-500
                    "
                  >
                    No structured entity has been resolved yet.
                  </p>

                )
          }

          {unresolvedEntityMentions.length > 0 && (

            <div
              className="
                mt-4
                rounded-lg
                border
                border-amber-200
                bg-amber-50
                p-4
              "
            >

              <p
                className="
                  text-sm
                  font-medium
                  text-amber-900
                "
              >
                Some entity mentions could not be resolved
              </p>

              <p
                className="
                  mt-1
                  text-sm
                  leading-6
                  text-amber-700
                "
              >
                Select or correct these entities before
                launching the documentary search.
              </p>

              <div
                className="
                  mt-3
                  flex
                  flex-wrap
                  gap-2
                "
              >

                {unresolvedEntityMentions.map(
                  (
                    mention,
                    index,
                  ) => (

                    <span
                      key={
                        `${
                          mention.entity_type
                        }-${
                          mention.entity_label
                        }-${index}`
                      }
                      className="
                        rounded-full
                        border
                        border-amber-300
                        bg-white
                        px-3
                        py-1.5
                        text-xs
                        font-medium
                        text-amber-800
                      "
                    >
                      {mention.entity_label}
                      {" · "}
                      {mention.entity_type}
                    </span>

                  ),
                )}

              </div>

            </div>

          )}

        </div>

        {/* ================================================= */}
        {/* AXES */}
        {/* ================================================= */}

        <div>

          <h3
            className="
              text-base
              font-semibold
              text-gray-900
            "
          >
            Research axes
          </h3>

          <div
            className="
              mt-4
              space-y-4
            "
          >

            {plan.axes.map(
              (
                axis,
                index,
              ) => (

                <article
                  key={axis.axis_id}
                  className="
                    rounded-lg
                    border
                    border-gray-200
                    p-5
                  "
                >

                  <div
                    className="
                      flex
                      flex-wrap
                      items-start
                      justify-between
                      gap-3
                    "
                  >

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
                        Axis {index + 1}
                        {" · "}
                        {
                          axis.axis_type
                            .replaceAll(
                              "_",
                              " ",
                            )
                        }
                      </p>

                      <h4
                        className="
                          mt-1
                          font-semibold
                          text-gray-900
                        "
                      >
                        {axis.label}
                      </h4>

                    </div>

                  </div>

                  <p
                    className="
                      mt-2
                      text-sm
                      leading-6
                      text-gray-700
                    "
                  >
                    {axis.objective}
                  </p>

                  {axis.search_terms.length > 0 && (

                    <div
                      className="
                        mt-4
                        flex
                        flex-wrap
                        gap-2
                      "
                    >

                      {axis.search_terms.map(
                        term => (

                          <span
                            key={term}
                            className="
                              rounded-full
                              bg-gray-100
                              px-2.5
                              py-1
                              text-xs
                              text-gray-700
                            "
                          >
                            {term}
                          </span>

                        ),
                      )}

                    </div>

                  )}

                </article>

              ),
            )}

            {plan.axes.length === 0 && (

              <p
                className="
                  rounded-lg
                  border
                  border-dashed
                  border-gray-300
                  px-4
                  py-6
                  text-center
                  text-sm
                  text-gray-500
                "
              >
                The research axes are still being defined.
              </p>

            )}

          </div>

        </div>

        {/* ================================================= */}
        {/* TERMS */}
        {/* ================================================= */}

        <div>

          <h3
            className="
              text-base
              font-semibold
              text-gray-900
            "
          >
            Retrieval strategy
          </h3>

          <div
            className="
              mt-4
              grid
              grid-cols-1
              gap-6
              lg:grid-cols-2
            "
          >

            <ListBlock
              title="Search terms"
              values={plan.search_terms}
            />

            <ListBlock
              title="Related angles"
              values={plan.related_angles}
            />

          </div>

        </div>

        {/* ================================================= */}
        {/* CAUTIONS */}
        {/* ================================================= */}

        <div
          className="
            grid
            grid-cols-1
            gap-6
            lg:grid-cols-2
          "
        >

          <ListBlock
            title="Assumptions"
            values={plan.assumptions}
          />

          <ListBlock
            title="Editorial cautions"
            values={plan.editorial_cautions}
          />

          <ListBlock
            title="Exclusions"
            values={plan.exclusions}
          />

          <ListBlock
            title="Missing information"
            values={plan.missing_information}
          />

        </div>

        {/* ================================================= */}
        {/* ACTION */}
        {/* ================================================= */}

        <div
          className="
            flex
            flex-wrap
            items-center
            justify-between
            gap-4
            border-t
            border-gray-100
            pt-5
          "
        >

          <p
            className="
              max-w-2xl
              text-sm
              leading-6
              text-gray-500
            "
          >
            Validation will use this plan to build one
            documentary corpus. You will still review and
            edit the proposed contents before generating
            the report.
          </p>

          <button
            type="button"
            onClick={onValidate}
            disabled={!canValidate}
            className="
              rounded-lg
              bg-ratecard-blue
              px-5
              py-2.5
              text-sm
              font-semibold
              text-white
              transition
              hover:opacity-90
              disabled:cursor-not-allowed
              disabled:opacity-50
            "
          >
            {
              validating
                ? "Starting research…"
                : "Validate plan and search"
            }
          </button>

        </div>

      </div>

    </section>

  );

}
