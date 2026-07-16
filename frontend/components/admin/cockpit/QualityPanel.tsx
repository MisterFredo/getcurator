"use client";

import { Play } from "lucide-react";

import {
  useCockpitQuality,
} from "@/hooks/useCockpitQuality";

/* ========================================================= */

type Props = {
  onResults: (
    title: string,
    rows: any[],
  ) => void;
};

/* ========================================================= */

type Report = {
  endpoint: string;

  title: string;

  description: string;
};

/* ========================================================= */

const REPORTS: Report[] = [

  {
    endpoint: "duplicate-titles",
    title: "Duplicate Titles",
    description:
      "Detect duplicated content titles.",
  },

  {
    endpoint: "unmatched-companies",
    title: "Unmatched Companies",
    description:
      "Companies detected but not matched.",
  },

  {
    endpoint: "unmatched-solutions",
    title: "Unmatched Solutions",
    description:
      "Solutions detected but not matched.",
  },

  {
    endpoint: "numbers-structure",
    title: "Numbers Structure",
    description:
      "Validate structured numbers.",
  },

];

/* ========================================================= */

export default function QualityPanel({
  onResults,
}: Props) {

  const {
    loading,
    load,
  } = useCockpitQuality();

  /* ======================================================= */

  async function runReport(
    report: Report,
  ) {

    const rows =
      await load(
        report.endpoint,
      );

    onResults(
      report.title,
      rows,
    );

  }

  /* ======================================================= */

  return (

    <div className="border rounded-xl bg-white p-6">

      <div className="mb-6">

        <h2 className="text-xl font-semibold">
          Quality
        </h2>

        <p className="text-sm text-gray-500 mt-1">
          Dataset quality diagnostics.
        </p>

      </div>

      <div className="space-y-3">

        {REPORTS.map((report) => (

          <div
            key={report.endpoint}
            className="flex items-center justify-between border rounded-lg p-4"
          >

            <div>

              <div className="font-medium">
                {report.title}
              </div>

              <div className="text-sm text-gray-500">
                {report.description}
              </div>

            </div>

            <button
              disabled={loading}
              onClick={() =>
                runReport(report)
              }
              className="inline-flex items-center gap-2 rounded-lg bg-ratecard-blue px-4 py-2 text-white disabled:opacity-50"
            >

              <Play size={16} />

              Run

            </button>

          </div>

        ))}

      </div>

    </div>

  );

}
