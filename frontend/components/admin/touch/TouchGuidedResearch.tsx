"use client";

import {
  useMemo,
  useState,
} from "react";

import SearchableMultiSelect, {
  type SelectOption,
} from "@/components/ui/SearchableMultiSelect";

import TouchGuidedResearchPlanView from "@/components/admin/touch/TouchGuidedResearchPlan";

import type {
  TouchEntityReference,
  TouchEntityType,
  TouchGuidedEntityMention,
  TouchGuidedResearchPlan,
} from "@/types/touch";

import type {
  TouchGuidedResearchContext,
  UseTouchGuidedResearchResult,
} from "@/hooks/useTouchGuidedResearch";


/* =========================================================
   RESOLVED ENTITY GROUPS
========================================================= */

export type TouchGuidedResolvedEntityGroups = {
  companies:
    TouchEntityReference[];

  solutions:
    TouchEntityReference[];

  topics:
    TouchEntityReference[];
};


/* =========================================================
   PROPS
========================================================= */

type Props = {
  outputLanguage:
    string;

  periodStart:
    string;

  periodEnd:
    string;

  onPeriodStartChange: (
    value: string,
  ) => void;

  onPeriodEndChange: (
    value: string,
  ) => void;

  companyOptions:
    SelectOption[];

  solutionOptions:
    SelectOption[];

  topicOptions:
    SelectOption[];

  selectedCompanies:
    SelectOption[];

  selectedSolutions:
    SelectOption[];

  selectedTopics:
    SelectOption[];

  onCompaniesChange: (
    values: SelectOption[],
  ) => void;

  onSolutionsChange: (
    values: SelectOption[],
  ) => void;

  onTopicsChange: (
    values: SelectOption[],
  ) => void;

  guided:
    UseTouchGuidedResearchResult;

  onValidatePlan: (
    plan: TouchGuidedResearchPlan,
    entities: TouchGuidedResolvedEntityGroups,
  ) => void;

  validating?:
    boolean;

  onReset:
    () => void;
};


/* =========================================================
   NORMALIZE LABEL
========================================================= */

function normalizeLabel(
  value: string,
): string {

  return value
    .normalize("NFD")
    .replace(
      /[\u0300-\u036f]/g,
      "",
    )
    .trim()
    .toLocaleLowerCase();

}


/* =========================================================
   BUILD PERIOD START
========================================================= */

function buildPeriodStart(
  value: string,
): string | null {

  if (!value) {
    return null;
  }

  return `${value}T00:00:00Z`;

}


/* =========================================================
   BUILD PERIOD END
========================================================= */

function buildPeriodEnd(
  value: string,
): string | null {

  if (!value) {
    return null;
  }

  const date =
    new Date(
      `${value}T00:00:00Z`,
    );

  if (
    Number.isNaN(
      date.getTime(),
    )
  ) {
    return null;
  }

  date.setUTCDate(
    date.getUTCDate() + 1,
  );

  return date.toISOString();

}


/* =========================================================
   BUILD ENTITY REFERENCES
========================================================= */

function buildEntityReferences(
  entityType: TouchEntityType,
  values: SelectOption[],
): TouchEntityReference[] {

  return values.map(
    value => ({

      entity_type:
        entityType,

      entity_id:
        value.id,

      entity_label:
        value.label,

    }),
  );

}


/* =========================================================
   UNIQUE OPTIONS
========================================================= */

function uniqueOptions(
  values: SelectOption[],
): SelectOption[] {

  const optionsById =
    new Map<
      string,
      SelectOption
    >();

  for (const value of values) {

    optionsById.set(
      value.id,
      value,
    );

  }

  return Array.from(
    optionsById.values(),
  );

}


/* =========================================================
   UNIQUE ENTITY REFERENCES
========================================================= */

function uniqueEntityReferences(
  values: TouchEntityReference[],
): TouchEntityReference[] {

  const entitiesByKey =
    new Map<
      string,
      TouchEntityReference
    >();

  for (const value of values) {

    const key =
      `${value.entity_type}:${value.entity_id}`;

    entitiesByKey.set(
      key,
      value,
    );

  }

  return Array.from(
    entitiesByKey.values(),
  );

}


/* =========================================================
   MENTION KEY
========================================================= */

function getMentionKey(
  mention: TouchGuidedEntityMention,
): string {

  return [
    mention.entity_type,
    normalizeLabel(
      mention.entity_label,
    ),
    mention.research_role,
  ].join(":");

}


/* =========================================================
   OPTIONS FOR TYPE
========================================================= */

