"use client";

import { useEffect, useMemo, useState } from "react";
import Link from "next/link";
import { api } from "@/lib/api";
import { deleteTouchEdition } from "@/lib/touch";
import type { TouchSavedReportSummary } from "@/types/touch";

/* The existing component now renders the unified reports list. */
type Edition = {
  archived_at?: string | null;
  edition_id: string;
  expert_id: string;
  period_start: string;
  period_end: string;
  status: string;
  subject: string;
  output_language: string;
  report_id: string | null;
  error: string | null;
  selected_count: number;
  candidate_count?: number | null;
  proposed_count?: number | null;
};
type SavedReport = TouchSavedReportSummary & { archived_at?: string | null; output_language?: string };
type Row = {
  key: string;
  type: "MONTHLY" | "STANDALONE";
  subject: string;
  expertId: string | null;
  period: string;
  status: string;
  reportId: string | null;
  edition: Edition | null;
  report: SavedReport | null;
};
type Props = {
  onOpenReport: (reportId: string) => Promise<void>;
  disabled?: boolean;
  refreshKey?: number;
  onChanged?: () => void;
};
const STATUS_LABELS: Record<string, string> = {
  BUILDING: "Preparing", TO_REVIEW: "To review", GENERATED: "Generated",
  ERROR: "Preparation failed", ARCHIVED: "Archived",
};

