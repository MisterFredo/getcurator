import { api } from "@/lib/api";
import type { WorkflowArtifact, WorkflowArtifactSummary, ProductionListItem, ProductionWorkspace } from "@/types/production-workflow";
import type { ProductionDocument } from "@/types/production-document";
const root = (id: string) => `/production/${encodeURIComponent(id)}/workflow`;
export async function browseProductions(offset = 0): Promise<ProductionListItem[]> {
  const res = await api.get(`/production/?limit=100&offset=${offset}`);
  return res.productions;
}
export async function readProduction(id: string): Promise<ProductionWorkspace> {
  return (await api.get(`/production/${encodeURIComponent(id)}`)).production;
}
export async function browseArtifacts(id: string, offset = 0): Promise<WorkflowArtifactSummary[]> {
  return (await api.get(`${root(id)}?limit=100&offset=${offset}`)).artifacts;
}
export async function readArtifact(id: string, artifact: string): Promise<WorkflowArtifact> {
  return (await api.get(`${root(id)}/artifacts/${encodeURIComponent(artifact)}`)).artifact;
}
export async function startPlan(id: string, requestId: string): Promise<WorkflowArtifact> {
  return (await api.post(`${root(id)}/plan-jobs`, { request_id: requestId })).artifact;
}
export async function saveReviewedPlan(id: string, requestId: string, text: string, parent: string | null): Promise<WorkflowArtifact> {
  return (await api.post(`${root(id)}/approved-plans`, {
    request_id: requestId, reviewed_plan: text, parent_artifact_id: parent,
  })).artifact;
}
export async function startDocument(id: string, requestId: string, planId: string): Promise<WorkflowArtifact> {
  return (await api.post(`${root(id)}/document-jobs`, { request_id: requestId, plan_artifact_id: planId })).artifact;
}
export async function importDocument(id: string, requestId: string, document: ProductionDocument, planId: string | null): Promise<WorkflowArtifact> {
  return (await api.post(`${root(id)}/import-document`, { request_id: requestId, document, plan_artifact_id: planId })).artifact;
}
export async function refreshArtifact(id: string, artifact: string, responseId?: string): Promise<WorkflowArtifact> {
  return (await api.post(`${root(id)}/artifacts/${encodeURIComponent(artifact)}/refresh`, {
    response_id: responseId || null,
  })).artifact;
}
