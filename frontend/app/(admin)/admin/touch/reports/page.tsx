"use client";

import { useRef, useState } from "react";
import Link from "next/link";
import { api } from "@/lib/api";
import { getTouchReport } from "@/lib/touch";
import TouchMonthlyEditionList from "@/components/admin/touch/TouchMonthlyEditionList";
import TouchOutputChoice from "@/components/admin/touch/TouchOutputChoice";
import type {
  TouchBriefStructure,
  TouchContentCandidate,
  TouchSavedReport,
} from "@/types/touch";

type TypedSavedReport = TouchSavedReport & {report_type?: "MONTHLY" | "RESEARCH"};

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


export default function TouchReportsPage() {
  const [selectedReport, setSelectedReport] = useState<TypedSavedReport | null>(null);
  const [selectedExpertName, setSelectedExpertName] = useState<string | null>(null);
  const expertNamesRef = useRef<Record<string, string> | null>(null);
  const [brief, setBrief] = useState<TouchBriefStructure | null>(null);
  const [openingId, setOpeningId] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);

  async function handleOpen(reportId: string) {
    if (openingId) return;
    setOpeningId(reportId);
    setError(null);
    try {
      const report = await getTouchReport(reportId) as TypedSavedReport;
      let expertName: string | null = null;
      if (report.expert_id && report.report_type === "MONTHLY") {
        if (!expertNamesRef.current || !expertNamesRef.current[report.expert_id]) {
          const response = await api.get("/user/admin/experts");
          const names: Record<string, string> = {};
          for (const expert of response.experts ?? []) {
            const id = expert.ID_USER ?? expert.id_user ?? expert.user_id ?? expert.id;
            const name = expert.DISPLAY_NAME ?? expert.display_name ?? expert.NAME ?? expert.name;
            if (typeof id === "string" && typeof name === "string" && name.trim()) names[id] = name.trim();
          }
          expertNamesRef.current = names;
        }
        expertName = expertNamesRef.current[report.expert_id] ?? null;
        if (!expertName) throw new Error("The expert name could not be found. Refresh the expert profile before opening this report.");
      }
      setSelectedExpertName(expertName);
      setBrief(null);
      setSelectedReport(report);
    } catch (exception) {
      setError(exception instanceof Error ? exception.message : "Unable to open the report.");
    } finally {
      setOpeningId(null);
    }
  }

  return (
    <div className="space-y-8">
      <header>
        <Link href="/admin/touch" className="text-sm font-medium text-ratecard-blue hover:underline">
          ← Back to Touch
        </Link>
        <h1 className="mt-3 text-3xl font-semibold text-gray-900">Touch reports</h1>
        <p className="mt-1 text-sm text-gray-500">
          Review corpora and open saved reports from one list.
        </p>
      </header>
      {error && <div role="alert" className="rounded-lg border border-red-200 bg-red-50 p-4 text-sm text-red-700">{error}</div>}
      {/* Keep the list mounted so filters survive opening a report. */}
      <div className={selectedReport ? "hidden" : ""}>
        <TouchMonthlyEditionList onOpenReport={handleOpen} disabled={openingId !== null} />
      </div>
      {selectedReport && (
        <div className="space-y-6">
          <button type="button" onClick={() => { setSelectedReport(null); setSelectedExpertName(null); setBrief(null); }}
            className="text-sm font-medium text-ratecard-blue hover:underline">
            ← All reports
          </button>
          <TouchOutputChoice notebook={selectedReport.notebook}
            expertName={selectedExpertName}
            reportType={selectedReport.report_type ?? "RESEARCH"}
            periodStart={selectedReport.period_start}
            periodEnd={selectedReport.period_end}
            outputLanguage={selectedReport.output_language}
            sources={reportSources(selectedReport)} brief={brief} onBriefChange={setBrief} />
        </div>
      )}
    </div>
  );
}
