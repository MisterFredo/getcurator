"use client";

import {
  useEffect,
  useState,
} from "react";

import Link from "next/link";

import {
  deleteTouchReport,
  getTouchReport,
  listTouchReports,
} from "@/lib/touch";

import TouchOutputChoice from "@/components/admin/touch/TouchOutputChoice";

import type {
  TouchBriefStructure,
  TouchContentCandidate,
  TouchSavedReport,
  TouchSavedReportSummary,
} from "@/types/touch";


/* =========================================================
   REPORT SOURCES
========================================================= */

function reportSources(
  report: TouchSavedReport,
): TouchContentCandidate[] {

  const sourcesById = new Map(
    report.sources.map(
      source => [
        source.content_id,
        source,
      ],
    ),
  );

  return report.content_ids.map(
    contentId => {

      const source =
        sourcesById.get(
          contentId,
        );

      return {
        content_id:
          contentId,

        title:
          source?.title
          || source?.original_title
          || "Untitled source",

        excerpt:
          "",

        source_title:
          source?.source_name
          || source?.original_title
          || source?.title
          || "Untitled source",

        source_url:
          source?.url
          || "",

        published_at:
          source?.published_at
          || null,

        companies:
          [],

        solutions:
          [],

        topics:
          [],

        universes:
          [],

        concepts:
          [],

        selection_sources:
          [],

        matched_entities:
          [],

        matched_terms:
          [],

        matched_angles:
          [],
      };

    },
  );

}


/* =========================================================
   PAGE
========================================================= */

