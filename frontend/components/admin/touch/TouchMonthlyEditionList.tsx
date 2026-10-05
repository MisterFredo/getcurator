"use client";

import { useEffect, useMemo, useState } from "react";
import Link from "next/link";
import { api } from "@/lib/api";


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

type Props = {
  onOpenReport: (reportId: string) => Promise<void>;
  disabled?: boolean;
  refreshKey?: number;
  onChanged?: () => void;
};

const STATUS_LABELS: Record<string, string> = {
  BUILDING: "Preparing",
  TO_REVIEW: "To review",
  GENERATED: "Generated",
  ERROR: "Preparation failed",
};


export default function TouchMonthlyEditionList({
  onOpenReport,
  disabled = false,
  refreshKey = 0,
  onChanged,
}: Props) {
  const [editions, setEditions] = useState<Edition[]>([]);
  const [expertNames, setExpertNames] = useState<Record<string, string>>({});
  const [expertFilter, setExpertFilter] = useState("");
  const [statusFilter, setStatusFilter] = useState("");
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [busy, setBusy] = useState(false);
  const [archiveFilter, setArchiveFilter] = useState("active");
  const [reload, setReload] = useState(0);

  useEffect(() => {
    let active = true;
    setLoading(true);
    setError(null);
    async function load() {
      const results = await Promise.allSettled([
        api.get("/touch/editions?limit=200"),
        api.get("/user/admin/experts"),
      ]);
      if (!active) return;
      if (results[0].status === "fulfilled") {
        setEditions(results[0].value.editions ?? []);
      } else {
        setError(
          results[0].reason instanceof Error
            ? results[0].reason.message
            : "Unable to load monthly editions.",
        );
      }
      if (results[1].status === "fulfilled") {
        const names: Record<string, string> = {};
        for (const expert of results[1].value.experts ?? []) {
          const id = expert.ID_USER ?? expert.id_user ?? expert.user_id ?? expert.id;
          if (id) names[id] = expert.DISPLAY_NAME ?? expert.display_name
            ?? expert.NAME ?? expert.name ?? id;
        }
        setExpertNames(names);
      }
      setLoading(false);
    }
    void load();
    return () => { active = false; };
  }, [reload, refreshKey]);

  const expertIds = useMemo(
    () => Array.from(new Set(editions.map(edition => edition.expert_id))),
    [editions],
  );

  const visible = useMemo(
    () => editions.filter(edition =>
      (!expertFilter || edition.expert_id === expertFilter)
      && (!statusFilter || edition.status === statusFilter)
      && (archiveFilter === "all" || (archiveFilter === "archived" ? !!edition.archived_at : !edition.archived_at)),
    ),
    [editions, expertFilter, statusFilter, archiveFilter],
  );

  async function manage(edition: Edition, action: "archive" | "restore" | "delete" | "reopen") {
    if (busy || disabled) return;
    if (action === "delete" && !window.confirm("Delete this document? The selected corpus will be preserved for regeneration.")) return;
    if (action === "reopen" && !window.confirm("Reopen the selected corpus? The current report will be kept in archives.")) return;
    setBusy(true);
    setError(null);
    try {
      if (action === "reopen") {
        await api.post(`/touch/editions/${encodeURIComponent(edition.edition_id)}/reopen`, {});
        window.location.assign(`/admin/touch?edition_id=${encodeURIComponent(edition.edition_id)}`);
      } else if (edition.report_id) {
        const path = `/touch/reports/${encodeURIComponent(edition.report_id)}`;
        if (action === "delete") await api.delete(path);
        else await api.post(`${path}/${action}`, {});
        setReload(value => value + 1);
        onChanged?.();
      }
    } catch (exception) {
      setError(exception instanceof Error ? exception.message : "Unable to update report.");
    } finally { setBusy(false); }
  }

  return (
    <section className="space-y-4 rounded-xl border border-gray-200 bg-white p-5">
      <div className="flex flex-wrap items-start justify-between gap-3">
        <div>
          <h2 className="text-lg font-semibold text-gray-900">Monthly expert editions</h2>
          <p className="mt-1 text-sm text-gray-500">
            Review the proposed contents before selecting sources for each monthly report.
          </p>
        </div>
        <button
          type="button"
          disabled={loading || disabled || busy}
          onClick={() => setReload(value => value + 1)}
          className="rounded-lg border px-3 py-2 text-sm disabled:opacity-50"
        >
          Refresh
        </button>
      </div>

      <div className="flex flex-wrap gap-3">
        <select aria-label="Filter archives" value={archiveFilter} onChange={event => setArchiveFilter(event.target.value)} className="rounded-lg border px-3 py-2 text-sm">
          <option value="active">Active editions</option><option value="archived">Archived reports</option><option value="all">All editions</option>
        </select>
        <select
          aria-label="Filter editions by expert"
          value={expertFilter}
          onChange={event => setExpertFilter(event.target.value)}
          className="rounded-lg border px-3 py-2 text-sm"
        >
          <option value="">All experts</option>
          {expertIds.map(id => (
            <option key={id} value={id}>{expertNames[id] ?? id}</option>
          ))}
        </select>
        <select
          aria-label="Filter editions by status"
          value={statusFilter}
          onChange={event => setStatusFilter(event.target.value)}
          className="rounded-lg border px-3 py-2 text-sm"
        >
          <option value="">All statuses</option>
          {Object.entries(STATUS_LABELS).map(([status, label]) => (
            <option key={status} value={status}>{label}</option>
          ))}
        </select>
      </div>

      {loading && <p className="text-sm text-gray-500">Loading monthly editions…</p>}
      {error && <p className="text-sm text-red-700" role="alert">{error}</p>}
      {!loading && !error && visible.length === 0 && (
        <p className="text-sm text-gray-500">
          No matching editions. Prepare monthly corpora from the dashboard or Touch.
        </p>
      )}

      {visible.map(edition => (
        <article key={edition.edition_id} className="rounded-lg border border-gray-200 p-4">
          <div className="flex flex-wrap items-start justify-between gap-3">
            <div className="min-w-0">
              <p className="text-xs font-medium text-gray-500">
                {expertNames[edition.expert_id] ?? edition.subject}
                {" · "}
                {edition.period_start.slice(0, 7)}
              </p>
              <h3 className="mt-1 font-semibold text-gray-900">{edition.subject}</h3>
              <p className="mt-2 text-xs text-gray-600">
                {edition.archived_at ? "Archived" : STATUS_LABELS[edition.status] ?? edition.status}
                {" · "}
                <span
                  className={edition.proposed_count === 0
                    ? "font-semibold text-amber-700"
                    : "font-semibold text-gray-900"}
                  title="Contents visible in Proposed contents: excludes dismissed sources and OUT_OF_SCOPE evaluations."
                >
                  {edition.proposed_count == null
                    ? edition.status === "BUILDING"
                      ? "Proposed corpus pending"
                      : "Proposed corpus unavailable"
                    : `${edition.proposed_count} contents proposed`}
                </span>
                {" · "}
                {edition.selected_count ?? 0} sources selected
                {" · "}
                {edition.output_language.toUpperCase()}
              </p>
              {edition.candidate_count != null && (
                <p className="mt-1 text-xs text-gray-500">
                  {edition.candidate_count} candidates retrieved before evaluation
                </p>
              )}
              {edition.error && (
                <p className="mt-2 text-sm text-red-700">{edition.error}</p>
              )}
            </div>

            {edition.status === "TO_REVIEW" && (
              <Link
                href={`/admin/touch?edition_id=${encodeURIComponent(edition.edition_id)}`}
                className="rounded-lg bg-ratecard-blue px-3 py-2 text-sm text-white"
              >
                Review corpus
              </Link>
            )}
            {edition.status === "GENERATED" && (
              <div className="flex flex-wrap gap-2">
                <button type="button" disabled={disabled || busy} onClick={() => void manage(edition, "reopen")} className="rounded-lg border px-3 py-2 text-sm disabled:opacity-50">Reopen corpus</button>
                {edition.report_id && <>
                  <button type="button" disabled={disabled || busy} onClick={() => void manage(edition, edition.archived_at ? "restore" : "archive")} className="rounded-lg border px-3 py-2 text-sm disabled:opacity-50">{edition.archived_at ? "Restore" : "Archive"}</button>
                  <button type="button" disabled={disabled || busy} onClick={() => void manage(edition, "delete")} className="rounded-lg border border-red-200 px-3 py-2 text-sm text-red-700 disabled:opacity-50">Delete</button>
                </>}
              </div>
            )}
            {edition.status === "GENERATED" && edition.report_id && (
              <button
                type="button"
                disabled={disabled || busy}
                onClick={() => void onOpenReport(edition.report_id!)}
                className="rounded-lg border px-3 py-2 text-sm disabled:opacity-50"
              >
                Open report
              </button>
            )}
          </div>
        </article>
      ))}
      {!loading && editions.length === 200 && (
        <p className="text-xs text-gray-500">Showing the 200 most recent editions.</p>
      )}
    </section>
  );
}