export default function TouchMonthlyEditionList({
  onOpenReport, disabled = false, refreshKey = 0, onChanged,
}: Props) {
  const [editions, setEditions] = useState<Edition[]>([]);
  const [reports, setReports] = useState<SavedReport[]>([]);
  const [expertNames, setExpertNames] = useState<Record<string, string>>({});
  const [expertFilter, setExpertFilter] = useState("");
  const [statusFilter, setStatusFilter] = useState("ACTIVE");
  const [periodFilter, setPeriodFilter] = useState("");
  const [typeFilter, setTypeFilter] = useState("");
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [busyKey, setBusyKey] = useState<string | null>(null);
  const [reload, setReload] = useState(0);

  useEffect(() => {
    let active = true;
    setLoading(true);
    setError(null);
    async function load() {
      const results = await Promise.allSettled([
        api.get("/touch/editions?limit=200"),
        api.get("/touch/reports?archive=all"),
        api.get("/user/admin/experts"),
      ]);
      if (!active) return;
      // Commit both lists together: partial data cannot reliably deduplicate.
      if (results[0].status === "fulfilled" && results[1].status === "fulfilled") {
        setEditions(results[0].value.editions ?? []);
        setReports(results[1].value.reports ?? []);
      } else {
        const failed = results.find(result => result.status === "rejected");
        setError(failed?.status === "rejected" && failed.reason instanceof Error
          ? failed.reason.message : "Unable to load reports and editions.");
      }
      if (results[2].status === "fulfilled") {
        const names: Record<string, string> = {};
        for (const expert of results[2].value.experts ?? []) {
          const id = expert.ID_USER ?? expert.id_user ?? expert.user_id ?? expert.id;
          if (id) names[id] = expert.DISPLAY_NAME ?? expert.display_name ?? expert.NAME ?? expert.name ?? id;
        }
        setExpertNames(names);
      }
      setLoading(false);
    }
    void load();
    return () => { active = false; };
  }, [reload, refreshKey]);

  const rows = useMemo<Row[]>(() => {
    const reportsById = new Map(reports.map(report => [report.report_id, report]));
    // Deduplicate before filtering, using the actual relationship, never titles.
    const linkedIds = new Set(editions.map(edition => edition.report_id).filter(Boolean));
    const monthly: Row[] = editions.map(edition => {
      const report = edition.report_id ? reportsById.get(edition.report_id) ?? null : null;
      return {
        key: `edition:${edition.edition_id}`, type: "MONTHLY",
        subject: edition.subject, expertId: edition.expert_id,
        period: edition.period_start.slice(0, 7),
        status: edition.archived_at || report?.archived_at ? "ARCHIVED" : edition.status,
        reportId: edition.report_id, edition, report,
      };
    });
    const standalone: Row[] = reports.filter(report => !linkedIds.has(report.report_id)).map(report => ({
      key: `report:${report.report_id}`, type: "STANDALONE",
      subject: report.subject, expertId: report.expert_id ?? null,
      period: report.period_start?.slice(0, 7) ?? "",
      status: report.archived_at ? "ARCHIVED" : "GENERATED",
      reportId: report.report_id, edition: null, report,
    }));
    return [...monthly, ...standalone].sort((a, b) =>
      b.period.localeCompare(a.period) || a.subject.localeCompare(b.subject) || a.key.localeCompare(b.key));
  }, [editions, reports]);
  const expertIds = useMemo(() => Array.from(new Set(rows.map(row => row.expertId)
    .filter((id): id is string => !!id))).sort((a, b) =>
      (expertNames[a] ?? a).localeCompare(expertNames[b] ?? b)), [rows, expertNames]);
  const periods = useMemo(() => Array.from(new Set(rows.map(row => row.period).filter(Boolean)))
    .sort((a, b) => b.localeCompare(a)), [rows]);
  const visible = useMemo(() => rows.filter(row =>
    (!expertFilter || (expertFilter === "NO_EXPERT" ? !row.expertId : row.expertId === expertFilter))
    && (!periodFilter || (periodFilter === "NO_PERIOD" ? !row.period : row.period === periodFilter))
    && (!typeFilter || row.type === typeFilter)
    && (!statusFilter || (statusFilter === "ACTIVE" ? row.status !== "ARCHIVED" : row.status === statusFilter))),
  [rows, expertFilter, periodFilter, typeFilter, statusFilter]);

  function refreshAfterChange() {
    setReload(value => value + 1);
    onChanged?.();
  }
  async function manage(row: Row, action: "archive" | "restore" | "delete" | "reopen" | "reset") {
    if (disabled || busyKey || loading) return;
    if (action === "reset" && (!row.edition || row.edition.status === "BUILDING")) return;
    if (action === "delete" && !window.confirm(`Delete “${row.subject}”? This action cannot be undone.`
      + (row.edition ? " The selected corpus will be preserved for regeneration." : ""))) return;
    if (action === "reopen" && !window.confirm("Reopen the selected corpus? The current report will be kept in archives.")) return;
    if (action === "reset" && !window.confirm(`Reset “${row.subject}”? This will permanently delete the monthly corpus, all source selections and the linked report, if any. Previously archived reports will be preserved. Prepare this edition again to use the current expert profile.`)) return;
    setBusyKey(row.key);
    setError(null);
    try {
      if (action === "reset" && row.edition) {
        await deleteTouchEdition(row.edition.edition_id);
      } else if (action === "reopen" && row.edition) {
        await api.post(`/touch/editions/${encodeURIComponent(row.edition.edition_id)}/reopen`, {});
        window.location.assign(`/admin/touch?edition_id=${encodeURIComponent(row.edition.edition_id)}`);
        return;
      } else if (row.reportId) {
        const path = `/touch/reports/${encodeURIComponent(row.reportId)}`;
        if (action === "delete") await api.delete(path);
        else await api.post(`${path}/${action}`, {});
      } else {
        throw new Error("This entry has no saved report.");
      }
      refreshAfterChange();
    } catch (exception) {
      setError(exception instanceof Error ? exception.message : "Unable to update report.");
    } finally {
      setBusyKey(null);
    }
  }
  const interactionsDisabled = disabled || busyKey !== null || loading;
  const selectClass = "rounded-lg border px-3 py-2 text-sm";
  const buttonClass = "rounded-lg border px-3 py-2 text-sm disabled:cursor-not-allowed disabled:opacity-50";

  return (
    <section className="space-y-4 rounded-xl border border-gray-200 bg-white p-5">
      <div className="flex flex-wrap items-start justify-between gap-3">
        <div>
          <h2 className="text-lg font-semibold text-gray-900">Reports and corpora</h2>
          <p className="mt-1 text-sm text-gray-500">Monthly editions and standalone reports, including previous archived reports.</p>
        </div>
        <button type="button" disabled={interactionsDisabled} onClick={() => setReload(value => value + 1)} className={buttonClass}>Refresh</button>
      </div>
      <div className="flex flex-wrap gap-3">
        <select aria-label="Filter by status" value={statusFilter} onChange={event => setStatusFilter(event.target.value)} className={selectClass}>
          <option value="ACTIVE">All active statuses</option><option value="">All statuses, including archives</option>
          {Object.entries(STATUS_LABELS).map(([status, label]) => <option key={status} value={status}>{label}</option>)}
        </select>
        <select aria-label="Filter by expert" value={expertFilter} onChange={event => setExpertFilter(event.target.value)} className={selectClass}>
          <option value="">All experts</option><option value="NO_EXPERT">Without an expert</option>
          {expertIds.map(id => <option key={id} value={id}>{expertNames[id] ?? id}</option>)}
        </select>
        <select aria-label="Filter by period" value={periodFilter} onChange={event => setPeriodFilter(event.target.value)} className={selectClass}>
          <option value="">All periods</option><option value="NO_PERIOD">Without a period</option>
          {periods.map(period => <option key={period} value={period}>{period}</option>)}
        </select>
        <select aria-label="Filter by type" value={typeFilter} onChange={event => setTypeFilter(event.target.value)} className={selectClass}>
          <option value="">All types</option><option value="MONTHLY">Monthly editions</option><option value="STANDALONE">Standalone reports</option>
        </select>
      </div>
      {loading && <p className="text-sm text-gray-500">Loading reports and corpora…</p>}
      {error && <p role="alert" className="text-sm text-red-700">{error}</p>}
      {!loading && !error && <p className="text-xs text-gray-500">{visible.length} matching entries</p>}
      {!loading && !error && visible.length === 0 && <p className="text-sm text-gray-500">No matching reports or corpora.</p>}
      {!loading && visible.map(row => (
        <article key={row.key} className="rounded-lg border border-gray-200 p-4">
          <div className="flex flex-wrap items-start justify-between gap-3">
            <div className="min-w-0 flex-1">
              <p className="text-xs font-medium text-gray-500">
                {row.type === "MONTHLY" ? "Monthly edition" : "Standalone report"}
                {row.expertId && ` · ${expertNames[row.expertId] ?? row.expertId}`}
                {row.period && ` · ${row.period}`}
              </p>
              <h3 className="mt-1 font-semibold text-gray-900">{row.subject}</h3>
              {row.report && row.report.subject !== row.subject && <p className="mt-1 text-sm text-gray-600">{row.report.subject}</p>}
              {!row.edition && row.report?.objective && <p className="mt-1 text-sm text-gray-600">{row.report.objective}</p>}
              <p className="mt-2 text-xs text-gray-600">
                {STATUS_LABELS[row.status] ?? row.status}
                {row.edition ? <>
                  {" · "}<span className={row.edition.proposed_count === 0 ? "font-semibold text-amber-700" : "font-semibold text-gray-900"}
                    title="Excludes dismissed sources and OUT_OF_SCOPE evaluations.">
                    {row.edition.proposed_count == null ? row.edition.status === "BUILDING" ? "Proposed corpus pending" : "Proposed corpus unavailable" : `${row.edition.proposed_count} contents proposed`}
                  </span>{` · ${row.edition.selected_count ?? 0} sources selected · ${row.edition.output_language.toUpperCase()}`}
                </> : row.report && ` · ${row.report.source_count} sources · ${(row.report.output_language ?? "").toUpperCase()}`}
              </p>
              {row.edition?.candidate_count != null && <p className="mt-1 text-xs text-gray-500">{row.edition.candidate_count} candidates retrieved before evaluation</p>}
              {row.report && <p className="mt-1 text-xs text-gray-500">Saved {new Date(row.report.created_at).toLocaleDateString("en-GB")} · Version {row.report.version_number}</p>}
              {row.edition?.error && <p className="mt-2 text-sm text-red-700">{row.edition.error}</p>}
            </div>
            <div className="flex flex-wrap items-start gap-2">
              {row.edition?.status === "TO_REVIEW" && <Link
                href={`/admin/touch?edition_id=${encodeURIComponent(row.edition.edition_id)}`}
                aria-disabled={interactionsDisabled} onClick={event => { if (interactionsDisabled) event.preventDefault(); }}
                className={`rounded-lg bg-ratecard-blue px-3 py-2 text-sm text-white${interactionsDisabled ? " cursor-not-allowed opacity-50" : ""}`}>Review corpus</Link>}
              {row.edition?.status === "GENERATED" && <button type="button" disabled={interactionsDisabled} onClick={() => void manage(row, "reopen")} className={buttonClass}>Reopen corpus</button>}
              {row.reportId && <>
                <button type="button" disabled={interactionsDisabled} onClick={() => void onOpenReport(row.reportId!)} className={buttonClass}>Open report</button>
                <button type="button" disabled={interactionsDisabled} onClick={() => void manage(row, row.status === "ARCHIVED" ? "restore" : "archive")} className={buttonClass}>{row.status === "ARCHIVED" ? "Restore" : "Archive"}</button>
                <button type="button" disabled={interactionsDisabled} onClick={() => void manage(row, "delete")} className={`${buttonClass} border-red-200 text-red-700`}>Delete report</button>
              </>}
              {row.edition && <button type="button" disabled={interactionsDisabled || row.edition.status === "BUILDING"}
                onClick={() => void manage(row, "reset")}
                title={row.edition.status === "BUILDING" ? "Wait until preparation has finished." : "Delete the monthly corpus, source selections and linked report."}
                className={`${buttonClass} border-red-200 text-red-700 hover:bg-red-50`}>Reset corpus and report</button>}
              {busyKey === row.key && <span role="status" className="self-center text-xs text-gray-500">Updating…</span>}
            </div>
          </div>
        </article>
      ))}
      {!loading && (editions.length >= 200 || reports.length >= 50) && <p className="text-xs text-amber-700">
        The list loads up to 200 recent editions and 50 recent saved reports. Filters apply to these loaded entries.
      </p>}
    </section>
  );
}
