import { api } from "@/lib/api";

export type WatchSourceType = "HTML" | "LINKEDIN" | "NEWSLETTER" | "PDF";
export type WatchSourceRole = "CORPORATE" | "EMPLOYEE";
export type WatchMethod = "MANUAL" | "STUDIO" | "HTML" | "BRIGHTDATA";
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
  id_contact?: string | null;
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


export type CorpoDiscovery = {
  id_discovery: string; id_company: string; id_company_watch: string;
  company_name?: string; watch_label?: string;
  url: string; title?: string; change_type: "NEW_URL" | "NEW_PAGE" | "UPDATED_PAGE";
  status: "NEW" | "STORED" | "DISMISSED"; error?: string; date_found?: string; id_stock?: string;
  published_at?: string | null; publication_date_note?: string | null;
  watch_active?: boolean; collection_method?: string;
  library_status?: "PENDING" | "IMPORTING" | "IMPORTED" | "ERROR"; id_document?: string | null;
};
export type CorpoScanResult = {
  status: "ok" | "IDLE" | "STARTING" | "RUNNING" | "UNKNOWN" | "COMPLETE" | "FAILED";
  new: number; known: number; unchanged: number; warnings: string[];
  snapshot_id?: string; message?: string; received?: number;
};
export async function getCorpoScanStatus(watch: CompanyWatch): Promise<CorpoScanResult> {
  return api.get(`/company/${encodeURIComponent(watch.id_company)}/watch/${encodeURIComponent(watch.id_company_watch)}/scan/status`);
}
export async function attachCorpoSnapshot(watch: CompanyWatch, snapshotId: string): Promise<CorpoScanResult> {
  return api.post(`/company/${encodeURIComponent(watch.id_company)}/watch/${encodeURIComponent(watch.id_company_watch)}/scan/attach`, {snapshot_id: snapshotId});
}
export async function scanCorpoSource(watch: CompanyWatch): Promise<CorpoScanResult> {
  return api.post(`/company/${encodeURIComponent(watch.id_company)}/watch/${encodeURIComponent(watch.id_company_watch)}/scan`, {});
}
export async function listCorpoDiscovery(options: {
  companyId?: string; watchId?: string; status?: string; offset?: number;
}): Promise<{items: CorpoDiscovery[]; has_more: boolean}> {
  const query = new URLSearchParams({status: options.status || "NEW", offset: String(options.offset || 0), limit:"50"});
  if (options.companyId) query.set("id_company",options.companyId);
  if (options.watchId) query.set("id_company_watch",options.watchId);
  return api.get(`/company/watch/discovery/list?${query}`);
}
export async function storeCorpoDiscovery(id: string): Promise<{id_stock: string; already_exists: boolean}> {
  return api.post(`/company/watch/discovery/${encodeURIComponent(id)}/store`, {});
}
export async function changeCorpoDiscoveryStatus(ids: string[], action: "dismiss" | "restore"): Promise<{
  requested: number; updated: number; skipped: number;
}> {
  return api.post(`/company/watch/discovery/${action}`, {discovery_ids: ids});
}
export async function getCorpoStoredContent(id: string): Promise<{
  title: string; text: string; url: string; captured_at: string;
  published_at?: string | null; author_name?: string | null; author_id?: string | null;
  monitored_account_url?: string | null; repost?: Record<string, unknown> | null; share_date?: string | null;
}> {
  return api.get(`/company/watch/discovery/${encodeURIComponent(id)}/content`);
}


export type LibraryImportResult = {
  id_document: string; library_status: "IMPORTING" | "IMPORTED";
  next_chunk: number; chunk_count: number;
};
export async function importCorpoLibraryStep(id: string): Promise<LibraryImportResult> {
  return api.post(`/company/watch/discovery/${encodeURIComponent(id)}/library-step`, {});
}
export type CorpoLibraryDocument = {
  id_document: string; document_type?: string; title: string; source_url: string; published_at?: string;
  company_name?: string; watch_label?: string; author_name?: string;
  extraction_status: string; extraction_error?: string; unit_count: number;
  next_chunk: number; chunk_count: number; id_company: string; id_company_watch: string | null;
};
export type CorpoLibraryUnit = {
  unit_id: string; fact: string; quote: string; verification_status: string;
  source_locator?: string; verification_reason?: string; kind?: string;
};
export type CorpoLibraryDetail = {
  id_document: string; title: string; source_url: string; text: string;
  published_at?: string; author_name?: string; author_id?: string;
  monitored_account_url?: string; status: string; units: CorpoLibraryUnit[];
  has_more: boolean; warning: string;
};
export type CorpoLibraryFilters = {
  q?: string; companyId?: string; sort?: string; direction?: string;
  status?: string; publishedFrom?: string; publishedTo?: string; documentType?: string;
};
export async function listCorpoLibrary(offset = 0, filters: CorpoLibraryFilters = {}): Promise<{items: CorpoLibraryDocument[];has_more: boolean}> {
  const params = new URLSearchParams({offset:String(offset),limit:"50"});
  const entries = {q:filters.q, id_company:filters.companyId, sort:filters.sort,
    document_type:filters.documentType, direction:filters.direction, status:filters.status, published_from:filters.publishedFrom, published_to:filters.publishedTo};
  Object.entries(entries).forEach(([key,value])=>{if(value)params.set(key,value);});
  return api.get(`/company/watch/library/list?${params.toString()}`);
}
export async function getCorpoLibraryDocument(id: string, offset = 0): Promise<CorpoLibraryDetail> {
  return api.get(`/company/watch/library/${encodeURIComponent(id)}?offset=${offset}&limit=100`);
}
