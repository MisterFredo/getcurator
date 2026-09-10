export type NumbersItem = {
  entity_type: string;
  entity_id: string;
  entity_name?: string;

  year: number;
  period: number;
  frequency: string;

  nb_numbers: number;
  nb_unique_numbers: number;

  numbers_status: string;
};


type NumberItem = {
  id_content: string;
  label: string;
  value: string;
  unit: string;

  // 🔥 6 colonnes
  actor: string;
  market: string;
  period: string;

  topics?: {
    id: string;
    label: string;
    checked: boolean;
  }[];
};

/* =========================================================
   NUMBERS BACKFILL MONITORING
========================================================= */

export type NumbersBackfillStatus = {
  transformer_version: string;

  total_contents: number;
  total_raw_numbers: number;

  completed_contents: number;
  failed_contents: number;
  processing_contents: number;
  pending_contents: number;

  total_observations: number;
  accepted_observations: number;
  review_observations: number;
  rejected_observations: number;

  progress_percent: number;
};

/* =========================================================
   NUMBERS BACKFILL RESULT
========================================================= */

export type NumbersBackfillContentResult = {
  id_content: string;
  title: string;
  published_at: string | null;

  raw_numbers_count: number;
  accepted_count: number;
  rejected_count: number;
  review_count: number;
};

export type NumbersBackfillFailure = {
  id_content: string;
  error: string;
};

export type NumbersBackfillStorage = {
  contents_processed: number;
  observations_saved: number;
  relations_saved: number;
};

export type NumbersBackfillResult = {
  status:
    | "processed"
    | "partial"
    | "completed";

  transformer_version: string;

  selected_count: number;
  processed_count: number;
  failed_count: number;

  storage: NumbersBackfillStorage;

  results: NumbersBackfillContentResult[];
  failures: NumbersBackfillFailure[];
};

/* =========================================================
   API RESPONSES
========================================================= */

export type NumbersBackfillStatusResponse = {
  status: string;
  result: NumbersBackfillStatus;
};

export type NumbersBackfillResponse = {
  status: string;
  result: NumbersBackfillResult;
};
