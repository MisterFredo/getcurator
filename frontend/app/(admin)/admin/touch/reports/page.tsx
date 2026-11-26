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


type TypedSavedReport = TouchSavedReport & {
  report_type?: "MONTHLY" | "RESEARCH";
};

type ProfileRecord = {
  ID_USER?: string;
  id_user?: string;
  user_id?: string;
  id?: string;
  DISPLAY_NAME?: string;
  display_name?: string;
  NAME?: string;
  name?: string;
};


// ============================================================
// REPORT SOURCES
// ============================================================

function reportSources(
  report: TouchSavedReport,
): TouchContentCandidate[] {
  const sourcesById = new Map(
    report.sources.map(source => [
      source.content_id,
      source,
    ]),
  );

  return report.content_ids.map(contentId => {
    const source = sourcesById.get(contentId);

    return {
      content_id: contentId,

      title:
        source?.title ||
        source?.original_title ||
        "Untitled source",

      excerpt: "",

      source_title:
        source?.source_name ||
        source?.original_title ||
        source?.title ||
        "Untitled source",

      source_url: source?.url || "",

      published_at: source?.published_at || null,

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
  });
}


// ============================================================
// PAGE
// ============================================================

export default function TouchReportsPage() {
  const [selectedReport, setSelectedReport] =
    useState<TypedSavedReport | null>(null);

  const [selectedExpertName, setSelectedExpertName] =
    useState<string | null>(null);

  const profileNamesRef =
    useRef<Record<string, string> | null>(null);

  const [brief, setBrief] =
    useState<TouchBriefStructure | null>(null);

  const [openingId, setOpeningId] =
    useState<string | null>(null);

  const [error, setError] =
    useState<string | null>(null);


  // ==========================================================
  // LOAD PROFILE NAMES — EXPERTS + USERS
  // ==========================================================

  async function loadProfileNames(): Promise<Record<string, string>> {
    const [expertsResponse, usersResponse] = await Promise.all([
      api.get("/user/admin/experts"),
      api.get(
        "/digest/admin/subject-digests/recipients?audience=user",
      ),
    ]);

    const names: Record<string, string> = {
      ...(profileNamesRef.current ?? {}),
    };

    const profiles: ProfileRecord[] = [
      ...(expertsResponse.experts ?? []),
      ...(usersResponse.recipients ?? []),
    ];

    for (const profile of profiles) {
      const id =
        profile.ID_USER ??
        profile.id_user ??
        profile.user_id ??
        profile.id;

      const name =
        profile.DISPLAY_NAME?.trim() ||
        profile.display_name?.trim() ||
        profile.NAME?.trim() ||
        profile.name?.trim();

      if (
        typeof id === "string" &&
        id.trim() &&
        name
      ) {
        names[id.trim()] = name;
      }
    }

    profileNamesRef.current = names;

    return names;
  }


  // ==========================================================
  // OPEN REPORT
  // ==========================================================

  async function handleOpen(reportId: string) {
    if (openingId) return;

    setOpeningId(reportId);
    setError(null);

    try {
      const report =
        (await getTouchReport(reportId)) as TypedSavedReport;

      let profileName: string | null = null;

      if (
        report.expert_id &&
        report.report_type === "MONTHLY"
      ) {
        let names = profileNamesRef.current;

        if (!names || !names[report.expert_id]) {
          names = await loadProfileNames();
        }

        profileName = names[report.expert_id] ?? null;

        if (!profileName) {
          throw new Error(
            "Le nom du profil associé au rapport est introuvable.",
          );
        }
      }

      setSelectedExpertName(profileName);
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


  // ==========================================================
  // CLOSE REPORT
  // ==========================================================

  function handleClose() {
    setSelectedReport(null);
    setSelectedExpertName(null);
    setBrief(null);
    setError(null);
  }


  // ==========================================================
  // RENDER
  // ==========================================================

  return (
    <div className="space-y-8">
      <header>
        <Link
          href="/admin/touch"
          className="text-sm font-medium text-ratecard-blue hover:underline"
        >
          ← Back to Touch
        </Link>

        <h1 className="mt-3 text-3xl font-semibold text-gray-900">
          Touch reports
        </h1>

        <p className="mt-1 text-sm text-gray-500">
          Review corpora and open saved reports from one list.
        </p>
      </header>

      {error && (
        <div
          role="alert"
          className="rounded-lg border border-red-200 bg-red-50 p-4 text-sm text-red-700"
        >
          {error}
        </div>
      )}

      {/* Keep the list mounted so filters survive opening a report. */}
      <div className={selectedReport ? "hidden" : ""}>
        <TouchMonthlyEditionList
          onOpenReport={handleOpen}
          disabled={openingId !== null}
        />
      </div>

      {selectedReport && (
        <div className="space-y-6">
          <button
            type="button"
            onClick={handleClose}
            className="text-sm font-medium text-ratecard-blue hover:underline"
          >
            ← All reports
          </button>

          <TouchOutputChoice
            reportId={selectedReport.report_id}
            notebook={selectedReport.notebook}
            expertName={selectedExpertName}
            reportType={selectedReport.report_type ?? "RESEARCH"}
            periodStart={selectedReport.period_start}
            periodEnd={selectedReport.period_end}
            outputLanguage={selectedReport.output_language}
            sources={reportSources(selectedReport)}
            brief={brief}
            onBriefChange={setBrief}
          />
        </div>
      )}
    </div>
  );
}
