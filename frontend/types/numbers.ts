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
   COMMON
========================================================= */

export type NumberStatus =
  | "ACCEPTED"
  | "REVIEW"
  | "REJECTED";

export type NumberEntityType =
  | "company"
  | "topic"
  | "solution";

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
   NUMBER OBSERVATION
========================================================= */

export type NumberObservationEntity = {
  entity_type:
    | "company"
    | "topic"
    | "solution";

  entity_id: string;
  entity_label: string;
};

export type NumberObservation = {
  id_number: string;
  id_content: string;

  content_title: string | null;
  raw_line: string;

  label: string | null;
  metric_type: string | null;

  value: number | null;
  value_min: number | null;
  value_max: number | null;

  unit: string | null;
  scale: string | null;

  zone: string | null;
  period_label: string | null;
  value_status: string | null;

  transformer_status: NumberStatus;
  effective_status: NumberStatus;

  manual_decision: NumberStatus | null;

  confidence: number;

  reason: string | null;
  review_reason: string | null;

  reviewed_by: string | null;
  reviewed_at: string | null;

  published_at: string | null;
  transformer_version: string;

  entities: NumberObservationEntity[];
};

/* =========================================================
   PAGINATION
========================================================= */

export type NumberObservationPagination = {
  total: number;
  limit: number;
  offset: number;
  has_more: boolean;
};

/* =========================================================
   MODERATION
========================================================= */

export type NumberModerationSkip = {
  id_number: string;
  reason: string;
};

export type NumberModerationResult = {
  decision: NumberStatus;

  requested: number;
  updated: number;
  skipped_count: number;

  updated_ids: string[];
  skipped: NumberModerationSkip[];
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

export type NumberObservationsResponse = {
  status: string;
  items: NumberObservation[];
  pagination: NumberObservationPagination;
};

export type NumberModerationResponse = {
  status: string;
  result: NumberModerationResult;
};


/* =========================================================
   NUMBERS KNOWLEDGE STATUS
========================================================= */

export type NumbersKnowledgeStatus = {
  total_entities: number;
  started_entities: number;
  up_to_date_entities: number;
  pending_entities: number;
  not_started_entities: number;

  total_observations: number;
  processed_observations: number;
  pending_observations: number;

  progress_percent: number;
};

/* =========================================================
   NUMBERS KNOWLEDGE CONTINUE
========================================================= */

export type NumbersKnowledgeFailure = {
  entity_type: string;
  entity_id: string;
  entity_label: string | null;
  error: string;
};

export type NumbersKnowledgeContinueResult = {
  status:
    | "processed"
    | "partial"
    | "completed";

  selected_entities: number;
  built_entities: number;
  no_data_entities: number;
  failed_entities: number;

  results: unknown[];
  failures: NumbersKnowledgeFailure[];
};

/* =========================================================
   NUMBERS KNOWLEDGE RESPONSES
========================================================= */

export type NumbersKnowledgeStatusResponse = {
  status: string;
  result: NumbersKnowledgeStatus;
};

export type NumbersKnowledgeContinueResponse = {
  status: string;
  result: NumbersKnowledgeContinueResult;
};
