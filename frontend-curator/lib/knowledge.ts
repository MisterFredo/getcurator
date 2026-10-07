import { api } from "@/lib/api";
import type {
  KnowledgeAvailableFilters, KnowledgeCatalogue, KnowledgeFilters,
  KnowledgeMessage, KnowledgeReport, KnowledgeSearch,
} from "@/types/knowledge";

export async function browseKnowledge(query: string, filters: KnowledgeFilters, offset = 0): Promise<KnowledgeCatalogue> {
  const params = new URLSearchParams({query, limit: "20", offset: String(offset)});
  for (const [key, value] of Object.entries(filters)) if (value) params.set(key, value);
  return api.get(`/touch/library/reports?${params.toString()}`);
}
export async function getKnowledgeFilters(): Promise<KnowledgeAvailableFilters> {
  return (await api.get("/touch/library/filters")).filters;
}
export async function getKnowledgeReport(reportId: string): Promise<KnowledgeReport> {
  return (await api.get(`/touch/library/reports/${encodeURIComponent(reportId)}`)).report;
}
export async function searchKnowledge(message: string, history: KnowledgeMessage[], filters: KnowledgeFilters): Promise<KnowledgeSearch> {
  return (await api.post("/touch/library/search", {message, history: history.slice(-12), filters, language: "en"})).search;
}