function getOptionsForType(
  entityType: TouchEntityType,
  companyOptions: SelectOption[],
  solutionOptions: SelectOption[],
  topicOptions: SelectOption[],
): SelectOption[] {

  if (
    entityType === "company"
  ) {
    return companyOptions;
  }

  if (
    entityType === "solution"
  ) {
    return solutionOptions;
  }

  return topicOptions;

}


/* =========================================================
   FIND EXACT OPTION
========================================================= */

function findExactOption(
  mention: TouchGuidedEntityMention,
  options: SelectOption[],
): SelectOption | null {

  const normalizedMention =
    normalizeLabel(
      mention.entity_label,
    );

  return (
    options.find(
      option =>
        normalizeLabel(
          option.label,
        ) === normalizedMention,
    )
    ?? null
  );

}


/* =========================================================
   COMPONENT
========================================================= */

export default function TouchGuidedResearch({
  outputLanguage,

  periodStart,
  periodEnd,

  onPeriodStartChange,
  onPeriodEndChange,

  companyOptions,
  solutionOptions,
  topicOptions,

  selectedCompanies,
  selectedSolutions,
  selectedTopics,

  onCompaniesChange,
  onSolutionsChange,
  onTopicsChange,

  guided,

  onValidatePlan,

  validating = false,

  onReset,
}: Props) {

  const [
    message,
    setMessage,
  ] = useState("");

  const [
    manualEntitySelections,
    setManualEntitySelections,
  ] = useState<
    Record<
      string,
      SelectOption[]
    >
  >({});


  /* =======================================================
     MENTION RESOLUTION
  ======================================================= */

  const mentionResolution =
    useMemo(() => {

      const resolved: Array<{
        mention:
          TouchGuidedEntityMention;

        option:
          SelectOption;
      }> = [];

      const unresolved:
        TouchGuidedEntityMention[] = [];

      const mentions =
        guided.plan
          ?.entity_mentions
        ?? [];

      for (const mention of mentions) {

        const options =
          getOptionsForType(

            mention.entity_type,

            companyOptions,
            solutionOptions,
            topicOptions,

          );

        const exactOption =
          findExactOption(
            mention,
            options,
          );

        const manualOption =
          manualEntitySelections[
            getMentionKey(
              mention,
            )
          ]?.[0]
          ?? null;

        const resolvedOption =
          manualOption
          ?? exactOption;

        if (resolvedOption) {

          resolved.push({
            mention,
            option:
              resolvedOption,
          });

        } else {

          unresolved.push(
            mention,
          );

        }

      }

      return {
        resolved,
        unresolved,
      };

    }, [
      companyOptions,
      guided.plan,
      manualEntitySelections,
      solutionOptions,
      topicOptions,
    ]);


  /* =======================================================
     EFFECTIVE OPTIONS
  ======================================================= */

  const effectiveOptions =
    useMemo(() => {

      const companies = [
        ...selectedCompanies,
      ];

      const solutions = [
        ...selectedSolutions,
      ];

      const topics = [
        ...selectedTopics,
      ];

      for (
        const {
          mention,
          option,
        }
        of mentionResolution.resolved
      ) {

        if (
          mention.entity_type
          === "company"
        ) {

          companies.push(
            option,
          );

        } else if (
          mention.entity_type
          === "solution"
        ) {

          solutions.push(
            option,
          );

        } else {

          topics.push(
            option,
          );

        }

      }

      return {

        companies:
          uniqueOptions(
            companies,
          ),

        solutions:
          uniqueOptions(
            solutions,
          ),

        topics:
          uniqueOptions(
            topics,
          ),

      };

    }, [
      mentionResolution.resolved,
      selectedCompanies,
      selectedSolutions,
      selectedTopics,
    ]);


  /* =======================================================
     EFFECTIVE ENTITIES
  ======================================================= */

  const effectiveEntities =
    useMemo<
      TouchGuidedResolvedEntityGroups
    >(
      () => ({

        companies:
          buildEntityReferences(
            "company",
            effectiveOptions
              .companies,
          ),

        solutions:
          buildEntityReferences(
            "solution",
            effectiveOptions
              .solutions,
          ),

        topics:
          buildEntityReferences(
            "topic",
            effectiveOptions
              .topics,
          ),

      }),
      [
        effectiveOptions,
      ],
    );


  /* =======================================================
     GUIDED CONTEXT
  ======================================================= */

  const guidedContext =
    useMemo<
      TouchGuidedResearchContext
    >(
      () => ({

        outputLanguage,

        periodStart:
          buildPeriodStart(
            periodStart,
          ),

        periodEnd:
          buildPeriodEnd(
            periodEnd,
          ),

        companies:
          effectiveEntities
            .companies,

        solutions:
          effectiveEntities
            .solutions,

        topics:
          effectiveEntities
            .topics,

      }),
      [
        effectiveEntities,
        outputLanguage,
        periodEnd,
        periodStart,
      ],
    );


  /* =======================================================
     DISPLAY PLAN
  ======================================================= */

  const displayPlan =
    useMemo<
      TouchGuidedResearchPlan | null
    >(
      () => {

        if (!guided.plan) {
          return null;
        }

        const resolvedEntities =
          uniqueEntityReferences([
            ...guided
              .plan
              .resolved_entities,

            ...effectiveEntities
              .companies,

            ...effectiveEntities
              .solutions,

            ...effectiveEntities
              .topics,
          ]);

        return {
          ...guided.plan,

          resolved_entities:
            resolvedEntities,
        };

      },
      [
        effectiveEntities,
        guided.plan,
      ],
    );


  /* =======================================================
     SUBMIT MESSAGE
  ======================================================= */

  async function handleSubmitMessage() {

    const cleanedMessage =
      message.trim();

    if (
      !cleanedMessage
      || guided.loading
    ) {
      return;
    }

    let outcome = null;

    if (!guided.started) {

      outcome =
        await guided.startInterview(
          cleanedMessage,
          guidedContext,
        );

    } else if (
      guided.phase
      === "PLAN_READY"
    ) {

      outcome =
        await guided.revisePlan(
          cleanedMessage,
          guidedContext,
        );

    } else {

      outcome =
        await guided.answerQuestion(
          cleanedMessage,
          guidedContext,
        );

    }

    if (outcome) {

      setMessage(
        "",
      );

    }

  }


  /* =======================================================
     PREPARE PLAN
  ======================================================= */

  async function handlePreparePlan() {

    if (
      guided.loading
      || !guided.started
    ) {
      return;
    }

    await guided.preparePlan(
      guidedContext,
    );

  }


  /* =======================================================
     VALIDATE PLAN
  ======================================================= */

  function handleValidatePlan() {

    if (
      !displayPlan
      || mentionResolution
          .unresolved
          .length > 0
    ) {
      return;
    }

    onValidatePlan(
      displayPlan,
      effectiveEntities,
    );

  }


  /* =======================================================
     RENDER
  ======================================================= */

  return (

    <div className="space-y-6">

      {/* ================================================= */}
      {/* INITIAL CONTEXT */}
      {/* ================================================= */}

      <section
        className="
          rounded-xl
          border
          border-gray-200
          bg-white
          p-6
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
            Guided research context
          </p>

          <h2
            className="
              mt-1
              text-lg
              font-semibold
              text-gray-900
            "
          >
            Define the initial research anchors
          </h2>

          <p
            className="
              mt-2
              text-sm
              leading-6
              text-gray-600
            "
          >
            Structured entities are reliable anchors.
            You may leave them empty when you want the
            guided interview to detect entities from
            the request.
          </p>

        </div>

        <div
          className="
            mt-5
            grid
            grid-cols-1
            gap-5
            lg:grid-cols-3
          "
        >

          <SearchableMultiSelect
            label="Companies"
            placeholder="Search companies…"
            options={companyOptions}
            values={selectedCompanies}
            onChange={onCompaniesChange}
          />

          <SearchableMultiSelect
            label="Solutions"
            placeholder="Search solutions…"
            options={solutionOptions}
            values={selectedSolutions}
            onChange={onSolutionsChange}
          />

          <SearchableMultiSelect
            label="Topics"
            placeholder="Search topics…"
            options={topicOptions}
            values={selectedTopics}
            onChange={onTopicsChange}
          />

        </div>

        <div
          className="
            mt-5
            grid
            grid-cols-1
            gap-5
            sm:grid-cols-2
            lg:max-w-2xl
          "
        >

          <div className="space-y-2">

            <label
              htmlFor="guided-period-start"
              className="
                text-sm
                font-medium
                text-gray-900
              "
            >
              From
            </label>

            <input
              id="guided-period-start"
              type="date"
              value={periodStart}
              onChange={event =>
                onPeriodStartChange(
                  event.target.value,
                )
              }
              disabled={guided.loading}
              className="
                w-full
                rounded-lg
                border
                border-gray-300
                px-3
                py-2
                text-sm
                outline-none
                focus:border-ratecard-blue
                focus:ring-2
                focus:ring-blue-100
                disabled:opacity-50
              "
            />

          </div>

          <div className="space-y-2">

            <label
              htmlFor="guided-period-end"
              className="
                text-sm
                font-medium
                text-gray-900
              "
            >
              To
            </label>

            <input
              id="guided-period-end"
              type="date"
              value={periodEnd}
              onChange={event =>
                onPeriodEndChange(
                  event.target.value,
                )
              }
              disabled={guided.loading}
              className="
                w-full
                rounded-lg
                border
                border-gray-300
                px-3
                py-2
                text-sm
                outline-none
                focus:border-ratecard-blue
                focus:ring-2
                focus:ring-blue-100
                disabled:opacity-50
              "
            />

          </div>

        </div>

      </section>

      {/* ================================================= */}
      {/* CONVERSATION */}
      {/* ================================================= */}

      {guided.conversationHistory.length > 0 && (

        <section
          className="
            rounded-xl
            border
            border-gray-200
            bg-white
            p-6
          "
        >

          <h2
            className="
              text-lg
              font-semibold
              text-gray-900
            "
          >
            Research-design interview
          </h2>

          <div
            className="
              mt-5
              space-y-4
            "
          >

            {guided.conversationHistory.map(
              (
                item,
                index,
              ) => (

                <div
                  key={
                    `${
                      item.role
                    }-${index}`
                  }
                  className={`
                    flex
                    ${
                      item.role === "user"
                        ? "justify-end"
                        : "justify-start"
                    }
                  `}
                >

                  <div
                    className={`
                      max-w-3xl
                      rounded-xl
                      px-4
                      py-3
                      text-sm
                      leading-6
                      ${
                        item.role === "user"
                          ? (
                              "bg-ratecard-blue "
                              + "text-white"
                            )
                          : (
                              "border "
                              + "border-gray-200 "
                              + "bg-gray-50 "
                              + "text-gray-700"
                            )
                      }
                    `}
                  >
                    {item.content}
                  </div>

                </div>

              ),
            )}

          </div>

          {guided.questions.length > 0 && (

            <div
              className="
                mt-5
                rounded-lg
                border
                border-blue-100
                bg-blue-50
                p-4
              "
            >

              <p
                className="
                  text-sm
                  font-medium
                  text-blue-900
                "
              >
                Questions to clarify
              </p>

              <ol
                className="
                  mt-2
                  list-decimal
                  space-y-2
                  pl-5
                  text-sm
                  leading-6
                  text-blue-800
                "
              >

                {guided.questions.map(
                  question => (

                    <li key={question}>
                      {question}
                    </li>

                  ),
                )}

              </ol>

            </div>

          )}

        </section>

      )}

      {/* ================================================= */}
      {/* ENTITY RESOLUTION */}
      {/* ================================================= */}

      {(
        guided.plan
        && guided.plan.entity_mentions.some(
          mention => {

            const options =
              getOptionsForType(

                mention.entity_type,

                companyOptions,
                solutionOptions,
                topicOptions,

              );

            return !findExactOption(
              mention,
              options,
            );

          },
        )
      ) && (

        <section
          className="
            rounded-xl
            border
            border-amber-200
            bg-amber-50
            p-6
          "
        >

          <h2
            className="
              text-lg
              font-semibold
              text-amber-900
            "
          >
            Resolve detected entities
          </h2>

          <p
            className="
              mt-1
              text-sm
              leading-6
              text-amber-700
            "
          >
            Some names detected during the interview do
            not exactly match the GetCurator entity
            catalog. Select the appropriate entity.
          </p>

          <div
            className="
              mt-5
              space-y-5
            "
          >

            {guided.plan.entity_mentions.map(
              mention => {

                const options =
                  getOptionsForType(

                    mention.entity_type,

                    companyOptions,
                    solutionOptions,
                    topicOptions,

                  );

                const exactOption =
                  findExactOption(
                    mention,
                    options,
                  );

                if (exactOption) {
                  return null;
                }

                const mentionKey =
                  getMentionKey(
                    mention,
                  );

                return (

                  <div
                    key={mentionKey}
                    className="
                      rounded-lg
                      border
                      border-amber-200
                      bg-white
                      p-4
                    "
                  >

                    <div
                      className="
                        mb-3
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
                            text-sm
                            font-medium
                            text-gray-900
                          "
                        >
                          {mention.entity_label}
                        </p>

                        <p
                          className="
                            mt-1
                            text-xs
                            text-gray-500
                          "
                        >
                          {mention.entity_type}
                          {" · "}
                          {mention.research_role}
                        </p>

                      </div>

                      <span
                        className="
                          rounded-full
                          bg-amber-100
                          px-2.5
                          py-1
                          text-xs
                          font-medium
                          text-amber-800
                        "
                      >
                        {
                          Math.round(
                            mention.confidence
                            * 100,
                          )
                        }
                        % confidence
                      </span>

                    </div>

                    <SearchableMultiSelect
                      label="Match with GetCurator entity"
                      placeholder="Search the entity catalog…"
                      options={options}
                      values={
                        manualEntitySelections[
                          mentionKey
                        ]
                        ?? []
                      }
                      onChange={values => {

                        const retainedValues =
                          values.length > 0
                            ? [
                                values[
                                  values.length - 1
                                ],
                              ]
                            : [];

                        setManualEntitySelections(
                          current => ({

                            ...current,

                            [mentionKey]:
                              retainedValues,

                          }),
                        );

                      }}
                    />

                  </div>

                );

              },
            )}

          </div>

        </section>

      )}

      {/* ================================================= */}
      {/* ERRORS */}
      {/* ================================================= */}

      {guided.error && (

        <div
          className="
            rounded-lg
            border
            border-red-200
            bg-red-50
            px-4
            py-3
            text-sm
            text-red-700
          "
        >
          {guided.error}
        </div>

      )}

      {guided.warning && (

        <div
          className="
            rounded-lg
            border
            border-amber-200
            bg-amber-50
            px-4
            py-3
            text-sm
            text-amber-700
          "
        >
          The guided assistant used a fallback:
          {" "}
          {guided.warning}
        </div>

      )}

      {/* ================================================= */}
      {/* MESSAGE FORM */}
      {/* ================================================= */}

      <section
        className="
          rounded-xl
          border
          border-gray-200
          bg-white
          p-6
        "
      >

        <label
          htmlFor="guided-research-message"
          className="
            text-sm
            font-medium
            text-gray-900
          "
        >
          {
            !guided.started
              ? "Describe the research you want to design"
              : (
                  guided.phase === "PLAN_READY"
                    ? "Request a revision"
                    : "Answer the questions"
                )
          }
        </label>

        <textarea
          id="guided-research-message"
          value={message}
          onChange={event =>
            setMessage(
              event.target.value,
            )
          }
          rows={5}
          disabled={guided.loading}
          placeholder={
            !guided.started
              ? (
                  "Example: Sephora innovates in digital "
                  + "and e-commerce. I want to understand "
                  + "whether these practices could be "
                  + "relevant to a wine and spirits brand."
                )
              : (
                  guided.phase === "PLAN_READY"
                    ? (
                        "Explain what should be changed "
                        + "in the proposed plan…"
                      )
                    : (
                        "Provide detailed answers to the "
                        + "questions above…"
                      )
                )
          }
          className="
            mt-2
            w-full
            resize-y
            rounded-lg
            border
            border-gray-300
            px-4
            py-3
            text-sm
            text-gray-900
            outline-none
            focus:border-ratecard-blue
            focus:ring-2
            focus:ring-blue-100
            disabled:opacity-50
          "
        />

        <div
          className="
            mt-5
            flex
            flex-wrap
            items-center
            justify-between
            gap-3
            border-t
            border-gray-100
            pt-5
          "
        >

          <div
            className="
              flex
              flex-wrap
              items-center
              gap-3
            "
          >

            <button
              type="button"
              onClick={onReset}
              disabled={guided.loading}
              className="
                px-3
                py-2
                text-sm
                text-gray-600
                hover:text-gray-900
                disabled:opacity-50
              "
            >
              Reset guided research
            </button>

            {(
              guided.started
              && guided.phase !== "PLAN_READY"
            ) && (

              <button
                type="button"
                onClick={handlePreparePlan}
                disabled={guided.loading}
                className="
                  rounded-lg
                  border
                  border-gray-300
                  bg-white
                  px-4
                  py-2
                  text-sm
                  font-medium
                  text-gray-700
                  hover:bg-gray-50
                  disabled:opacity-50
                "
              >
                Prepare plan now
              </button>

            )}

          </div>

          <button
            type="button"
            onClick={handleSubmitMessage}
            disabled={
              guided.loading
              || !message.trim()
            }
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
              guided.loading
                ? "Working…"
                : (
                    !guided.started
                      ? "Start guided interview"
                      : (
                          guided.phase
                          === "PLAN_READY"
                            ? "Revise plan"
                            : "Send answer"
                        )
                  )
            }
          </button>

        </div>

      </section>

      {/* ================================================= */}
      {/* PLAN */}
      {/* ================================================= */}

      {displayPlan && (

        <TouchGuidedResearchPlanView
          plan={displayPlan}
          unresolvedEntityMentions={
            mentionResolution.unresolved
          }
          onValidate={
            handleValidatePlan
          }
          validating={
            validating
          }
        />

      )}

    </div>

  );

}
