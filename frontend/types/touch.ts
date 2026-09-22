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


/* =========================================================
   GUIDED RESEARCH
========================================================= */

export type TouchResearchMode =
  | "DIRECT"
  | "GUIDED";


export type TouchGuidedResearchAction =
  | "START"
  | "ANSWER"
  | "PREPARE_PLAN"
  | "REVISE";


export type TouchGuidedResearchPhase =
  | "INTERVIEW"
  | "PLAN_READY";


export type TouchGuidedResearchType =
  | "ENTITY"
  | "COMPARATIVE"
  | "CROSS_SECTOR"
  | "TOPIC"
  | "EVOLUTION"
  | "EVENT"
  | "MARKET"
  | "OTHER";


export type TouchGuidedEntityType =
  | "company"
  | "solution"
  | "topic";


export type TouchGuidedEntityRole =
  | "PRIMARY"
  | "COMPARISON"
  | "CONTEXT";


export type TouchGuidedAxisType =
  | "CORE_SUBJECT"
  | "COMPARISON"
  | "CONTEXT"
  | "MECHANISM"
  | "EVIDENCE"
  | "LIMITATIONS"
  | "EVOLUTION"
  | "OTHER";


/* =========================================================
   GUIDED ENTITY MENTION
========================================================= */

export type TouchGuidedEntityMention = {
  entity_type:
    TouchGuidedEntityType;

  entity_label:
    string;

  research_role:
    TouchGuidedEntityRole;

  reason:
    string;

  confidence:
    number;
};


/* =========================================================
   GUIDED RESEARCH AXIS
========================================================= */

export type TouchGuidedResearchAxis = {
  axis_id:
    string;

  axis_type:
    TouchGuidedAxisType;

  label:
    string;

  objective:
    string;

  search_terms:
    string[];

  related_angles:
    string[];
};


/* =========================================================
   GUIDED RESEARCH PLAN
========================================================= */

export type TouchGuidedResearchPlan = {
  subject:
    string;

  objective:
    string;

  central_question:
    string;

  research_type:
    TouchGuidedResearchType;

  scope_summary:
    string;

  target_context:
    string | null;

  period_start:
    string | null;

  period_end:
    string | null;

  geographies:
    string[];

  entity_mentions:
    TouchGuidedEntityMention[];

  resolved_entities:
    TouchEntityReference[];

  axes:
    TouchGuidedResearchAxis[];

  search_terms:
    string[];

  related_angles:
    string[];

  exclusions:
    string[];

  assumptions:
    string[];

  editorial_cautions:
    string[];

  missing_information:
    string[];

  ready_for_search:
    boolean;
};


/* =========================================================
   GUIDED RESEARCH REQUEST
========================================================= */

export type TouchGuidedResearchRequest = {
  action:
    TouchGuidedResearchAction;

  message:
    string;

  output_language:
    string;

  period_start:
    string | null;

  period_end:
    string | null;

  companies:
    TouchEntityReference[];

  solutions:
    TouchEntityReference[];

  topics:
    TouchEntityReference[];

  conversation_history:
    TouchConversationMessage[];

  current_plan:
    TouchGuidedResearchPlan | null;
};


/* =========================================================
   GUIDED RESEARCH OUTCOME
========================================================= */

export type TouchGuidedResearchOutcome = {
  phase:
    TouchGuidedResearchPhase;

  assistant_message:
    string;

  questions:
    string[];

  plan:
    TouchGuidedResearchPlan | null;

  missing_information:
    string[];

  ready_for_search:
    boolean;

  used_fallback:
    boolean;

  error:
    string | null;
};


/* =========================================================
   GUIDED RESEARCH RESPONSE
========================================================= */

export type TouchGuidedResearchResponse = {
  status:
    string;

  guided_research:
    TouchGuidedResearchOutcome;
};

/* =========================================================
   GENERATION
========================================================= */

export type TouchDraftStatus =
  | "GENERATED"
  | "GENERATION_FAILED";

export type TouchSectionType =
  | "WHAT_HAPPENED"
  | "WHY_IT_MATTERS"
  | "HOW_IT_WORKS"
  | "BIGGER_PICTURE";


export type TouchGenerationRequest = {
  subject: string;
  objective: string;
  output_language: string;
  content_ids: string[];
};


export type TouchNarrativeSection = {
  section_type: TouchSectionType;
  title: string;
  body: string;
  source_content_ids: string[];
};


export type TouchExecutiveTakeaway = {
  statement: string;
  source_content_ids: string[];
};


export type TouchWatchPoint = {
  label: string;
  explanation: string;
  source_content_ids: string[];
};


export type TouchKeyNumber = {
  value: string;
  label: string;
  context: string;
  source_content_ids: string[];
};


export type TouchDocumentSource = {
  content_id: string;
  title: string;
  source_title: string;
  source_url: string;
  published_at: string | null;
};


