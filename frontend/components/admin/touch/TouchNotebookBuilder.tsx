"use client";

import {
  useMemo,
  useRef,
  useState,
} from "react";

import {
  buildTouchNotebook,
  saveTouchReport,
} from "@/lib/touch";

import type {
  TouchContentDecision,
  TouchCorpusNotebook,
  TouchNotebookContribution,
  TouchNotebookReportDesign,
  TouchNotebookRequest,
} from "@/types/touch";

import TouchNotebookPreview from "@/components/admin/touch/TouchNotebookPreview";


/* =========================================================
   PROPS
========================================================= */

type Props = {
  subject: string;
  objective: string;
  reportDesign:
    TouchNotebookReportDesign;

  selectedContentIds: string[];

  decisionsByContentId: Map<
    string,
    TouchContentDecision
  >;

  notebook:
    TouchCorpusNotebook | null;

  onNotebookChange: (
    notebook: TouchCorpusNotebook | null
  ) => void;

  onContinue?: () => void;
  reportId: string | null;

  onReportIdChange: (
    reportId: string | null
  ) => void;

  outputLanguage?: string;
};


/* =========================================================
   UNIQUE STATEMENTS
========================================================= */

function uniqueStatements(
  values: string[],
): string[] {

  const statements: string[] = [];

  const seenStatements =
    new Set<string>();

  for (const value of values) {

    if (
      typeof value !== "string"
    ) {
      continue;
    }

    const statement =
      value.trim();

    if (
      !statement
      || seenStatements.has(
        statement,
      )
    ) {
      continue;
    }

    seenStatements.add(
      statement,
    );

    statements.push(
      statement,
    );

  }

  return statements;

}

/* =========================================================
   COPY REPORT DESIGN
========================================================= */

function copyReportDesign(
  reportDesign: TouchNotebookReportDesign,
): TouchNotebookReportDesign {

  return {
    ...reportDesign,

    geographies:
      [...reportDesign.geographies],

    axes:
      reportDesign.axes.map(
        axis => ({
          ...axis,

          search_terms:
            [...axis.search_terms],

          related_angles:
            [...axis.related_angles],
        }),
      ),

    assumptions:
      [...reportDesign.assumptions],

    editorial_cautions:
      [...reportDesign.editorial_cautions],

    missing_information:
      [...reportDesign.missing_information],
  };

}


/* =========================================================
   COMPONENT
========================================================= */

