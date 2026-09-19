"use client";

import {
  useEffect,
  useState,
} from "react";

import {
  api,
} from "@/lib/api";

import Link from "next/link";

import {
  useTouchResearch,
} from "@/hooks/useTouchResearch";

import TouchCandidateList from "@/components/admin/touch/TouchCandidateList";
import TouchNotebookBuilder from "@/components/admin/touch/TouchNotebookBuilder";
import TouchOutputChoice from "@/components/admin/touch/TouchOutputChoice";
import TouchResearchCoverage from "@/components/admin/touch/TouchResearchCoverage";
import TouchResearchForm from "@/components/admin/touch/TouchResearchForm";
import TouchSelectedCorpus from "@/components/admin/touch/TouchSelectedCorpus";
import TouchWorkflowSteps from "@/components/admin/touch/TouchWorkflowSteps";

import type {
  TouchWorkflowStep,
} from "@/components/admin/touch/TouchWorkflowSteps";

import type {
  SelectOption,
} from "@/components/ui/SearchableMultiSelect";

import type {
  TouchBriefStructure,
  TouchCorpusNotebook,
  TouchEntityReference,
  TouchEntityType,
} from "@/types/touch";


/* =========================================================
   NORMALIZE OPTIONS
========================================================= */

function normalizeOptions(
  values: unknown,
  idFields: string[],
  labelFields: string[],
): SelectOption[] {

  if (!Array.isArray(values)) {
    return [];
  }

  const options:
    SelectOption[] = [];

  const seenIds =
    new Set<string>();

  for (const value of values) {

    if (
      !value
      || typeof value !== "object"
    ) {
      continue;
    }

    const record =
      value as Record<
        string,
        unknown
      >;

    let id = "";

    for (const field of idFields) {

      const candidate =
        record[field];

      if (
        typeof candidate === "string"
        && candidate.trim()
      ) {

        id = candidate.trim();
        break;

      }

    }

    let label = "";

    for (const field of labelFields) {

      const candidate =
        record[field];

      if (
        typeof candidate === "string"
        && candidate.trim()
      ) {

        label = candidate.trim();
        break;

      }

    }

    if (
      !id
      || !label
      || seenIds.has(id)
    ) {
      continue;
    }

    seenIds.add(
      id,
    );

    options.push({
      id,
      label,
    });

  }

  return options.sort(
    (
      left,
      right,
    ) =>
      left.label.localeCompare(
        right.label,
        undefined,
        {
          sensitivity: "base",
        },
      ),
  );

}


/* =========================================================
   BUILD ENTITY REFERENCES
========================================================= */

