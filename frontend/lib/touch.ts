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
  TouchNotebookOutcome,
  TouchNotebookRequest,
  TouchNotebookResponse,
  TouchResearchBrief,
  TouchSearchResponse,
  TouchSearchResult,
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
