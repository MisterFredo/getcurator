import { api } from "@/lib/api";

export type EditionSummary = {
  edition_id: string;
  date: string;
  universe_label: string;
  content_count: number;
};

export type Topic = {
  title: string;
  summary: string;
  relevance_reason?: string;
  id_contents: string[];
};

export type Article = { id_content: string; title: string; source_title?: string | null; source_url?: string | null };
export type Edition = EditionSummary & {
  topics: Topic[];
  contents: Article[];
  preview: { a_retenir: Topic[]; by_the_way: Topic[] };
};

export type DailyJob = {
  job_id: string;
  status: string;
  universes: { universe_id: string; universe_label: string; status: string; error?: string }[];
};

const root = "/editorial";
const jobPath = (id: string) => `${root}/daily-jobs/${encodeURIComponent(id)}`;

export async function startDailyJob(date: string, request_id: string): Promise<DailyJob> {
  return (await api.post(`${root}/daily-jobs`, { date, request_id })).job;
}

export async function readDailyJob(id: string): Promise<DailyJob> {
  return (await api.get(jobPath(id))).job;
}

export async function refreshDailyJob(id: string): Promise<DailyJob> {
  return (await api.post(`${jobPath(id)}/refresh`, {})).job;
}

export async function listDailyEditions(date: string): Promise<EditionSummary[]> {
  return (await api.get(`${root}/daily-editions?date=${encodeURIComponent(date)}`)).editions;
}

export async function readDailyEdition(id: string): Promise<Edition> {
  return (await api.get(`${root}/daily-editions/${encodeURIComponent(id)}`)).edition;
}
