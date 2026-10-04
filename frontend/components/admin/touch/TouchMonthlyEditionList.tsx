"use client";

import { useEffect, useMemo, useState } from "react";
import Link from "next/link";
import { api } from "@/lib/api";


type Edition = {
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
};

type Props = {
  onOpenReport: (reportId: string) => Promise<void>;
  disabled?: boolean;
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
}: Props) {
  const [editions, setEditions] = useState<Edition[]>([]);
  const [expertNames, setExpertNames] = useState<Record<string, string>>({});
  const [expertFilter, setExpertFilter] = useState("");
  const [statusFilter, setStatusFilter] = useState("");
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
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
  }, [reload]);

  const expertIds = useMemo(
    () => Array.from(new Set(editions.map(edition => edition.expert_id))),
    [editions],
  );

  const visible = useMemo(
    () => editions.filter(edition =>
      (!expertFilter || edition.expert_id === expertFilter)
      && (!statusFilter || edition.status === statusFilter),
    ),
    [editions, expertFilter, statusFilter],
  );

  return (
    <section className="space-y-4 rounded-xl border border-gray-200 bg-white p-5">
      <div className="flex flex-wrap items-start justify-between gap-3">
        <div>
          <h2 className="text-lg font-semibold text-gray-900">Monthly expert editions</h2>
          <p className="mt-1 text-sm text-gray-500">
            Check the initial corpus size, then review sources before generating each monthly report.
          </p>
        </div>
        <button
          type="button"
          disabled={loading || disabled}
          onClick={() => setReload(value => value + 1)}
          className="rounded-lg border px-3 py-2 text-sm disabled:opacity-50"
        >
          Refresh
        </button>
      </div>

      <div className="flex flex-wrap gap-3">
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
                {STATUS_LABELS[edition.status] ?? edition.status}
                {" · "}
                <span
                  className={edition.candidate_count === 0
                    ? "font-semibold text-amber-700"
                    : "font-semibold text-gray-900"}
                  title="All candidates returned by the search before manual selection, including sources later dismissed."
                >
                  {edition.candidate_count == null
                    ? edition.status === "BUILDING"
                      ? "Initial corpus pending"
                      : "Initial corpus unavailable"
                    : `${edition.candidate_count} contents retrieved`}
                </span>
                {" · "}
                {edition.selected_count ?? 0} sources selected
                {" · "}
                {edition.output_language.toUpperCase()}
              </p>
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
            {edition.status === "GENERATED" && edition.report_id && (
              <button
                type="button"
                disabled={disabled}
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