export type TouchOnePagerDraft = {
  title: string;
  subtitle: string;

  executive_takeaways:
    TouchExecutiveTakeaway[];

  sections:
    TouchNarrativeSection[];

  key_numbers:
    TouchKeyNumber[];

  what_to_watch:
    TouchWatchPoint[];
};


export type TouchGenerationOutcome = {
  status: TouchDraftStatus;

  draft:
    TouchOnePagerDraft | null;

  sources:
    TouchDocumentSource[];

  error: string | null;
};


export type TouchGenerationResponse = {
  status: string;

  generation:
    TouchGenerationOutcome;
};

/* =========================================================
   EDITORIAL NOTEBOOK
========================================================= */

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


/* =========================================================
   CORPUS NOTEBOOK
========================================================= */

export type TouchCorpusNotebook = {
  subject: string;
  objective: string;

  corpus_summary: string;
  executive_summary: TouchNotebookExecutiveSummaryItem[];

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

/* =========================================================
   NOTEBOOK CONTRIBUTION
========================================================= */

export type TouchNotebookContribution = {
  content_id: string;

  statements: string[];
};

/* =========================================================
   NOTEBOOK REQUEST
========================================================= */

export type TouchNotebookRequest = {
  report_id?: string | null;

  subject: string;
  objective: string;

  content_ids: string[];

  contributions:
    TouchNotebookContribution[];

  output_language: string;
};

/* =========================================================
   NOTEBOOK OUTCOME
========================================================= */

export type TouchNotebookOutcome = {
  status:
    | "GENERATED"
    | "GENERATION_FAILED";

  notebook:
    TouchCorpusNotebook | null;

  source_count: number;

  report_id:
    string | null;

  persistence_error?:
    string | null;

  error:
    string | null;
};


/* =========================================================
   NOTEBOOK RESPONSE
========================================================= */

export type TouchNotebookResponse = {
  status: string;

  notebook_generation:
    TouchNotebookOutcome;
};

export type TouchSavedReportSummary = {
  report_id: string;
  parent_report_id: string | null;
  version_number: number;
  created_at: string;
  subject: string;
  objective: string;
  output_language: string;
  source_count: number;
};

export type TouchSavedReport = {
  report_id: string;
  parent_report_id: string | null;
  version_number: number;
  created_at: string;
  subject: string;
  objective: string;
  output_language: string;
  content_ids: string[];
  contributions: TouchNotebookContribution[];
  sources: Array<{
    content_id: string;
    title: string | null;
    original_title: string | null;
    source_name: string | null;
    url: string | null;
    published_at: string | null;
  }>;
  notebook: TouchCorpusNotebook;
};

/* =========================================================
   TOUCH BRIEF
========================================================= */

export type TouchBriefType =
  | "STRATEGIC_EVENT"
  | "COMPARATIVE"
  | "CHRONOLOGICAL"
  | "PEDAGOGICAL"
  | "MARKET_ANALYSIS"
  | "HYBRID";


export type TouchBriefSectionType =
  | "ESSENTIAL"
  | "EXPLANATION"
  | "MECHANISM"
  | "ACTOR_READING"
  | "COMPARISON"
  | "TIMELINE"
  | "MARKET_DYNAMICS"
  | "TENSIONS"
  | "KEY_NUMBERS"
  | "EXAMPLES"
  | "OPEN_QUESTIONS"
  | "OTHER";


export type TouchBriefSectionLayout =
  | "BULLETS"
  | "STEPS"
  | "COLUMNS"
  | "TIMELINE"
  | "NUMBER_CARDS";


export type TouchBriefSectionGroup = {
  label: string;

  note_ids: string[];
  number_ids: string[];
  event_ids: string[];
};


export type TouchBriefSection = {
  section_id: string;

  section_type:
    TouchBriefSectionType;

  title: string;
  introduction: string;

  layout:
    TouchBriefSectionLayout;

  note_ids: string[];
  number_ids: string[];
  event_ids: string[];

  groups:
    TouchBriefSectionGroup[];
};


export type TouchBriefStructure = {
  brief_type:
    TouchBriefType;

  secondary_brief_type:
    TouchBriefType | null;

  recommendation_reason: string;

  headline: string;
  subheadline: string;

  central_question: string;
  key_message: string;

  sections:
    TouchBriefSection[];

  hidden_note_ids: string[];
  hidden_number_ids: string[];

  editorial_cautions: string[];
};


/* =========================================================
   BRIEF REQUEST
========================================================= */

export type TouchBriefRequest = {
  notebook:
    TouchCorpusNotebook;

  requested_brief_type:
    "AUTO";

  editorial_instruction: string;

  output_language: string;
};


/* =========================================================
   BRIEF OUTCOME
========================================================= */

export type TouchBriefOutcome = {
  status:
    | "GENERATED"
    | "GENERATION_FAILED";

  brief:
    TouchBriefStructure | null;

  error: string | null;
};


/* =========================================================
   BRIEF RESPONSE
========================================================= */

export type TouchBriefResponse = {
  status: string;

  brief_generation:
    TouchBriefOutcome;
};


