/* =========================================================
   TYPES
========================================================= */

export type TouchEntityType =
  | "company"
  | "solution"
  | "topic";

export type TouchConversationRole =
  | "user"
  | "assistant";

export type TouchCandidateSource =
  | "CORE_COMPANY"
  | "CORE_SOLUTION"
  | "CORE_TOPIC"
  | "SEARCH_TERM"
  | "RELATED_ANGLE";

export type TouchContentRelevance =
  | "DIRECT"
  | "CONTEXT"
  | "RELATED"
  | "OUT_OF_SCOPE";

export type TouchCoverageDimension =
  | "ANNOUNCEMENT"
  | "ACTORS"
  | "MECHANISM"
  | "PRODUCT_SCOPE"
  | "GEOGRAPHY"
  | "TIMELINE"
  | "BUSINESS_MODEL"
  | "STRATEGY"
  | "MARKET_CONTEXT"
  | "NUMBERS"
  | "REACTIONS"
  | "LIMITATIONS"
  | "OUTLOOK";


/* =========================================================
   ENTITY
========================================================= */

export type TouchEntityReference = {
  entity_type: TouchEntityType;
  entity_id: string;
  entity_label: string;
};


/* =========================================================
   CONVERSATION
========================================================= */

export type TouchConversationMessage = {
  role: TouchConversationRole;
  content: string;
};


/* =========================================================
   SEARCH REQUEST
========================================================= */

export type TouchResearchBrief = {
  query: string;
  output_language: string;

  period_start: string | null;
  period_end: string | null;

  companies: TouchEntityReference[];
  solutions: TouchEntityReference[];
  topics: TouchEntityReference[];

  conversation_history:
    TouchConversationMessage[];

  selected_content_ids: string[];
  dismissed_content_ids: string[];

  previously_proposed_content_ids:
    string[];
};


/* =========================================================
   INTERPRETATION
========================================================= */

export type TouchResearchInterpretation = {
  subject: string;
  objective: string;

  companies: TouchEntityReference[];
  solutions: TouchEntityReference[];
  topics: TouchEntityReference[];

  search_terms: string[];
  related_angles: string[];

  response_message: string;
};


/* =========================================================
   CONTENT ENTITY
========================================================= */

export type TouchContentEntity = {
  id_company?: string;
  id_solution?: string;
  id_topic?: string;
  id_universe?: string;
  id_concept?: string;

  name?: string;
  label?: string;
  canonical_label?: string;
  title?: string;

  media_logo_rectangle_id?: string;

  [key: string]: unknown;
};


/* =========================================================
   CANDIDATE
========================================================= */

export type TouchContentCandidate = {
  content_id: string;

  title: string;
  excerpt: string;

  source_title: string;
  source_url: string;

  published_at: string | null;

  companies: TouchContentEntity[];
  solutions: TouchContentEntity[];
  topics: TouchContentEntity[];
  universes: TouchContentEntity[];
  concepts: TouchContentEntity[];

  selection_sources: TouchCandidateSource[];

  matched_entities: string[];
  matched_terms: string[];
  matched_angles: string[];
};


/* =========================================================
   DECISION
========================================================= */

export type TouchContentDecision = {
  content_id: string;

  event_key: string | null;

  relevance: TouchContentRelevance;
  relevance_score: number;

  reason: string;

  coverage_dimensions:
    TouchCoverageDimension[];

  key_contributions: string[];

  overlaps_with: string[];
  contradictions_with: string[];
};


/* =========================================================
   EVALUATION
========================================================= */

export type TouchCandidateEvaluation = {
  decisions: TouchContentDecision[];
};


/* =========================================================
   EVENT GROUP
========================================================= */

export type TouchEventGroup = {
  event_key: string;
  label: string;

  content_ids: string[];

  shared_information: string[];

  complementary_contributions:
    string[];

  contradictions: string[];
};


/* =========================================================
   COVERAGE
========================================================= */

export type TouchCoverageAnalysis = {
  summary: string;

  covered_dimensions:
    TouchCoverageDimension[];

  missing_dimensions:
    TouchCoverageDimension[];

  strengths: string[];
  gaps: string[];
  contradictions: string[];

  suggested_follow_ups: string[];
};


/* =========================================================
   CONSOLIDATION
========================================================= */

export type TouchConsolidation = {
  event_groups: TouchEventGroup[];

  coverage_analysis:
    TouchCoverageAnalysis;
};


/* =========================================================
   SEARCH RESULT
========================================================= */

export type TouchSearchResult = {
  interpretation:
    TouchResearchInterpretation;

  candidates:
    TouchContentCandidate[];

  evaluation:
    TouchCandidateEvaluation;

  consolidation:
    TouchConsolidation;

  used_fallback: boolean;
  errors: string[];
};


/* =========================================================
   API RESPONSE
========================================================= */

export type TouchSearchResponse = {
  status: string;
  search: TouchSearchResult;
};
