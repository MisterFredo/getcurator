import type {
  TouchCorpusNotebook,
} from "@/types/touch";


/* =========================================================
   REQUEST
========================================================= */

export type ProductionOutputFormat =
  | "AUTONOMOUS_REPORT"
  | "SPEAKER_PRESENTATION";

export type ProductionPrepareRequest = {
  title: string;
  report_ids: string[];
  objective: string;
  target_audience: string;
  output_language: "fr" | "en";
  output_format: ProductionOutputFormat;
  target_page_count: number | null;
};


/* =========================================================
   CORPUS
========================================================= */

export type ProductionEvidenceKind =
  | "NOTE"
  | "EVENT"
  | "NUMBER"
  | "SECTION"
  | "SUMMARY"
  | "CROSS_READING";

export type ProductionEvidenceReference = {
  reference_id: string;
  report_id: string;
  report_version: number;
  kind: ProductionEvidenceKind;
  local_id: string;
};

export type ProductionReportSnapshot = {
  report_id: string;
  version_number: number;
  snapshot_sha256: string;

  payload: {
    notebook: TouchCorpusNotebook;
    [key: string]: unknown;
  };
};

export type ProductionCorpusCounts = {
  reports: number;
  unique_contents: number;
  notes: number;
  events: number;
  number_occurrences: number;
  unique_number_ids: number;
  sections: number;
  executive_summary_items: number;
  cross_readings: number;
};

export type ProductionPreparedCorpus = {
  schema_version: "1.0";
  production_id: string;
  prepared_at: string;
  status: "CORPUS_PREPARED";
  data_policy: "SAVED_TOUCH_REPORTS_ONLY";

  request: ProductionPrepareRequest;

  reports: ProductionReportSnapshot[];
  evidence_index: ProductionEvidenceReference[];
  counts: ProductionCorpusCounts;

  corpus_sha256: string;
};


/* =========================================================
   PRODUCTION
========================================================= */

export type ProductionStatus =
  | "CORPUS_PREPARED"
  | "PLAN_TO_REVIEW";

export type ProductionSummary = {
  production_id: string;
  status: ProductionStatus;
  title: string;
  output_language: "fr" | "en";
  output_format: ProductionOutputFormat;
  target_page_count: number | null;
  created_at: string;
  updated_at: string;
  corpus_sha256: string;
};

export type Production = ProductionSummary & {
  corpus: ProductionPreparedCorpus;
};


/* =========================================================
   EDITORIAL PLAN
========================================================= */

export type ProductionPageLayout =
  | "COVER"
  | "EXECUTIVE_SUMMARY"
  | "CHART_WITH_ANALYSIS"
  | "KEY_NUMBERS"
  | "CASE_STUDY"
  | "COMPARISON"
  | "EXPLANATORY"
  | "IMPLICATIONS"
  | "SOURCES";

export type ProductionPagePlan = {
  page_id: string;
  layout: ProductionPageLayout;
  title: string;
  key_message: string;
  explanation_outline: string[];
  evidence_reference_ids: string[];
  number_reference_ids: string[];
  visual_intent: string;
  cautions: string[];
};

export type ProductionEditorialPlan = {
  title: string;
  editorial_angle: string;
  pages: ProductionPagePlan[];
};

export type ProductionPlanSnapshot = {
  production_id: string;
  corpus_sha256: string;
  generated_at: string;
  status: "PLAN_TO_REVIEW";
  plan: ProductionEditorialPlan;
};

export type ProductionPlanVersionSummary = {
  plan_id: string;
  production_id: string;
  plan_version: number;
  corpus_sha256: string;
  created_at: string;
};

export type ProductionSavedPlan =
  ProductionPlanVersionSummary & {
    snapshot: ProductionPlanSnapshot;
  };