function buildEntityReferences(
  type: TouchEntityType,
  values: SelectOption[],
): TouchEntityReference[] {

  return values.map(
    value => ({

      entity_type:
        type,

      entity_id:
        value.id,

      entity_label:
        value.label,

    }),
  );

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
   BUILD EXCLUSIVE PERIOD END
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
   PAGE
========================================================= */

export default function TouchPage() {

  /* =======================================================
     WORKFLOW
  ======================================================= */

  const [
    currentStep,
    setCurrentStep,
  ] = useState<TouchWorkflowStep>(
    "RESEARCH",
  );

  const [
    notebook,
    setNotebook,
  ] = useState<TouchCorpusNotebook | null>(
    null,
  );

  const [
    reportId,
    setReportId,
  ] = useState<string | null>(
    null,
  );

  const [
    brief,
    setBrief,
  ] = useState<TouchBriefStructure | null>(
    null,
  );

  /* =======================================================
     FORM
  ======================================================= */

  const [
    query,
    setQuery,
  ] = useState("");

  const [
    reportLanguage,
    setReportLanguage,
  ] = useState<"fr" | "en">(
    "fr",
  );

  const [
    periodStart,
    setPeriodStart,
  ] = useState("");

  const [
    periodEnd,
    setPeriodEnd,
  ] = useState("");

  const [
    selectedCompanies,
    setSelectedCompanies,
  ] = useState<SelectOption[]>([]);

  const [
    selectedSolutions,
    setSelectedSolutions,
  ] = useState<SelectOption[]>([]);

  const [
    selectedTopics,
    setSelectedTopics,
  ] = useState<SelectOption[]>([]);

  /* =======================================================
     LOOKUPS
  ======================================================= */

  const [
    companyOptions,
    setCompanyOptions,
  ] = useState<SelectOption[]>([]);

  const [
    solutionOptions,
    setSolutionOptions,
  ] = useState<SelectOption[]>([]);

  const [
    topicOptions,
    setTopicOptions,
  ] = useState<SelectOption[]>([]);

  const [
    lookupsLoading,
    setLookupsLoading,
  ] = useState(true);

  /* =======================================================
     RESEARCH
  ======================================================= */

  const {
    loading,
    error,
    backendErrors,

    interpretation,

    candidates,

    decisionsByContentId,

    consolidation,

    conversationHistory,

    selectedContentIds,
    selectedCandidates,

    dismissedContentIds,

    runSearch,

    toggleContent,
    unselectContent,
    dismissContent,
    restoreContent,

    resetResearch,
  } = useTouchResearch();

  const researchReady = Boolean(
    interpretation
    || conversationHistory.length > 0
    || candidates.length > 0,
  );

  const corpusReady =
    selectedContentIds.length > 0;

  const notebookReady =
    notebook !== null;

  /* =======================================================
     LOAD LOOKUPS
  ======================================================= */

  useEffect(() => {

    async function loadLookups() {

      try {

        setLookupsLoading(
          true,
        );

        const [
          companiesResponse,
          solutionsResponse,
          topicsResponse,
        ] = await Promise.all([

          api.get(
            "/company/list",
          ),

          api.get(
            "/solution/list",
          ),

          api.get(
            "/topic/list",
          ),

        ]);

        setCompanyOptions(
          normalizeOptions(

            companiesResponse
              .companies
              ?? [],

            [
              "id",
              "id_company",
              "ID_COMPANY",
            ],

            [
              "label",
              "name",
              "canonical_label",
              "NAME",
            ],

          ),
        );

        setSolutionOptions(
          normalizeOptions(

            solutionsResponse
              .solutions
              ?? [],

            [
              "id",
              "id_solution",
              "ID_SOLUTION",
            ],

            [
              "label",
              "name",
              "canonical_label",
              "NAME",
            ],

          ),
        );

        setTopicOptions(
          normalizeOptions(

            topicsResponse
              .topics
              ?? [],

            [
              "id",
              "id_topic",
              "ID_TOPIC",
            ],

            [
              "label",
              "name",
              "canonical_label",
              "NAME",
            ],

          ),
        );

      } catch (caughtError) {

        console.error(
          "Unable to load Touch lookups",
          caughtError,
        );

      } finally {

        setLookupsLoading(
          false,
        );

      }

    }

    loadLookups();

  }, []);

  /* =======================================================
     SEARCH
  ======================================================= */

  async function handleSearch() {

    const cleanedQuery =
      query.trim();

    if (
      !cleanedQuery
      || loading
    ) {
      return;
    }

    await runSearch({

      query:
        cleanedQuery,

      outputLanguage:
        reportLanguage,

      periodStart:
        buildPeriodStart(
          periodStart
        ),

      periodEnd:
        buildPeriodEnd(
          periodEnd
        ),

      companies:
        buildEntityReferences(
          "company",
          selectedCompanies,
        ),

      solutions:
        buildEntityReferences(
          "solution",
          selectedSolutions,
        ),

      topics:
        buildEntityReferences(
          "topic",
          selectedTopics,
        ),

    });

    setQuery("");

  }

  /* =======================================================
     INVALIDATE GENERATED OUTPUTS
  ======================================================= */

  function invalidateGeneratedOutputs() {

    setNotebook(
      null,
    );

    setReportId(
      null,
    );

    setBrief(
      null,
    );

  }

  /* =======================================================
     CORPUS ACTIONS
  ======================================================= */

  function handleToggleContent(
    contentId: string,
  ) {

    toggleContent(
      contentId,
    );

    invalidateGeneratedOutputs();

  }


  function handleUnselectContent(
    contentId: string,
  ) {

    unselectContent(
      contentId,
    );

    invalidateGeneratedOutputs();

  }


  function handleDismissContent(
    contentId: string,
  ) {

    dismissContent(
      contentId,
    );

    invalidateGeneratedOutputs();

  }


  function handleRestoreContent(
    contentId: string,
  ) {

    restoreContent(
      contentId,
    );

  }

  /* =======================================================
     FOLLOW-UP
  ======================================================= */

  function handleFollowUp(
    followUp: string,
  ) {

    setQuery(
      followUp,
    );

    setCurrentStep(
      "RESEARCH",
    );

  }

  /* =======================================================
     RESET
  ======================================================= */

  function handleReset() {

    resetResearch();

    setQuery("");

    setPeriodStart("");

    setPeriodEnd("");

    setSelectedCompanies([]);

    setSelectedSolutions([]);

    setSelectedTopics([]);

    setNotebook(
      null,
    );

    setBrief(
      null,
    );

    setCurrentStep(
      "RESEARCH",
    );

  }

  /* =======================================================
     RENDER
  ======================================================= */

  return (

    <div className="space-y-8">

      {/* ================================================= */}
      {/* HEADER */}
      {/* ================================================= */}

      <div>

        <h1
          className="
            text-3xl
            font-semibold
            text-gray-900
          "
        >
          GetCurator Touch
        </h1>

        <p className="mt-1 text-gray-500">
          Research a subject, build a reliable corpus
          and transform it into a structured evidence
          notebook.
        </p>

        <Link
          href="/admin/touch/reports"
          className="
            mt-3
            inline-block
            text-sm
            font-medium
            text-ratecard-blue
            hover:underline
          "
        >
          View saved reports
        </Link>

      </div>

      {/* ================================================= */}
      {/* WORKFLOW */}
      {/* ================================================= */}

      <TouchWorkflowSteps
        currentStep={currentStep}
        researchReady={researchReady}
        corpusReady={corpusReady}
        notebookReady={notebookReady}
        onStepChange={setCurrentStep}
      />

      {/* ================================================= */}
      {/* STEP 1 — RESEARCH */}
      {/* ================================================= */}

      {currentStep === "RESEARCH" && (

        <div className="space-y-6">

          <div
            className="
              rounded-xl
              border
              border-gray-200
              bg-white
              p-4
            "
          >

            <label
              htmlFor="touch-report-language"
              className="
                block
                text-sm
                font-medium
                text-gray-900
              "
            >
              Report language
            </label>

            <p className="mt-1 text-xs text-gray-500">
              Choose before starting the research.
              Reset the research to change it later.
            </p>

            <select
              id="touch-report-language"
              value={reportLanguage}
              onChange={event =>
                setReportLanguage(
                  event.target.value as "fr" | "en",
                )
              }
              disabled={
                loading
                || researchReady
                || corpusReady
              }
              className="
                mt-3
                rounded-lg
                border
                border-gray-300
                bg-white
                px-3
                py-2
                text-sm
                text-gray-900
                disabled:opacity-50
              "
            >
              <option value="fr">Français</option>
              <option value="en">English</option>
            </select>

          </div>

          <TouchResearchForm
            query={query}
            onQueryChange={
              setQuery
            }

            companyOptions={
              companyOptions
            }
            solutionOptions={
              solutionOptions
            }
            topicOptions={
              topicOptions
            }

            selectedCompanies={
              selectedCompanies
            }
            selectedSolutions={
              selectedSolutions
            }
            selectedTopics={
              selectedTopics
            }

            onCompaniesChange={
              setSelectedCompanies
            }
            onSolutionsChange={
              setSelectedSolutions
            }
            onTopicsChange={
              setSelectedTopics
            }

            periodStart={
              periodStart
            }
            periodEnd={
              periodEnd
            }

            onPeriodStartChange={
              setPeriodStart
            }
            onPeriodEndChange={
              setPeriodEnd
            }

            loading={
              loading
            }

            hasResearch={
              conversationHistory.length > 0
            }

            onSubmit={
              handleSearch
            }

            onReset={
              handleReset
            }
          />

          {lookupsLoading && (

            <p className="text-sm text-gray-500">
              Loading companies, solutions and topics…
            </p>

          )}

          {interpretation && (

            <section
              className="
                rounded-xl
                border
                border-blue-100
                bg-blue-50
                px-5
                py-4
              "
            >

              <p
                className="
                  text-xs
                  font-medium
                  uppercase
                  tracking-wide
                  text-blue-600
                "
              >
                Research interpretation
              </p>

              <h2
                className="
                  mt-1
                  text-lg
                  font-semibold
                  text-gray-900
                "
              >
                {interpretation.subject}
              </h2>

              <p
                className="
                  mt-1
                  text-sm
                  leading-6
                  text-gray-700
                "
              >
                {
                  interpretation
                    .response_message
                }
              </p>

              {(
                interpretation
                  .search_terms
                  .length > 0
              ) && (

                <div
                  className="
                    mt-3
                    flex
                    flex-wrap
                    gap-2
                  "
                >

                  {
                    interpretation
                      .search_terms
                      .map(
                        term => (

                          <span
                            key={term}
                            className="
                              rounded-full
                              border
                              border-blue-200
                              bg-white
                              px-2.5
                              py-1
                              text-xs
                              text-blue-700
                            "
                          >
                            {term}
                          </span>

                        ),
                      )
                  }

                </div>

              )}

            </section>

          )}

          {error && (

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
              {error}
            </div>

          )}

          {backendErrors.length > 0 && (

            <div
              className="
                rounded-lg
                border
                border-amber-200
                bg-amber-50
                px-4
                py-3
              "
            >

              <p
                className="
                  text-sm
                  font-medium
                  text-amber-800
                "
              >
                The research completed with warnings.
              </p>

              <ul
                className="
                  mt-2
                  space-y-1
                  text-sm
                  text-amber-700
                "
              >

                {backendErrors.map(
                  (
                    backendError,
                    index,
                  ) => (

                    <li
                      key={
                        `${backendError}-${index}`
                      }
                    >
                      {backendError}
                    </li>

                  ),
                )}

              </ul>

            </div>

          )}

          <TouchResearchCoverage
            consolidation={
              consolidation
            }
            onFollowUp={
              handleFollowUp
            }
          />

          {researchReady && (

            <div className="flex justify-end">

              <button
                type="button"
                onClick={() =>
                  setCurrentStep(
                    "CORPUS",
                  )
                }
                className="
                  rounded-lg
                  bg-ratecard-blue
                  px-4
                  py-2.5
                  text-sm
                  font-semibold
                  text-white
                "
              >
                Review proposed corpus
              </button>

            </div>

          )}

        </div>

      )}

      {/* ================================================= */}
      {/* STEP 2 — CORPUS */}
      {/* ================================================= */}

      {currentStep === "CORPUS" && (

        <div className="space-y-6">

          <div
            className="
              flex
              flex-wrap
              items-center
              justify-between
              gap-4
            "
          >

            <div>

              <h2 className="text-xl font-semibold text-gray-900">
                Editorial corpus
              </h2>

              <p className="mt-1 text-sm text-gray-500">
                Review the proposed contents and retain all
                sources that contribute useful evidence.
              </p>

            </div>

            <button
              type="button"
              onClick={() =>
                setCurrentStep(
                  "RESEARCH",
                )
              }
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
              "
            >
              Refine research
            </button>

          </div>

          <div
            className="
              grid
              grid-cols-1
              gap-6
              xl:grid-cols-[minmax(0,1fr)_360px]
            "
          >

            <TouchCandidateList
              candidates={
                candidates
              }
              decisionsByContentId={
                decisionsByContentId
              }
              selectedContentIds={
                selectedContentIds
              }
              dismissedContentIds={
                dismissedContentIds
              }
              onToggleContent={
                handleToggleContent
              }
              onDismissContent={
                handleDismissContent
              }
              onRestoreContent={
                handleRestoreContent
              }
            />

            <TouchSelectedCorpus
              candidates={
                selectedCandidates
              }
              decisionsByContentId={
                decisionsByContentId
              }
              onRemove={
                handleUnselectContent
              }
              onValidate={() =>
                setCurrentStep(
                  "NOTEBOOK",
                )
              }
              validating={false}
            />

          </div>

        </div>

      )}

      {/* ================================================= */}
      {/* STEP 3 — NOTEBOOK */}
      {/* ================================================= */}

      {currentStep === "NOTEBOOK" && (

        <TouchNotebookBuilder
          subject={
            interpretation?.subject
            ?? ""
          }
          objective={
            interpretation?.objective
            ?? ""
          }
          selectedContentIds={
            selectedContentIds
          }
          decisionsByContentId={
            decisionsByContentId
          }
          notebook={
            notebook
          }
          onNotebookChange={
            setNotebook
          }
          reportId={
            reportId
          }
          onReportIdChange={
            setReportId
          }
          onContinue={() =>
            setCurrentStep(
              "OUTPUT",
            )
          }
          outputLanguage={
            reportLanguage
          }
        />

      )}

      {/* ================================================= */}
      {/* STEP 4 — OUTPUT */}
      {/* ================================================= */}

      {(
        currentStep === "OUTPUT"
        && notebook
      ) && (

        <TouchOutputChoice
          notebook={
            notebook
          }
          outputLanguage={
            reportLanguage
          }
          sources={
            selectedCandidates
          }
          brief={
            brief
          }
          onBriefChange={
            setBrief
          }
        />

      )}
    </div>

  );

}
