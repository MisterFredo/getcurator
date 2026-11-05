import { api } from "@/lib/api";

export type WatchSourceType = "HTML" | "LINKEDIN" | "NEWSLETTER" | "PDF";
export type WatchSourceRole = "CORPORATE" | "EMPLOYEE";
export type WatchMethod = "MANUAL" | "STUDIO";
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
