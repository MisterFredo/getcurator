export type DocumentSource = {
  id: string;
  report_id: string;
  report_version: number;
  json_pointer: string;
  quote: string;
  content_id: string | null;
  label: string;
};
export type DocumentMetric = {
  value: number;
  display_value: string;
  label: string;
  context: string;
  source_id: string;
};
export type DocumentChart = {
  kind: "COMPARISON" | "TREND";
  title: string;
  unit: string;
  measure: string;
  scope: string;
  comparability_note: string;
  points: { label: string; value: number; source_id: string }[];
};
export type DocumentPage = {
  page_id: string;
  layout: "COVER" | "SUMMARY" | "METRICS" | "COMPARISON" | "TREND" | "CASE_STUDY" | "ANALYSIS" | "IMPLICATIONS" | "SOURCES";
  title: string;
  eyebrow: string;
  paragraphs: string[];
  bullets: string[];
  metrics: DocumentMetric[];
  chart: DocumentChart | null;
  takeaway: string;
  cautions: string[];
  source_ids: string[];
};
export type ProductionDocument = {
  schema_version: "1.0";
  template: "GETCURATOR_AUTONOMOUS_V1";
  title: string;
  subtitle: string;
  pages: DocumentPage[];
  sources: DocumentSource[];
  review_notes: string[];
};
