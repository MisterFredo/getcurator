import {
  api,
} from "@/lib/api";

import type {
  TouchBriefOutcome,
  TouchBriefRequest,
  TouchBriefResponse,
  TouchCorpusNotebook,
  TouchGenerationOutcome,
  TouchGenerationRequest,
  TouchGenerationResponse,
  TouchGuidedResearchOutcome,
  TouchGuidedResearchRequest,
  TouchGuidedResearchResponse,
  TouchNotebookOutcome,
  TouchNotebookRequest,
  TouchNotebookResponse,
  TouchResearchBrief,
  TouchSearchResponse,
  TouchSearchResult,
  TouchSavedReportSummary,
  TouchSavedReport,
} from "@/types/touch";


/* =========================================================
   TYPES
========================================================= */

export type TouchSearchResponseMode =
  | "full"
  | "analysis"
  | "consolidation";


/* =========================================================
   SEARCH
========================================================= */

export async function searchTouchContents(
  brief: TouchResearchBrief,
  responseMode: TouchSearchResponseMode = "full",
): Promise<TouchSearchResult> {

  const params =
    new URLSearchParams();

  params.set(
    "response_mode",
    responseMode,
  );

  const response:
    TouchSearchResponse =
      await api.post(
        `/touch/search?${params.toString()}`,
        brief,
      );

  return response.search;

}

/* =========================================================
   GUIDED RESEARCH
========================================================= */

export async function continueTouchGuidedResearch(
  request: TouchGuidedResearchRequest,
): Promise<TouchGuidedResearchOutcome> {

  const response:
    TouchGuidedResearchResponse =
      await api.post(
        "/touch/research-guide",
        request,
      );

  return response.guided_research;

}


/* =========================================================
   GENERATE ONE-PAGER
========================================================= */

export async function generateTouchOnePager(
  request: TouchGenerationRequest,
): Promise<TouchGenerationOutcome> {

  const response:
    TouchGenerationResponse =
      await api.post(
        "/touch/generate",
        request,
      );

  return response.generation;

}

/* =========================================================
   BUILD EDITORIAL NOTEBOOK
========================================================= */

export async function buildTouchNotebook(
  request: TouchNotebookRequest,
): Promise<TouchNotebookOutcome> {

  const response:
    TouchNotebookResponse =
      await api.post(
        "/touch/notebook",
        request,
      );

  return response.notebook_generation;

}

export async function saveTouchReport(
  request: TouchNotebookRequest,
  notebook: TouchCorpusNotebook,
): Promise<string> {

  const response: {
    status: string;
    report_id: string;
  } = await api.post(
    "/touch/reports",
    {
      request,
      notebook,
    },
  );

  return response.report_id;

}

export async function listTouchReports():
  Promise<TouchSavedReportSummary[]> {

  const response: {
    status: string;
    reports: TouchSavedReportSummary[];
  } = await api.get(
    "/touch/reports",
  );

  return response.reports;

}

export async function getTouchReport(
  reportId: string,
): Promise<TouchSavedReport> {

  const response: {
    status: string;
    report: TouchSavedReport;
  } = await api.get(
    `/touch/reports/${encodeURIComponent(reportId)}`,
  );

  return response.report;

}

/* =========================================================
   BUILD INTERPRETED BRIEF
========================================================= */

export async function buildTouchBrief(
  request: TouchBriefRequest,
): Promise<TouchBriefOutcome> {

  const response:
    TouchBriefResponse =
      await api.post(
        "/touch/brief",
        request,
      );

  return response.brief_generation;

}

/* =========================================================
   DELETE SAVED TOUCH REPORT
========================================================= */

export async function deleteTouchReport(
  reportId: string,
): Promise<void> {

  await api.delete(
    `/touch/reports/${reportId}`,
  );

}
