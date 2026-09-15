"use client";

import {
  useEffect,
  useState,
} from "react";

import {
  api,
} from "@/lib/api";

import {
  generateTouchOnePager,
} from "@/lib/touch";

import {
  useTouchResearch,
} from "@/hooks/useTouchResearch";

import TouchCandidateList from "@/components/admin/touch/TouchCandidateList";
import TouchResearchCoverage from "@/components/admin/touch/TouchResearchCoverage";
import TouchResearchForm from "@/components/admin/touch/TouchResearchForm";
import TouchSelectedCorpus from "@/components/admin/touch/TouchSelectedCorpus";
import TouchDraftPreview from "@/components/admin/touch/TouchDraftPreview";
import TouchNotebookBuilder from "@/components/admin/touch/TouchNotebookBuilder";

import type {
  SelectOption,
} from "@/components/ui/SearchableMultiSelect";

import TouchOutputChoice from "@/components/admin/touch/TouchOutputChoice";

import type {
  TouchEntityReference,
  TouchEntityType,
  TouchGenerationOutcome,
  TouchCorpusNotebook,
  TouchBriefStructure,
  TouchCorpusNotebook,
} from "@/types/touch";

const [
  notebook,
  setNotebook,
] = useState<TouchCorpusNotebook | null>(
  null,
);

const [
  brief,
  setBrief,
] = useState<TouchBriefStructure | null>(
  null,
);


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

    seenIds.add(id);

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
     FORM
  ======================================================= */

  const [
    query,
    setQuery,
  ] = useState("");

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
     GENERATION
  ======================================================= */

  const [
    generating,
    setGenerating,
  ] = useState(false);

  const [
    generation,
    setGeneration,
  ] = useState<
    TouchGenerationOutcome | null
  >(null);

  const [
    generationError,
    setGenerationError,
  ] = useState<string | null>(
    null,
  );

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
        "fr",

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
     GENERATE ONE-PAGER
  ======================================================= */

  async function handleGenerateOnePager() {

    if (
      selectedContentIds.length === 0
      || generating
      || !interpretation
    ) {
      return;
    }

    try {

      setGenerating(
        true,
      );

      setGenerationError(
        null,
      );

      const result =
        await generateTouchOnePager({

          subject:
            interpretation.subject,

          objective:
            interpretation.objective,

          output_language:
            "fr",

          content_ids:
            selectedContentIds,

        });

      setGeneration(
        result,
      );

    } catch (caughtError) {

      console.error(
        "Touch generation error",
        caughtError,
      );

      setGenerationError(

        caughtError instanceof Error

          ? caughtError.message

          : (
              "Unable to generate "
              + "the one-pager."
            )

      );

    } finally {

      setGenerating(
        false,
      );

    }

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

    setGeneration(null);

    setGenerationError(null);

    setGenerating(false);

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
          Build an editorial corpus from the complete
          GetCurator content base.
        </p>

      </div>

      {/* ================================================= */}
      {/* FORM */}
      {/* ================================================= */}

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

      {/* ================================================= */}
      {/* LOOKUPS */}
      {/* ================================================= */}

      {lookupsLoading && (

        <p className="text-sm text-gray-500">
          Loading companies, solutions and topics…
        </p>

      )}

      {/* ================================================= */}
      {/* INTERPRETATION */}
      {/* ================================================= */}

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

      {/* ================================================= */}
      {/* RESEARCH ERROR */}
      {/* ================================================= */}

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

      {/* ================================================= */}
      {/* RESEARCH WARNINGS */}
      {/* ================================================= */}

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

      {/* ================================================= */}
      {/* COVERAGE */}
      {/* ================================================= */}

      <TouchResearchCoverage
        consolidation={
          consolidation
        }

        onFollowUp={
          setQuery
        }
      />

      {/* ================================================= */}
      {/* GENERATION ERROR */}
      {/* ================================================= */}

      {generationError && (

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
          {generationError}
        </div>

      )}

      {/* ================================================= */}
      {/* GENERATED DRAFT */}
      {/* ================================================= */}
      
      {generation?.draft && (
      
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
          notebook={notebook}
          onNotebookChange={
            setNotebook
          }
          onContinue={() =>
            setCurrentStep(
              "OUTPUT",
            )
          }
          outputLanguage="fr"
        />
      
      )}

      {/* ================================================= */}
      {/* WORK AREA */}
      {/* ================================================= */}

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
            toggleContent
          }

          onDismissContent={
            dismissContent
          }

          onRestoreContent={
            restoreContent
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
            unselectContent
          }

          onValidate={
            handleGenerateOnePager
          }

          validating={
            generating
          }
        />

      </div>

    </div>

  );

}
