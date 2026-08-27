"use client";

import {
  useCallback,
  useEffect,
  useState,
} from "react";

import {
  Languages,
  Play,
  RefreshCw,
} from "lucide-react";

import {
  api,
} from "@/lib/api";


/* ========================================================= */

type BackfillStatus = {

  state:
    | "NOT_STARTED"
    | "RUNNING"
    | "PAUSED"
    | "FAILED"
    | "READY_TO_MERGE";

  running: boolean;

  started_at?: string | null;

  finished_at?: string | null;

  last_error?: string | null;

  total_count: number;

  completed_count: number;

  failed_count: number;

  failed_attempt_count: number;

  remaining_count: number;

  progress_percent: number;

};


/* ========================================================= */

export default function TranslationBackfillOperation() {

  const [
    status,
    setStatus,
  ] = useState<BackfillStatus | null>(
    null,
  );

  const [
    loading,
    setLoading,
  ] = useState(true);

  const [
    actionLoading,
    setActionLoading,
  ] = useState(false);

  const [
    error,
    setError,
  ] = useState<string | null>(
    null,
  );


  /* =====================================================
     LOAD STATUS
  ===================================================== */

  const loadStatus = useCallback(
    async (
      showLoading = false,
    ) => {

      try {

        if (showLoading) {
          setLoading(true);
        }

        const response =
          await api.get(
            "/cockpit/operations/translation-backfill/status",
          );

        setStatus(
          response.backfill,
        );

        setError(null);

      } catch (e: any) {

        setError(
          e?.message
          || "Unable to load translation backlog status.",
        );

      } finally {

        if (showLoading) {
          setLoading(false);
        }

      }

    },
    [],
  );


  /* =====================================================
     INITIAL LOAD + POLLING
  ===================================================== */

  useEffect(() => {

    loadStatus(true);

    const interval =
      window.setInterval(
        () => {
          loadStatus(false);
        },
        5000,
      );

    return () => {
      window.clearInterval(
        interval,
      );
    };

  }, [
    loadStatus,
  ]);


  /* =====================================================
     START / RESUME
  ===================================================== */

  async function startOrResume() {

    try {

      setActionLoading(true);

      setError(null);

      const endpoint = (

        status
        && status.completed_count > 0

          ? "/cockpit/operations/translation-backfill/retry"

          : "/cockpit/operations/translation-backfill/start"

      );

      await api.post(
        endpoint,
        {},
      );

      await loadStatus(false);

    } catch (e: any) {

      setError(
        e?.message
        || "Unable to start translation backlog.",
      );

    } finally {

      setActionLoading(false);

    }

  }


  /* =====================================================
     DISPLAY
  ===================================================== */

  const progress = Math.min(
    Math.max(
      status?.progress_percent
      || 0,
      0,
    ),
    100,
  );

  const isRunning = Boolean(
    status?.running
  );

  const readyToMerge = (
    status?.state
    === "READY_TO_MERGE"
  );

  const blockedByErrors = Boolean(

    status

    && status.remaining_count === 0

    && status.failed_count > 0

  );


  /* =====================================================
     RENDER
  ===================================================== */

  return (

    <div className="rounded-lg border p-4">

      <div className="flex items-start justify-between gap-6">

        <div className="flex min-w-0 flex-1 items-start gap-3">

          <Languages
            size={18}
            className="mt-1 shrink-0 text-gray-500"
          />

          <div className="min-w-0 flex-1">

            <div className="font-medium">

              Translation Backfill 2026

            </div>

            <div className="text-sm text-gray-500">

              Persist the five English drawer fields for content published since January 2026.

            </div>

            {loading && (

              <div className="mt-3 text-sm text-gray-400">

                Loading progress…

              </div>

            )}

            {!loading && status && (

              <div className="mt-4 space-y-3">

                <div className="flex flex-wrap gap-x-5 gap-y-1 text-sm">

                  <span>

                    <strong>
                      {status.completed_count}
                    </strong>
                    {" / "}
                    {status.total_count}
                    {" completed"}

                  </span>

                  <span>

                    <strong>
                      {status.remaining_count}
                    </strong>
                    {" remaining"}

                  </span>

                  <span
                    className={
                      status.failed_count > 0
                        ? "text-red-600"
                        : ""
                    }
                  >

                    <strong>
                      {status.failed_count}
                    </strong>
                    {" failed"}

                  </span>

                </div>

                <div className="h-2 overflow-hidden rounded-full bg-gray-100">

                  <div
                    className="h-full rounded-full bg-ratecard-blue transition-all duration-500"
                    style={{
                      width:
                        `${progress}%`,
                    }}
                  />

                </div>

                <div className="flex items-center justify-between text-xs text-gray-500">

                  <span>

                    {progress.toFixed(1)}
                    {"%"}

                  </span>

                  <span>

                    {isRunning
                      ? "Running"
                      : readyToMerge
                        ? "Ready to merge"
                        : blockedByErrors
                          ? "Completed with errors"
                          : status.state === "PAUSED"
                            ? "Paused"
                            : "Not started"}

                  </span>

                </div>

              </div>

            )}

            {error && (

              <div className="mt-3 text-sm text-red-600">

                {error}

              </div>

            )}

            {status?.last_error && (

              <div className="mt-3 text-sm text-red-600">

                {status.last_error}

              </div>

            )}

          </div>

        </div>

        <button
          type="button"
          disabled={
            loading
            || actionLoading
            || isRunning
            || readyToMerge
            || blockedByErrors
          }
          onClick={
            startOrResume
          }
          className="inline-flex shrink-0 items-center gap-2 rounded-lg bg-ratecard-blue px-4 py-2 text-white disabled:opacity-50"
        >

          {isRunning ? (

            <RefreshCw
              size={16}
              className="animate-spin"
            />

          ) : (

            <Play size={16} />

          )}

          {isRunning
            ? "Running"
            : status
              && status.completed_count > 0
                ? "Resume"
                : "Start"}

        </button>

      </div>

    </div>

  );

}
