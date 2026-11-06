import { api } from "@/lib/api";

export type WatchSourceType = "HTML" | "LINKEDIN" | "NEWSLETTER" | "PDF";
export type WatchSourceRole = "CORPORATE" | "EMPLOYEE";
export type WatchMethod = "MANUAL" | "STUDIO" | "HTML";
export type WatchPayload = {
  label: string;
  source_type: WatchSourceType;
  source_url: string;
  source_role: WatchSourceRole;
  author_name: string | null;
  collection_method: WatchMethod;
  collection_config: Record<string, unknown>;
  is_active: boolean;
};
export type CompanyWatch = WatchPayload & {
  id_company_watch: string;
  id_company: string;
  company_name?: string | null;
  created_at: string;
  updated_at: string;
};
export type WatchCompany = {
  id_company: string;
  name: string;
  website_url?: string | null;
  linkedin_url?: string | null;
};
export type WatchList = {
  status: string;
  watches: CompanyWatch[];
  has_more: boolean;
  limit: number;
  offset: number;
};
export async function listWatchCompanies(): Promise<WatchCompany[]> {
  const response = await api.get("/company/list");
  return response.companies || [];
}
export async function listCompanyWatches(options: {
  id_company?: string;
  is_active?: boolean;
  offset?: number;
  limit?: number;
}): Promise<WatchList> {
  const query = new URLSearchParams();
  if (options.id_company) query.set("id_company", options.id_company);
  if (options.is_active !== undefined) query.set("is_active", String(options.is_active));
  query.set("offset", String(options.offset ?? 0));
  query.set("limit", String(options.limit ?? 50));
  return api.get(`/company/watch/list?${query.toString()}`);
}
export async function createCompanyWatch(companyId: string, payload: WatchPayload): Promise<CompanyWatch> {
  return api.post(`/company/${encodeURIComponent(companyId)}/watch`, payload);
}
export async function updateCompanyWatch(
  companyId: string, watchId: string, payload: Partial<WatchPayload>,
): Promise<CompanyWatch> {
  return api.put(`/company/${encodeURIComponent(companyId)}/watch/${encodeURIComponent(watchId)}`, payload);
}

export type WatchPublication = {
  id_document: string;
  title: string;
  source_url?: string;
  status?: string;
  extraction_status?: string;
  extraction_error?: string | null;
  next_chunk: number;
  chunk_count: number;
  already_exists?: boolean;
  unit_count?: number;
  review_count?: number;
};
export type WatchEvidence = {
  unit_id: string; fact: string; quote: string; verification_status: string;
  verification_reason?: string; source_locator?: string;
};
export type WatchDetail = WatchPublication & { text: string; units: WatchEvidence[]; has_more: boolean; warning: string };
function watchPath(watch: CompanyWatch) {
  return `/company/${encodeURIComponent(watch.id_company)}/watch/${encodeURIComponent(watch.id_company_watch)}`;
}
export async function scanWatch(watch: CompanyWatch): Promise<{
  items: {url: string; title?: string}[]; warnings: string[]; pages_scanned: number;
}> { return api.post(`${watchPath(watch)}/scan`, {}); }
export async function collectWatchUrl(watch: CompanyWatch, url: string): Promise<WatchPublication> {
  return api.post(`${watchPath(watch)}/collect`, { url });
}
export async function extractWatchStep(watch: CompanyWatch, id: string): Promise<WatchPublication> {
  return api.post(`${watchPath(watch)}/publications/${encodeURIComponent(id)}/extract-step`, {});
}
export async function importWatchText(watch: CompanyWatch, data: {
  text: string; format: "SINGLE" | "LINKEDIN_ACTIVITY"; title?: string; source_url?: string;
  reference_date?: string; published_date?: string;
}): Promise<{items: WatchPublication[]; errors: {index: number; error: string}[]; warnings: string[]}> {
  return api.post(`${watchPath(watch)}/import-text`, data);
}
export async function listWatchPublications(watch: CompanyWatch, offset=0): Promise<{
  items: WatchPublication[]; has_more: boolean;
}> { return api.get(`${watchPath(watch)}/publications?offset=${offset}&limit=50`); }
export async function getWatchPublication(watch: CompanyWatch, id: string, offset=0): Promise<WatchDetail> {
  return api.get(`${watchPath(watch)}/publications/${encodeURIComponent(id)}?offset=${offset}&limit=100`);
}

