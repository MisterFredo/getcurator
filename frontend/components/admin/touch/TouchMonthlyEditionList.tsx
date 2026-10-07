"use client";

import {
  useEffect,
  useMemo,
  useState,
} from "react";

import Link from "next/link";

import { api } from "@/lib/api";
import { deleteTouchEdition } from "@/lib/touch";

/* =========================================================
   TYPES
========================================================= */

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

/* =========================================================
   COMPONENT
========================================================= */

export default function TouchMonthlyEditionList({
  onOpenReport,
  disabled = false,
  refreshKey = 0,
  onChanged,
}: Props) {
  const [editions, setEditions] = useState<Edition[]>([]);

  const [expertNames, setExpertNames] = useState<
    Record<string, string>
  >({});

  const [expertFilter, setExpertFilter] = useState("");
  const [statusFilter, setStatusFilter] = useState("");
  const [archiveFilter, setArchiveFilter] = useState("active");

  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [busy, setBusy] = useState(false);

  const [reload, setReload] = useState(0);

  const [resettingId, setResettingId] = useState<
    string | null
  >(null);

  /* =======================================================
     LOAD EDITIONS AND EXPERT NAMES
  ======================================================= */

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
          const id =
            expert.ID_USER
            ?? expert.id_user
            ?? expert.user_id
            ?? expert.id;

          if (id) {
            names[id] =
              expert.DISPLAY_NAME
              ?? expert.display_name
              ?? expert.NAME
              ?? expert.name
              ?? id;
          }
        }

        setExpertNames(names);
      }

      setLoading(false);
    }

    void load();

    return () => {
      active = false;
    };
  }, [reload, refreshKey]);

  /* =======================================================
     FILTERS
  ======================================================= */

  const expertIds = useMemo(
    () =>
      Array.from(
        new Set(
          editions.map(edition => edition.expert_id),
        ),
      ),
    [editions],
  );

  const visible = useMemo(
    () =>
      editions.filter(
        edition =>
          (!expertFilter || edition.expert_id === expertFilter)
          && (!statusFilter || edition.status === statusFilter)
          && (
            archiveFilter === "all"
            || (
              archiveFilter === "archived"
                ? !!edition.archived_at
                : !edition.archived_at
            )
          ),
      ),
    [editions, expertFilter, statusFilter, archiveFilter],
  );

  /* =======================================================
     REFRESH AFTER CHANGES
  ======================================================= */

  function refreshAfterChange() {
    if (onChanged) {
      onChanged();
    } else {
      setReload(value => value + 1);
    }
  }

  /* =======================================================
     MANAGE LINKED REPORT
  ======================================================= */

  async function manage(
    edition: Edition,
    action: "archive" | "restore" | "delete" | "reopen",
  ) {
    if (busy || disabled) return;

    if (
      action === "delete"
      && !window.confirm(
        "Delete this document? "
        + "The selected corpus will be preserved for regeneration.",
      )
    ) {
      return;
    }

    if (
      action === "reopen"
      && !window.confirm(
        "Reopen the selected corpus? "
        + "The current report will be kept in archives.",
      )
    ) {
      return;
    }

    setBusy(true);
    setError(null);

    try {
      if (action === "reopen") {
        await api.post(
          `/touch/editions/${encodeURIComponent(edition.edition_id)}/reopen`,
          {},
        );

        window.location.assign(
          `/admin/touch?edition_id=${encodeURIComponent(edition.edition_id)}`,
        );
      } else if (edition.report_id) {
        const path =
          `/touch/reports/${encodeURIComponent(edition.report_id)}`;

        if (action === "delete") {
          await api.delete(path);
        } else {
          await api.post(`${path}/${action}`, {});
        }

        refreshAfterChange();
      }
    } catch (exception) {
      setError(
        exception instanceof Error
          ? exception.message
          : "Unable to update report.",
      );
    } finally {
      setBusy(false);
    }
  }

  /* =======================================================
     RESET MONTHLY CORPUS AND LINKED REPORT
  ======================================================= */

  async function handleReset(edition: Edition) {
    if (
      busy
      || disabled
      || edition.status === "BUILDING"
    ) {
      return;
    }

    const confirmed = window.confirm(
      `Reset “${edition.subject}”? `
      + "This will permanently delete the monthly corpus, "
      + "all source selections and the linked report, if any. "
      + "Previously archived reports will be preserved. "
      + "Prepare this edition again to use the current expert profile.",
    );

    if (!confirmed) return;

    setBusy(true);
    setResettingId(edition.edition_id);
    setError(null);

    try {
      await deleteTouchEdition(edition.edition_id);

      setEditions(current =>
        current.filter(
          item => item.edition_id !== edition.edition_id,
        ),
      );

      refreshAfterChange();
    } catch (exception) {
      setError(
        exception instanceof Error
          ? exception.message
          : "Unable to reset the monthly edition.",
      );
    } finally {
      setResettingId(null);
      setBusy(false);
    }
  }

  /* =======================================================
     RENDER
  ======================================================= */

  const interactionsDisabled = disabled || busy;

  return (
    <section className="space-y-4 rounded-xl border border-gray-200 bg-white p-5">
      <div className="flex flex-wrap items-start justify-between gap-3">
        <div>
          <h2 className="text-lg font-semibold text-gray-900">
            Monthly expert editions
          </h2>

          <p className="mt-1 text-sm text-gray-500">
            Review the proposed contents before selecting sources
            for each monthly report.
          </p>
        </div>

        <button
          type="button"
          disabled={loading || interactionsDisabled}
          onClick={() => setReload(value => value + 1)}
          className="rounded-lg border px-3 py-2 text-sm disabled:opacity-50"
        >
          Refresh
        </button>
      </div>

      <div className="flex flex-wrap gap-3">
        <select
          aria-label="Filter archives"
          value={archiveFilter}
          onChange={event =>
            setArchiveFilter(event.target.value)
          }
          className="rounded-lg border px-3 py-2 text-sm"
        >
          <option value="active">Active editions</option>
          <option value="archived">Archived reports</option>
          <option value="all">All editions</option>
        </select>

        <select
          aria-label="Filter editions by expert"
          value={expertFilter}
          onChange={event =>
            setExpertFilter(event.target.value)
          }
          className="rounded-lg border px-3 py-2 text-sm"
        >
          <option value="">All experts</option>

          {expertIds.map(id => (
            <option key={id} value={id}>
              {expertNames[id] ?? id}
            </option>
          ))}
        </select>

        <select
          aria-label="Filter editions by status"
          value={statusFilter}
          onChange={event =>
            setStatusFilter(event.target.value)
          }
          className="rounded-lg border px-3 py-2 text-sm"
        >
          <option value="">All statuses</option>

          {Object.entries(STATUS_LABELS).map(
            ([status, label]) => (
              <option key={status} value={status}>
                {label}
              </option>
            ),
          )}
        </select>
      </div>

      {loading && (
        <p className="text-sm text-gray-500">
          Loading monthly editions…
        </p>
      )}

      {error && (
        <p className="text-sm text-red-700" role="alert">
          {error}
        </p>
      )}

      {!loading && !error && visible.length === 0 && (
        <p className="text-sm text-gray-500">
          No matching editions. Prepare monthly corpora
          from the dashboard or Touch.
        </p>
      )}

      {visible.map(edition => (
        <article
          key={edition.edition_id}
          className="rounded-lg border border-gray-200 p-4"
        >
          <div className="flex flex-wrap items-start justify-between gap-3">
            <div className="min-w-0 flex-1">
              <p className="text-xs font-medium text-gray-500">
                {expertNames[edition.expert_id] ?? edition.subject}
                {" · "}
                {edition.period_start.slice(0, 7)}
              </p>

              <h3 className="mt-1 font-semibold text-gray-900">
                {edition.subject}
              </h3>

              <p className="mt-2 text-xs text-gray-600">
                {edition.archived_at
                  ? "Archived"
                  : STATUS_LABELS[edition.status] ?? edition.status}

                {" · "}

                <span
                  className={
                    edition.proposed_count === 0
                      ? "font-semibold text-amber-700"
                      : "font-semibold text-gray-900"
                  }
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
                  {edition.candidate_count} candidates retrieved
                  before evaluation
                </p>
              )}

              {edition.error && (
                <p className="mt-2 text-sm text-red-700">
                  {edition.error}
                </p>
              )}
            </div>

            <div className="flex flex-wrap items-start gap-2">
              {edition.status === "TO_REVIEW" && (
                <Link
                  href={
                    interactionsDisabled
                      ? "#"
                      : `/admin/touch?edition_id=${encodeURIComponent(edition.edition_id)}`
                  }
                  aria-disabled={interactionsDisabled}
                  onClick={event => {
                    if (interactionsDisabled) {
                      event.preventDefault();
                    }
                  }}
                  className={
                    "rounded-lg bg-ratecard-blue px-3 py-2 text-sm text-white"
                    + (
                      interactionsDisabled
                        ? " cursor-not-allowed opacity-50"
                        : ""
                    )
                  }
                >
                  Review corpus
                </Link>
              )}

              {edition.status === "GENERATED" && (
                <>
                  <button
                    type="button"
                    disabled={interactionsDisabled}
                    onClick={() =>
                      void manage(edition, "reopen")
                    }
                    className="rounded-lg border px-3 py-2 text-sm disabled:opacity-50"
                  >
                    Reopen corpus
                  </button>

                  {edition.report_id && (
                    <>
                      <button
                        type="button"
                        disabled={interactionsDisabled}
                        onClick={() =>
                          void manage(
                            edition,
                            edition.archived_at
                              ? "restore"
                              : "archive",
                          )
                        }
                        className="rounded-lg border px-3 py-2 text-sm disabled:opacity-50"
                      >
                        {edition.archived_at ? "Restore" : "Archive"}
                      </button>

                      <button
                        type="button"
                        disabled={interactionsDisabled}
                        onClick={() =>
                          void manage(edition, "delete")
                        }
                        className="rounded-lg border border-red-200 px-3 py-2 text-sm text-red-700 disabled:opacity-50"
                      >
                        Delete report
                      </button>

                      <button
                        type="button"
                        disabled={interactionsDisabled}
                        onClick={() =>
                          void onOpenReport(edition.report_id!)
                        }
                        className="rounded-lg border px-3 py-2 text-sm disabled:opacity-50"
                      >
                        Open report
                      </button>
                    </>
                  )}
                </>
              )}

              <button
                type="button"
                disabled={
                  interactionsDisabled
                  || edition.status === "BUILDING"
                }
                onClick={() => void handleReset(edition)}
                title={
                  edition.status === "BUILDING"
                    ? "Wait until preparation has finished."
                    : "Delete the monthly corpus, source selections and linked report."
                }
                className="
                  rounded-lg
                  border
                  border-red-200
                  px-3
                  py-2
                  text-sm
                  text-red-700
                  hover:bg-red-50
                  disabled:cursor-not-allowed
                  disabled:opacity-50
                "
              >
                {resettingId === edition.edition_id
                  ? "Resetting…"
                  : "Reset corpus and report"}
              </button>
            </div>
          </div>
        </article>
      ))}

      {!loading && editions.length === 200 && (
        <p className="text-xs text-gray-500">
          Showing the 200 most recent editions.
        </p>
      )}
    </section>
  );
}
