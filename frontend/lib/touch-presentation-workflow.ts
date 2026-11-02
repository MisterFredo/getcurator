import { api } from "@/lib/api";
import type { ProductionDocument } from "@/types/production-document";
export type TouchPresentationJob = {
  artifact_id: string; report_id: string; report_version: number; version_number: number;
  status: string; response_id?: string | null; model?: string | null;
  created_at: string; updated_at: string;
  result?: { export_context?: { subject: string; output_language: string; period_start: string | null; period_end: string | null }; document?: ProductionDocument | null; text?: string;
    error?: { message?: string } | null; section_coverage?: {
      section_id: string; page_ids: string[]; omitted_details: string;
    }[]; validation_notes?: string[] };
};
export const activePresentation = (status: string) => ["STARTING", "SUBMISSION_UNKNOWN", "queued", "in_progress"].includes(status);
const base = (id: string) => `/touch/reports/${encodeURIComponent(id)}/presentations`;
export async function listTouchPresentations(id: string, offset = 0): Promise<TouchPresentationJob[]> {
  return (await api.get(`${base(id)}?limit=30&offset=${offset}`)).presentations;
}
export async function readTouchPresentation(id: string, artifact: string): Promise<TouchPresentationJob> {
  return (await api.get(`${base(id)}/${encodeURIComponent(artifact)}`)).presentation;
}
export async function startTouchPresentation(id: string, artifact: string, version: number): Promise<TouchPresentationJob> {
  return (await api.post(base(id), { artifact_id: artifact, expected_version: version })).presentation;
}
export async function refreshTouchPresentation(id: string, artifact: string, responseId?: string): Promise<TouchPresentationJob> {
  return (await api.post(`${base(id)}/${encodeURIComponent(artifact)}/refresh`, { response_id: responseId || null })).presentation;
}
