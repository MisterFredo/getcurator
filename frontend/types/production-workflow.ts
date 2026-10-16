import type { ProductionDocument } from "@/types/production-document";

export type WorkflowStage = "PLAN" | "APPROVED_PLAN" | "DOCUMENT";
export type WorkflowStatus = "STARTING" | "SUBMISSION_UNKNOWN" | "queued" | "in_progress" | "completed" | "failed" | "incomplete" | "cancelled" | "validation_failed";
export type WorkflowSummary = {
  artifact_count: number;
  document_count: number;
  updated_at: string | null;
  latest: { ARTIFACT_ID: string; STAGE: WorkflowStage; STATUS: WorkflowStatus; VERSION_NUMBER: number };
};
export type WorkflowArtifactSummary = {
  artifact_id: string;
  production_id: string;
  version_number: number;
  stage: WorkflowStage;
  status: WorkflowStatus;
  response_id: string | null;
  model: string | null;
  corpus_sha256: string;
  parent_artifact_id: string | null;
  created_at: string;
  updated_at: string;
};
export type WorkflowArtifact = WorkflowArtifactSummary & {
  request: { reviewed_plan?: string; plan_artifact_id?: string; imported_document?: ProductionDocument; kind?: string };
  result: {
    id?: string;
    status: string;
    text?: string;
    document?: ProductionDocument | null;
    error?: { message?: string } | null;
    usage?: Record<string, unknown> | null;
    incomplete_details?: Record<string, unknown> | null;
    origin?: string;
  } | null;
};
export type ProductionListItem = {
  production_id: string;
  status: string;
  title: string;
  output_language: "fr" | "en";
  output_format: "AUTONOMOUS_REPORT" | "SPEAKER_PRESENTATION";
  target_page_count: number | null;
  created_at: string;
  updated_at: string;
  corpus_sha256: string;
  workflow?: WorkflowSummary | null;
};
export type ProductionWorkspace = ProductionListItem & {
  corpus: {
    request: { objective: string; target_audience: string; report_ids: string[] };
    reports: { report_id: string; version_number: number; payload: { subject?: string; period_start?: string; period_end?: string } }[];
    counts: { reports: number; unique_contents: number; notes: number; unique_number_ids: number };
  };
};
export const isRunning = (status: string) => ["STARTING", "queued", "in_progress"].includes(status);
export const blocksSubmission = (status: string) => isRunning(status) || status === "SUBMISSION_UNKNOWN";
export const stageLabel = (stage: WorkflowStage) => ({ PLAN: "Plan généré", APPROVED_PLAN: "Plan validé", DOCUMENT: "Rapport" })[stage];
export const statusLabel = (status: string) => ({
  STARTING: "Démarrage", SUBMISSION_UNKNOWN: "Acceptation à vérifier", queued: "En attente",
  in_progress: "En cours", completed: "Enregistré", failed: "Échec", incomplete: "Réponse partielle",
  cancelled: "Annulé", validation_failed: "Contrôles à revoir",
}[status] || status);