export default function TouchNotebookBuilder({
  subject,
  objective,
  reportDesign,
  selectedContentIds,
  decisionsByContentId,
  notebook,
  onNotebookChange,
  reportId,
  onReportIdChange,
  onContinue,
  outputLanguage = "fr",
}: Props) {

  const [
    loading,
    setLoading,
  ] = useState(false);

  const [
    error,
    setError,
  ] = useState<string | null>(
    null,
  );

  const [
    sourceCount,
    setSourceCount,
  ] = useState(0);

  const lastRequestRef =
    useRef<TouchNotebookRequest | null>(null);

  const [
    persistenceError,
    setPersistenceError,
  ] = useState<string | null>(null);

  const [
    savingReport,
    setSavingReport,
  ] = useState(false);

  /* =======================================================
     CONTRIBUTIONS
  ======================================================= */

  const contributions =
    useMemo<
      TouchNotebookContribution[]
    >(
      () =>
        selectedContentIds.map(
          contentId => {

            const decision =
              decisionsByContentId.get(
                contentId,
              );

            return {
              content_id:
                contentId,

              statements:
                uniqueStatements(
                  decision
                    ?.key_contributions
                  ?? [],
                ),
            };

          },
        ),
      [
        decisionsByContentId,
        selectedContentIds,
      ],
    );

  const contributionCount =
    useMemo(
      () =>
        contributions.reduce(
          (
            total,
            contribution,
          ) =>
            total
            + contribution
                .statements
                .length,
          0,
        ),
      [
        contributions,
      ],
    );

  const missingContributionIds =
    useMemo(
      () =>
        contributions
          .filter(
            contribution =>
              contribution
                .statements
                .length === 0,
          )
          .map(
            contribution =>
              contribution.content_id,
          ),
      [
        contributions,
      ],
    );

  /* =======================================================
     BUILD NOTEBOOK
  ======================================================= */

  async function handleBuildNotebook() {

    if (
      loading
      || selectedContentIds.length === 0
    ) {
      return;
    }

    const normalizedSubject =
      subject.trim();

    if (!normalizedSubject) {

      setError(
        "A research subject is required.",
      );

      return;

    }

    if (
      missingContributionIds.length > 0
    ) {

      setError(
        "Some selected contents do not contain "
        + "editorial contributions: "
        + missingContributionIds.join(
          ", ",
        ),
      );

      return;

    }

    if (contributionCount === 0) {

      setError(
        "The selected corpus does not contain "
        + "any editorial contribution.",
      );

      return;

    }

    const notebookRequest:
      TouchNotebookRequest = {

        report_id:
          reportId,

        subject:
          normalizedSubject,

        objective:
          objective.trim(),

        content_ids:
          [...selectedContentIds],

        contributions:
          contributions.map(
            contribution => ({
              content_id:
                contribution.content_id,

              statements:
                [...contribution.statements],
            }),
          ),

        output_language:
          outputLanguage,

        report_design:
          copyReportDesign(
            reportDesign,
          ),
      };

    try {

      setLoading(
        true,
      );

      setError(
        null,
      );

      setPersistenceError(
        null,
      );

      lastRequestRef.current =
        notebookRequest;

      const outcome =
        await buildTouchNotebook(
          notebookRequest,
        );

      if (
        outcome.status !== "GENERATED"
        || !outcome.notebook
      ) {

        throw new Error(
          outcome.error
          || "Unable to build the editorial notebook.",
        );

      }

      onNotebookChange(
        outcome.notebook,
      );

      setSourceCount(
        outcome.source_count,
      );

      if (outcome.report_id) {

        onReportIdChange(
          outcome.report_id,
        );

        lastRequestRef.current = {
          ...notebookRequest,

          report_id:
            outcome.report_id,
        };

      }

      setPersistenceError(
        outcome.report_id
          ? null
          : (
              outcome.persistence_error
              || "The notebook is ready, but the report "
                 + "could not be saved."
            ),
      );

    } catch (exception) {

      console.error(
        "Touch notebook error",
        exception,
      );

      onNotebookChange(
        null,
      );

      setSourceCount(
        0,
      );

      lastRequestRef.current =
        null;

      setPersistenceError(
        null,
      );

      setError(
        exception instanceof Error
          ? exception.message
          : "Unable to build the editorial notebook.",
      );

      // Do not reset reportId here.
      // An unsuccessful rebuild must not lose the identity
      // of the existing saved report.

    } finally {

      setLoading(
        false,
      );

    }

  }


  /* =======================================================
     RETRY REPORT SAVE
  ======================================================= */

  async function handleRetrySave() {

    const request =
      lastRequestRef.current;

    if (
      savingReport
      || !request
      || !notebook
    ) {
      return;
    }

    try {

      setSavingReport(
        true,
      );

      setPersistenceError(
        null,
      );

      const requestToSave:
        TouchNotebookRequest = {

        ...request,

        report_id:
          reportId,

      };

      const savedReportId =
        await saveTouchReport(
          requestToSave,
          notebook,
        );

      onReportIdChange(
        savedReportId,
      );

      lastRequestRef.current = {
        ...requestToSave,

        report_id:
          savedReportId,
      };

    } catch (exception) {

      setPersistenceError(
        exception instanceof Error
          ? exception.message
          : "Unable to save the report.",
      );

    } finally {

      setSavingReport(
        false,
      );

    }

  }
  /* =======================================================
     EMPTY CORPUS
  ======================================================= */

  if (
    selectedContentIds.length === 0
  ) {

    return (

      <div
        className="
          rounded-xl
          border
          border-dashed
          border-gray-300
          bg-white
          px-6
          py-10
          text-center
        "
      >

        <p className="text-sm font-medium text-gray-700">
          The editorial corpus is empty
        </p>

        <p className="mt-1 text-sm text-gray-500">
          Return to the corpus step and select contents
          before building the notebook.
        </p>

      </div>

    );

  }

   /* =======================================================
     RENDER
  ======================================================= */

  return (

    <section className="space-y-6">

      {/* ACTION */}

      <div
        className="
          rounded-xl
          border
          border-gray-200
          bg-white
          p-5
        "
      >

        <div
          className="
            flex
            flex-wrap
            items-center
            justify-between
            gap-4
          "
        >

            <div
              className="
                mt-3
                flex
                flex-wrap
                gap-2
              "
            >

              <span
                className="
                  rounded-full
                  bg-blue-50
                  px-2.5
                  py-1
                  text-xs
                  font-medium
                  text-blue-700
                "
              >
                {
                  reportDesign
                    .report_archetype
                    .replaceAll(
                      "_",
                      " ",
                    )
                }
              </span>

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
                {
                  reportDesign
                    .organization_mode
                    .replaceAll(
                      "_",
                      " ",
                    )
                }
              </span>

              {(
                reportDesign.time_granularity
                !== "AUTO"
              ) && (

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
                  {
                    reportDesign
                      .time_granularity
                  }
                </span>

              )}

            </div>

          </div>

          <button
            type="button"
            onClick={handleBuildNotebook}
            disabled={
              loading
              || !subject.trim()
              || contributionCount === 0
              || missingContributionIds.length > 0
            }
            className="
              rounded-lg
              bg-ratecard-blue
              px-4
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
              loading
                ? "Building notebook…"
                : notebook
                  ? "Rebuild notebook"
                  : "Build editorial notebook"
            }
          </button>

        {missingContributionIds.length > 0 && (

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

            <p className="text-sm font-medium text-amber-800">
              Contributions are missing
            </p>

            <p className="mt-1 text-sm text-amber-700">
              Some selected contents have no editorial
              contribution and cannot be added to the
              notebook.
            </p>

          </div>

        )}

        {loading && (

          <div
            className="
              mt-4
              rounded-lg
              border
              border-blue-100
              bg-blue-50
              p-4
            "
          >

            <p className="text-sm font-medium text-blue-800">
              Organising editorial contributions…
            </p>

            <p className="mt-1 text-sm text-blue-700">
              Duplicate contributions are consolidated
              before the documentary plan is constructed.
            </p>

          </div>

        )}

        {error && (

          <div
            className="
              mt-4
              rounded-lg
              border
              border-red-200
              bg-red-50
              p-4
            "
          >

            <p className="text-sm font-medium text-red-800">
              Notebook generation failed
            </p>

            <p className="mt-1 text-sm text-red-700">
              {error}
            </p>

          </div>

        )}

        {notebook && !loading && (

          <div
            className="
              mt-4
              flex
              flex-wrap
              items-center
              justify-between
              gap-4
              rounded-lg
              border
              border-emerald-200
              bg-emerald-50
              p-4
            "
          >

            <div>

              <p className="text-sm font-medium text-emerald-800">
                Editorial notebook ready
              </p>

              <p className="mt-1 text-sm text-emerald-700">

                {sourceCount || selectedContentIds.length}
                {" "}
                sources and
                {" "}
                {contributionCount}
                {" "}
                contributions consolidated into
                {" "}
                {notebook.notes.length}
                {" "}
                evidence notes.

              </p>

              {reportId && (

                <p className="mt-1 text-sm text-emerald-700">
                  Report saved. You can reopen it later.
                </p>

              )}

            </div>

            {onContinue && (

              <button
                type="button"
                onClick={onContinue}
                className="
                  rounded-lg
                  bg-emerald-700
                  px-4
                  py-2
                  text-sm
                  font-semibold
                  text-white
                  transition
                  hover:bg-emerald-800
                "
              >
                Continue to output
              </button>

            )}

          </div>

        )}

        {notebook && !loading && persistenceError && (

          <div
            className="
              mt-4
              flex
              flex-wrap
              items-center
              justify-between
              gap-4
              rounded-lg
              border
              border-amber-200
              bg-amber-50
              p-4
            "
          >

            <div>

              <p className="text-sm font-medium text-amber-800">
                Notebook ready, report not saved
              </p>

              <p className="mt-1 text-sm text-amber-700">
                {persistenceError}
              </p>

            </div>

            <button
              type="button"
              onClick={handleRetrySave}
              disabled={savingReport}
              className="
                rounded-lg
                bg-amber-700
                px-4
                py-2
                text-sm
                font-semibold
                text-white
                transition
                hover:bg-amber-800
                disabled:cursor-not-allowed
                disabled:opacity-50
              "
            >
              {
                savingReport
                  ? "Saving…"
                  : "Retry saving"
              }
            </button>

          </div>

        )}

      </div>

      {/* NOTEBOOK PREVIEW */}

      {notebook && (

        <TouchNotebookPreview
          notebook={notebook}
          sourceContentIds={
            selectedContentIds
          }
        />

      )}

    </section>

  );

}