export default function TouchReportsPage() {

  const [
    reports,
    setReports,
  ] = useState<
    TouchSavedReportSummary[]
  >([]);

  const [
    selectedReport,
    setSelectedReport,
  ] = useState<
    TouchSavedReport | null
  >(null);

  const [
    brief,
    setBrief,
  ] = useState<
    TouchBriefStructure | null
  >(null);

  const [
    loading,
    setLoading,
  ] = useState(
    true,
  );

  const [
    openingId,
    setOpeningId,
  ] = useState<
    string | null
  >(null);

  const [
    deletingId,
    setDeletingId,
  ] = useState<
    string | null
  >(null);

  const [
    error,
    setError,
  ] = useState<
    string | null
  >(null);


  /* =======================================================
     LOAD REPORTS
  ======================================================= */

  useEffect(() => {

    let active = true;

    async function loadReports() {

      try {

        setError(
          null,
        );

        const result =
          await listTouchReports();

        if (active) {

          setReports(
            result,
          );

        }

      } catch (exception) {

        if (active) {

          setError(
            exception instanceof Error
              ? exception.message
              : "Unable to load saved reports.",
          );

        }

      } finally {

        if (active) {

          setLoading(
            false,
          );

        }

      }

    }

    void loadReports();

    return () => {

      active = false;

    };

  }, []);


  /* =======================================================
     OPEN REPORT
  ======================================================= */

  async function handleOpen(
    reportId: string,
  ) {

    if (
      openingId
      || deletingId
    ) {

      return;

    }

    try {

      setOpeningId(
        reportId,
      );

      setError(
        null,
      );

      const report =
        await getTouchReport(
          reportId,
        );

      setBrief(
        null,
      );

      setSelectedReport(
        report,
      );

    } catch (exception) {

      setError(
        exception instanceof Error
          ? exception.message
          : "Unable to open the report.",
      );

    } finally {

      setOpeningId(
        null,
      );

    }

  }


  /* =======================================================
     DELETE REPORT
  ======================================================= */

  async function handleDelete(
    report: TouchSavedReportSummary,
  ) {

    if (
      deletingId
      || openingId
    ) {

      return;

    }

    const confirmed =
      window.confirm(
        `Delete “${report.subject}”? `
        + "This action cannot be undone.",
      );

    if (!confirmed) {

      return;

    }

    try {

      setDeletingId(
        report.report_id,
      );

      setError(
        null,
      );

      await deleteTouchReport(
        report.report_id,
      );

      setReports(
        currentReports =>
          currentReports.filter(
            currentReport =>
              currentReport.report_id
              !== report.report_id,
          ),
      );

      if (
        selectedReport?.report_id
        === report.report_id
      ) {

        setSelectedReport(
          null,
        );

        setBrief(
          null,
        );

      }

    } catch (exception) {

      setError(
        exception instanceof Error
          ? exception.message
          : "Unable to delete the report.",
      );

    } finally {

      setDeletingId(
        null,
      );

    }

  }


  /* =======================================================
     RENDER
  ======================================================= */

  return (

    <div className="space-y-8">

      <header>

        <Link
          href="/admin/touch"
          className="
            text-sm
            font-medium
            text-ratecard-blue
            hover:underline
          "
        >
          ← Back to Touch
        </Link>

        <h1
          className="
            mt-3
            text-3xl
            font-semibold
            text-gray-900
          "
        >
          Saved Touch reports
        </h1>

        <p className="mt-1 text-sm text-gray-500">
          Open or delete an existing report without
          rebuilding its notebook.
        </p>

      </header>

      {error && (

        <div
          className="
            rounded-lg
            border
            border-red-200
            bg-red-50
            p-4
            text-sm
            text-red-700
          "
        >
          {error}
        </div>

      )}

      {selectedReport ? (

        <div className="space-y-6">

          <button
            type="button"
            onClick={() => {

              setSelectedReport(
                null,
              );

              setBrief(
                null,
              );

            }}
            className="
              text-sm
              font-medium
              text-ratecard-blue
              hover:underline
            "
          >
            ← All saved reports
          </button>

          <TouchOutputChoice
            notebook={
              selectedReport.notebook
            }
            outputLanguage={
              selectedReport.output_language
            }
            sources={
              reportSources(
                selectedReport,
              )
            }
            brief={
              brief
            }
            onBriefChange={
              setBrief
            }
          />

        </div>

      ) : (

        <section className="space-y-3">

          {loading && (

            <p className="text-sm text-gray-500">
              Loading reports…
            </p>

          )}

          {!loading && reports.length === 0 && (

            <div
              className="
                rounded-xl
                border
                border-dashed
                border-gray-300
                bg-white
                px-6
                py-12
                text-center
              "
            >

              <p className="text-sm font-medium text-gray-700">
                No saved reports yet
              </p>

              <p className="mt-1 text-sm text-gray-500">
                Generated Touch reports will appear here.
              </p>

            </div>

          )}

          {reports.map(
            report => {

              const isOpening =
                openingId
                === report.report_id;

              const isDeleting =
                deletingId
                === report.report_id;

              const interactionsDisabled =
                openingId !== null
                || deletingId !== null;

              return (

                <article
                  key={
                    report.report_id
                  }
                  className="
                    flex
                    items-start
                    gap-4
                    rounded-xl
                    border
                    border-gray-200
                    bg-white
                    p-5
                    transition
                    hover:border-blue-300
                  "
                >

                  <button
                    type="button"
                    onClick={() =>
                      handleOpen(
                        report.report_id,
                      )
                    }
                    disabled={
                      interactionsDisabled
                    }
                    className="
                      min-w-0
                      flex-1
                      text-left
                      disabled:cursor-not-allowed
                      disabled:opacity-60
                    "
                  >

                    <span
                      className="
                        block
                        font-semibold
                        text-gray-900
                      "
                    >
                      {report.subject}
                    </span>

                    {report.objective && (

                      <span
                        className="
                          mt-1
                          block
                          text-sm
                          text-gray-600
                        "
                      >
                        {report.objective}
                      </span>

                    )}

                    <span
                      className="
                        mt-3
                        block
                        text-xs
                        text-gray-500
                      "
                    >
                      {report.source_count}
                      {" sources · "}
                      {new Date(
                        report.created_at,
                      ).toLocaleDateString(
                        "en-GB",
                      )}
                      {" · Version "}
                      {report.version_number}
                    </span>

                    {isOpening && (

                      <span
                        className="
                          mt-2
                          block
                          text-xs
                          font-medium
                          text-ratecard-blue
                        "
                      >
                        Opening…
                      </span>

                    )}

                  </button>

                  <button
                    type="button"
                    onClick={() => {

                      void handleDelete(
                        report,
                      );

                    }}
                    disabled={
                      interactionsDisabled
                    }
                    className="
                      shrink-0
                      rounded-lg
                      border
                      border-red-200
                      px-3
                      py-2
                      text-xs
                      font-semibold
                      text-red-700
                      transition
                      hover:border-red-300
                      hover:bg-red-50
                      disabled:cursor-not-allowed
                      disabled:opacity-50
                    "
                  >
                    {
                      isDeleting
                        ? "Deleting…"
                        : "Delete"
                    }
                  </button>

                </article>

              );

            },
          )}

        </section>

      )}

    </div>

  );

}
