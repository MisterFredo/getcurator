"use client";

import { useEffect, useRef, useState } from "react";
import Link from "next/link";
import { useUser } from "@/hooks/useUser";
import { browseKnowledge, getKnowledgeFilters, getKnowledgeReport, searchKnowledge } from "@/lib/knowledge";
import KnowledgeReportDocument from "@/components/knowledge/KnowledgeReportDocument";
import type {
  KnowledgeAvailableFilters, KnowledgeCatalogue, KnowledgeFilters,
  KnowledgeMessage, KnowledgeReport, KnowledgeSummary,
} from "@/types/knowledge";

const EMPTY_FILTERS: KnowledgeFilters = {expert_id: null, month: null, output_language: null};
const EMPTY_CATALOGUE: KnowledgeCatalogue = {items: [], pagination: {total: 0, limit: 20, offset: 0, has_more: false}};
const inputClass = "rounded-lg border border-gray-200 bg-white px-3 py-2 text-sm";
const buttonClass = "rounded-lg border border-gray-200 bg-white px-4 py-2 text-sm disabled:opacity-50";

function reportPeriod(value: string | null) {
  if (!value) return "";
  const date = new Date(value);
  return Number.isNaN(date.getTime()) ? "" : new Intl.DateTimeFormat("en-GB", {month: "long", year: "numeric", timeZone: "UTC"}).format(date);
}

