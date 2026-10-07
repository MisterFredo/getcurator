export type TouchCrossReadingType = "CONVERGENCE" | "DIFFERENCE" | "ENABLING_CONDITION" | "FRICTION" | "EVIDENCE_GAP";

export type TouchEvidenceNoteType =
  | "FACT"
  | "MECHANISM"
  | "NUMBER"
  | "STRATEGIC_READING"
  | "TENSION"
  | "LIMITATION"
  | "UNCERTAINTY"
  | "COMPARISON"
  | "MILESTONE"
  | "EXAMPLE";


export type TouchEvidenceConfidence =
  | "HIGH"
  | "MEDIUM"
  | "LOW";


export type TouchEvidenceStatus =
  | "VALIDATED"
  | "TO_VERIFY"
  | "CONTRADICTED";


export type TouchEvidenceNote = {
  note_id: string;

  note_type:
    TouchEvidenceNoteType;

  statement: string;
  explanation: string;

  actors: string[];
  geographies: string[];
  dates: string[];

  confidence:
    TouchEvidenceConfidence;

  status:
    TouchEvidenceStatus;

  source_content_ids: string[];
};


/* =========================================================
   NOTEBOOK EVENT
========================================================= */

export type TouchNotebookEvent = {
  event_id: string;

  title: string;
  description: string;

  event_date: string | null;

  actors: string[];

  note_ids: string[];
  number_ids: string[];

  source_content_ids: string[];
};


/* =========================================================
   NOTEBOOK NUMBER ENTITY
========================================================= */

export type TouchNotebookNumberEntity = {
  entity_type: string | null;
  entity_id: string | null;
  entity_label: string | null;
};


/* =========================================================
   NOTEBOOK NUMBER
========================================================= */

export type TouchNotebookNumber = {
  number_id: string;

  id_content: string;

  label: string | null;
  metric_type: string | null;

  value:
    | string
    | number
    | null;

  value_min:
    | string
    | number
    | null;

  value_max:
    | string
    | number
    | null;

  unit: string | null;
  scale: string | null;

  zone: string | null;
  period_label: string | null;

  value_status: string | null;

  confidence: number;

  entities:
    TouchNotebookNumberEntity[];

  source_content_ids: string[];
};


/* =========================================================
   NOTEBOOK TIMELINE
========================================================= */

export type TouchNotebookTimelineItem = {
  date: string;

  label: string;
  description: string;

  event_id: string | null;

  note_ids: string[];
  source_content_ids: string[];
};


/* =========================================================
   NOTEBOOK DIMENSION
========================================================= */

export type TouchNotebookDimension = {
  label: string;
  summary: string;

  note_ids: string[];
  source_content_ids: string[];
};

/* =========================================================
   NOTEBOOK SECTION
========================================================= */

export type TouchNotebookSection = {
  section_id: string;

  title: string;
  description: string;

  event_ids: string[];
  note_ids: string[];
  number_ids: string[];
};


/* =========================================================
   QUARANTINED NUMBER
========================================================= */

export type TouchQuarantinedNumber = {
  value: string;
  unit: string;
  metric: string;
  context: string;

  reason: string;

  source_content_ids: string[];
};


/* =========================================================
   CONTRADICTION
========================================================= */

export type TouchNotebookContradiction = {
  subject: string;
  description: string;

  note_ids: string[];
  source_content_ids: string[];

  resolution: string | null;
};

export type TouchNotebookExecutiveSummaryItem = {
  summary_id: string;
  statement: string;
  note_ids: string[];
  source_content_ids: string[];
};


export type TouchNotebookCrossReading = {
  reading_id: string;

  title: string;

  statement: string;

  reading_type:
    TouchCrossReadingType;

  note_ids: string[];

  source_content_ids: string[];

  confidence:
    TouchEvidenceConfidence;
};

/* =========================================================
   CORPUS NOTEBOOK
========================================================= */

export type TouchCorpusNotebook = {
  subject: string;
  objective: string;

  corpus_summary: string;
  executive_summary: TouchNotebookExecutiveSummaryItem[];
  cross_readings:
     TouchNotebookCrossReading[];

  sections:
    TouchNotebookSection[];

  notes: TouchEvidenceNote[];

  events: TouchNotebookEvent[];

  timeline:
    TouchNotebookTimelineItem[];

  dimensions:
    TouchNotebookDimension[];

  validated_numbers:
    TouchNotebookNumber[];

  quarantined_numbers:
    TouchQuarantinedNumber[];

  contradictions:
    TouchNotebookContradiction[];

  corpus_strengths: string[];
  corpus_limits: string[];
};


export type KnowledgeSource = {
  content_id: string;
  title: string | null;
  original_title: string | null;
  source_name: string | null;
  url: string | null;
  published_at: string | null;
};
export type KnowledgeDocumentSource = {
  content_id: string; title: string; source_title: string;
  source_url: string; published_at: string | null;
};
export type KnowledgeFilters = {
  expert_id: string | null; month: string | null; output_language: "fr" | "en" | null;
};
export type KnowledgeSummary = {
  report_id: string; subject: string; objective: string;
  expert_id: string | null; expert_name: string | null;
  period_start: string | null; period_end: string | null;
  output_language: string; created_at: string; published_at: string;
  source_count: number; summary: string; key_points: string[];
  match_type?: "DIRECT" | "PARTIAL"; match_reason?: string;
  match_evidence?: { evidence_id: string; text: string; explanation?: string };
};
export type KnowledgeReport = {
  report_id: string; subject: string; objective: string; expert_id: string | null;
  period_start: string | null; period_end: string | null;
  output_language: string; created_at: string; published_at: string;
  sources: KnowledgeSource[]; notebook: TouchCorpusNotebook;
};
export type KnowledgeMessage = {role: "user" | "assistant"; content: string};
export type KnowledgeCatalogue = {
  items: KnowledgeSummary[];
  pagination: {total: number; limit: number; offset: number; has_more: boolean};
};
export type KnowledgeSearch = {
  items: KnowledgeSummary[]; assistant_message: string;
  phase: "RESULTS" | "CLARIFY" | "OUT_OF_SCOPE"; has_more: boolean;
};
export type KnowledgeAvailableFilters = {
  experts: {expert_id: string; label: string}[]; months: string[]; languages: string[];
};
