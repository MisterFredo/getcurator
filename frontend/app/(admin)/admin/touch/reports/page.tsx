"use client";

import {
  useEffect,
  useState,
} from "react";

import Link from "next/link";

import {
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
        sourcesById.get(contentId);

      return {
        content_id: contentId,

        title:
          source?.title
          || source?.original_title
          || "Untitled source",

        excerpt: "",

        source_title:
          source?.original_title
          || source?.title
          || "Untitled source",

        source_url:
          source?.url || "",

        published_at:
          source?.published_at || null,

        companies: [],
        solutions: [],
        topics: [],
        universes: [],
        concepts: [],

        selection_sources: [],

        matched_entities: [],
        matched_terms: [],
        matched_angles: [],
      };

    },
  );

}


export default function TouchReportsPage() {

  const [
    reports,
    setReports,
  ] = useState<TouchSavedReportSummary[]>([]);

  const [
    selectedReport,
    setSelectedReport,
  ] = useState<TouchSavedReport | null>(null);

  const [
    brief,
    setBrief,
  ] = useState<TouchBriefStructure | null>(null);

  const [
    loading,
    setLoading,
  ] = useState(true);

  const [
    openingId,
    setOpeningId,
  ] = useState<string | null>(null);

  const [
    error,
    setError,
  ] = useState<string | null>(null);

  useEffect(() => {

    let active = true;

    async function loadReports() {

      try {

        const result =
          await listTouchReports();

        if (active) {
          setReports(result);
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
          setLoading(false);
        }

      }

    }

    void loadReports();

    return () => {
      active = false;
    };

  }, []);

  async function handleOpen(
    reportId: string,
  ) {

    if (openingId) {
      return;
    }

    try {

      setOpeningId(reportId);
      setError(null);

      const report =
        await getTouchReport(
          reportId,
        );

      setBrief(null);
      setSelectedReport(report);

    } catch (exception) {

      setError(
        exception instanceof Error
          ? exception.message
          : "Unable to open the report.",
      );

    } finally {

      setOpeningId(null);

    }

  }

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
          Open an existing report without rebuilding
          its notebook.
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
              setSelectedReport(null);
              setBrief(null);
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
            brief={brief}
            onBriefChange={setBrief}
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

            <p className="text-sm text-gray-500">
              No saved reports yet.
            </p>

          )}

          {reports.map(
            report => (

              <button
                key={report.report_id}
                type="button"
                onClick={() =>
                  handleOpen(
                    report.report_id,
                  )
                }
                disabled={openingId !== null}
                className="
                  w-full
                  rounded-xl
                  border
                  border-gray-200
                  bg-white
                  p-5
                  text-left
                  hover:border-blue-300
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
                    "fr-FR",
                  )}
                  {" · Version "}
                  {report.version_number}
                </span>

                {openingId === report.report_id && (

                  <span
                    className="
                      mt-2
                      block
                      text-xs
                      text-ratecard-blue
                    "
                  >
                    Opening…
                  </span>

                )}

              </button>

            ),
          )}

        </section>

      )}

    </div>

  );

}