export default function KnowledgePage() {
  const {user, loading: userLoading} = useUser();
  const [filters, setFilters] = useState<KnowledgeFilters>(EMPTY_FILTERS);
  const [available, setAvailable] = useState<KnowledgeAvailableFilters>({experts: [], months: [], languages: []});
  const [query, setQuery] = useState("");
  const [submittedQuery, setSubmittedQuery] = useState("");
  const [offset, setOffset] = useState(0);
  const [catalogue, setCatalogue] = useState<KnowledgeCatalogue>(EMPTY_CATALOGUE);
  const [matches, setMatches] = useState<KnowledgeSummary[] | null>(null);
  const [conversation, setConversation] = useState<KnowledgeMessage[]>([]);
  const [message, setMessage] = useState("");
  const [moreMatches, setMoreMatches] = useState(false);
  const [reportExpertName, setReportExpertName] = useState<string | null>(null);
  const [report, setReport] = useState<KnowledgeReport | null>(null);
  const [loading, setLoading] = useState(false);
  const [searching, setSearching] = useState(false);
  const [opening, setOpening] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const requestVersion = useRef(0);
  const userId = user?.user_id;

  useEffect(() => {
    if (!userId) return;
    let active = true;
    getKnowledgeFilters().then(value => {if (active) setAvailable(value);}).catch(() => {
      if (active) setError("Unable to load report filters. Refresh the page to try again.");
    });
    return () => {active = false;};
  }, [userId]);

  useEffect(() => {
    if (!userId) return;
    const version = ++requestVersion.current;
    setLoading(true);
    setError(null);
    browseKnowledge(submittedQuery, filters, offset).then(value => {
      if (version === requestVersion.current) setCatalogue(value);
    }).catch(exception => {
      if (version === requestVersion.current) setError(exception instanceof Error ? exception.message : "Unable to load reports.");
    }).finally(() => {if (version === requestVersion.current) setLoading(false);});
    return () => {requestVersion.current += 1;};
  }, [userId, submittedQuery, filters, offset]);

  function changeFilters(next: KnowledgeFilters) {
    setFilters(next); setOffset(0); setMatches(null); setConversation([]); setMoreMatches(false);
  }
  async function discover() {
    if (!message.trim() || searching) return;
    const text = message.trim();
    setSearching(true); setError(null);
    try {
      const result = await searchKnowledge(text, conversation, filters);
      setConversation(current => [...current, {role: "user", content: text}, {role: "assistant", content: result.assistant_message}].slice(-12) as KnowledgeMessage[]);
      setMatches(result.items); setMoreMatches(result.has_more); setMessage("");
    } catch (exception) {
      setError(exception instanceof Error ? exception.message : "Unable to find reports.");
    } finally {setSearching(false);}
  }
  async function openReport(id: string) {
    setOpening(true); setError(null);
    try {
      const savedReport = await getKnowledgeReport(id);
      const summary = (matches ?? catalogue.items).find(item => item.report_id === id);
      let expertName = summary?.expert_name?.trim() || available.experts.find(expert => expert.expert_id === savedReport.expert_id)?.label.trim() || null;
      if (savedReport.report_type === "MONTHLY" && savedReport.expert_id && !expertName) {
        const refreshedFilters = await getKnowledgeFilters();
        setAvailable(refreshedFilters);
        expertName = refreshedFilters.experts.find(expert => expert.expert_id === savedReport.expert_id)?.label.trim() || null;
        if (!expertName) throw new Error("The expert name is unavailable. Refresh the page and try again.");
      }
      setReportExpertName(expertName);
      setReport(savedReport);
    }
    catch (exception) {setError(exception instanceof Error ? exception.message : "Unable to open report.");}
    finally {setOpening(false);}
  }
  if (userLoading) return <p className="p-6 text-sm text-gray-500">Loading…</p>;
  if (!userId) return <div className="space-y-3"><h1 className="text-2xl font-semibold">Knowledge</h1><p>Sign in to explore the reports.</p><Link href="/login" className="text-emerald-700 underline">Sign in</Link></div>;
  if (report) return <div className="space-y-4">
    <button type="button" className={buttonClass} onClick={() => {setReport(null); setReportExpertName(null);}}>← Back to reports</button>
    <KnowledgeReportDocument reportType={report.report_type ?? "RESEARCH"} expertName={reportExpertName} notebook={report.notebook} periodStart={report.period_start} periodEnd={report.period_end}
      outputLanguage={report.output_language} sources={report.sources.map(source => ({content_id: source.content_id,
        title: source.title ?? source.original_title ?? "Untitled source", source_title: source.source_name ?? "",
        source_url: /^https?:\/\//i.test(source.url ?? "") ? source.url! : "", published_at: source.published_at}))} />
  </div>;
  const items = matches ?? catalogue.items;
  return <div className="space-y-4">
    <header><h1 className="text-2xl font-semibold text-gray-900">Knowledge</h1>
      <p className="mt-1 text-sm text-gray-500">Find and explore GetCurator’s published research reports.</p></header>
    <section className="space-y-3 rounded-xl border bg-white p-4">
      <form onSubmit={event => {event.preventDefault(); setMatches(null); setConversation([]); setOffset(0); setSubmittedQuery(query.trim());}} className="flex flex-wrap gap-2">
        <input className={`${inputClass} min-w-0 flex-1`} value={query} onChange={event => setQuery(event.target.value)} aria-label="Search reports" placeholder="Search report titles and content…" disabled={searching} />
        <button type="submit" className={buttonClass} disabled={searching}>Search</button>
      </form>
      <div className="flex flex-wrap gap-3">
        <select className={inputClass} aria-label="Expertise" disabled={searching} value={filters.expert_id ?? ""} onChange={event => changeFilters({...filters, expert_id: event.target.value || null})}>
          <option value="">All expertise</option>{available.experts.map(expert => <option key={expert.expert_id} value={expert.expert_id}>{expert.label}</option>)}
        </select>
        <select className={inputClass} aria-label="Period" disabled={searching} value={filters.month ?? ""} onChange={event => changeFilters({...filters, month: event.target.value || null})}>
          <option value="">All periods</option>{available.months.map(month => <option key={month} value={month}>{month}</option>)}
        </select>
        <select className={inputClass} aria-label="Report language" disabled={searching} value={filters.output_language ?? ""} onChange={event => changeFilters({...filters, output_language: (event.target.value || null) as KnowledgeFilters["output_language"]})}>
          <option value="">All languages</option>{available.languages.filter(language => language === "fr" || language === "en").map(language => <option key={language} value={language}>{language.toUpperCase()}</option>)}
        </select>
        <button type="button" disabled={searching} className={buttonClass} onClick={() => {changeFilters(EMPTY_FILTERS); setQuery(""); setSubmittedQuery("");}}>Reset</button>
      </div>
    </section>
    <div className="grid items-start gap-6 xl:grid-cols-[minmax(0,1fr)_340px]">
      <section className="min-w-0 space-y-3" aria-live="polite">
        <div className="flex items-center justify-between gap-2"><h2 className="font-semibold">{matches ? "Reports connected to your request" : "Reports"}</h2>
          {!matches && !loading && <span className="text-sm text-gray-500">{catalogue.pagination.total} reports</span>}</div>
        {error && <p role="alert" className="rounded-lg bg-red-50 p-4 text-sm text-red-700">{error}</p>}
        {(loading && matches === null || searching || opening) && <p role="status" className="text-sm text-gray-500">{searching ? "Finding relevant reports…" : opening ? "Opening report…" : "Loading reports…"}</p>}
        {!(loading && matches === null) && !searching && items.length === 0 && <p className="rounded-xl border bg-white p-6 text-sm text-gray-500">No matching reports. Try another subject or adjust the filters.</p>}
        {!(loading && matches === null) && !searching && items.map(item => {
          const isMonthly = item.report_type === "MONTHLY";
          const theme = isMonthly
            ? {border: "border-emerald-100", hover: "hover:border-emerald-300", tint: "bg-emerald-50", text: "text-emerald-800", accent: "text-emerald-700", button: "bg-emerald-700"}
            : {border: "border-blue-100", hover: "hover:border-blue-300", tint: "bg-blue-50", text: "text-blue-800", accent: "text-blue-700", button: "bg-blue-700"};
          return <article key={item.report_id} className={`overflow-hidden rounded-2xl border ${theme.border} bg-white shadow-sm transition ${theme.hover} hover:shadow-md`}>
          <div className={`grid gap-3 border-b ${theme.border} ${theme.tint} px-4 py-3 lg:grid-cols-[minmax(0,1fr)_auto] lg:items-center lg:gap-6`}>
            <div className="min-w-0 space-y-1">
              <p className={`text-[11px] font-semibold uppercase tracking-wide ${theme.accent}`}>{isMonthly ? "Monthly edition" : "Research report"} · {item.output_language.toUpperCase()}</p>
              <h3 className="text-base font-bold leading-snug text-gray-900">{isMonthly ? item.expert_name || item.subject : item.subject}</h3>
              <p className={`text-xs font-medium ${theme.text}`}>{reportPeriod(item.period_start) || `Published ${new Date(item.published_at).toLocaleDateString("en-GB")}`}</p>
            </div>
            <div className={`border-t ${theme.border} pt-2 lg:border-l lg:border-t-0 lg:pl-5 lg:pt-0`}>
              <p className={`mb-1 text-[10px] font-semibold uppercase tracking-wide ${theme.accent}`}>The research, done for you</p>
              <dl className="flex flex-wrap gap-x-5 gap-y-2">
                {item.candidate_count != null && <div><dt className="text-[11px] text-gray-600">Candidates reviewed</dt><dd className="text-lg font-bold leading-6 text-gray-900">{item.candidate_count}</dd></div>}
                <div><dt className="text-[11px] text-gray-600">Sources selected</dt><dd className={`text-lg font-bold leading-6 ${theme.accent}`}>{item.source_count}</dd></div>
                {item.note_count != null && <div><dt className="text-[11px] text-gray-600">Insights extracted</dt><dd className="text-lg font-bold leading-6 text-gray-900">{item.note_count}</dd></div>}
              </dl>
            </div>
          </div>
          <div className="space-y-2 px-4 py-3">
          {item.match_reason && <div className={`rounded-lg ${theme.tint} p-2.5 text-xs leading-5 text-emerald-900`}>
            <p className="mb-1 text-xs font-semibold">{item.match_type === "PARTIAL" ? "Partial match" : "Direct match"}</p><p>{item.match_reason}</p>
            {item.match_evidence && <blockquote className="mt-1 border-l-2 border-emerald-200 pl-3 text-xs">{item.match_evidence.text}</blockquote>}
          </div>}
          {(item.summary || item.objective || item.key_points.length > 0) && <details className="group">
            <summary className={`cursor-pointer text-xs font-medium ${theme.accent} hover:underline`}>
              <span className="group-open:hidden">Show more</span>
              <span className="hidden group-open:inline">Show less</span>
            </summary>
            <div className="mt-2 space-y-2">
              {(item.summary || item.objective) && <p className="text-xs leading-5 text-gray-600">{item.summary || item.objective}</p>}
              {item.key_points.length > 0 && <ul className="list-disc space-y-1 pl-5 text-xs text-gray-600">{item.key_points.map((point,index) => <li key={index}>{point}</li>)}</ul>}
            </div>
          </details>}
          <button type="button" className={`rounded-lg ${theme.button} px-3 py-1.5 text-xs text-white disabled:opacity-50`} disabled={opening || searching} onClick={() => void openReport(item.report_id)}>Explore this report →</button>
          </div>
        </article>;
        })}
        {matches && moreMatches && <p className="text-xs text-gray-500">Additional reports matched the search terms. Refine your request to explore them.</p>}
        {matches === null && !loading && <div className="flex items-center justify-between">
          <button type="button" className={buttonClass} disabled={offset === 0 || searching} onClick={() => setOffset(Math.max(0, offset-20))}>Previous</button>
          <button type="button" className={buttonClass} disabled={!catalogue.pagination.has_more || searching} onClick={() => setOffset(offset+20)}>Next</button>
        </div>}
      </section>
      <aside className="space-y-3 rounded-xl border bg-white p-4 xl:sticky xl:top-0">
        <div><h2 className="font-semibold">Which reports are you looking for?</h2><p className="mt-1 text-sm text-gray-500">Describe a subject, actor or market to find related reports.</p></div>
        <div className="max-h-[40vh] space-y-3 overflow-y-auto" aria-live="polite">
          {conversation.map((entry,index) => <p key={index} className={`rounded-lg p-3 text-sm ${entry.role === "user" ? "bg-gray-100 text-gray-900" : "bg-emerald-50 text-emerald-900"}`}>{entry.content}</p>)}
        </div>
        <form onSubmit={event => {event.preventDefault(); void discover();}} className="space-y-3">
          <textarea aria-label="Describe the reports you need" maxLength={2000} rows={4} className={`${inputClass} w-full`} value={message} onChange={event => setMessage(event.target.value)} placeholder="Reports on retail media measurement for brands…" disabled={searching} />
          <button type="submit" className="w-full rounded-lg bg-emerald-700 px-3 py-1.5 text-xs text-white disabled:opacity-50" disabled={searching || !message.trim()}>{searching ? "Searching…" : "Find reports"}</button>
        </form>
        {matches !== null && <button type="button" disabled={searching} className="text-sm text-emerald-700 underline" onClick={() => {setMatches(null); setConversation([]); setMessage(""); setMoreMatches(false);}}>Back to catalogue</button>}
      </aside>
    </div>
  </div>;
}
