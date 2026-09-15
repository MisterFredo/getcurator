import {
  api,
} from "@/lib/api";

import type {
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
