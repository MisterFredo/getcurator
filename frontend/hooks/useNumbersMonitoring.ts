"use client";

import {
  useCallback,
  useEffect,
  useRef,
  useState,
} from "react";

import {
  api,
} from "@/lib/api";

import type {
  NumbersBackfillResponse,
  NumbersBackfillResult,
  NumbersBackfillStatus,
  NumbersBackfillStatusResponse,
} from "@/types/numbers";

/* =========================================================
   TYPES
========================================================= */

type NumbersAction =
  | "continue"
  | "retry"
  | "continuous"
  | null;

/* =========================================================
   CONFIG
========================================================= */

const BATCH_SIZE = 5;
const BATCH_PAUSE_MS = 750;

/* =========================================================
   HELPERS
========================================================= */

function wait(
  duration: number,
) {

  return new Promise<void>(
    (resolve) => {

      window.setTimeout(
        resolve,
        duration,
      );

    },
  );
}

/* =========================================================
   HOOK
========================================================= */

export function useNumbersMonitoring() {

  const [
    monitoring,
    setMonitoring,
  ] = useState<NumbersBackfillStatus | null>(
    null,
  );

  const [
    lastRun,
    setLastRun,
  ] = useState<NumbersBackfillResult | null>(
    null,
  );

  const [
    loading,
    setLoading,
  ] = useState(true);

  const [
    action,
    setAction,
  ] = useState<NumbersAction>(
    null,
  );

  const [
    error,
    setError,
  ] = useState<string | null>(
    null,
  );

  const [
    continuousProcessed,
    setContinuousProcessed,
  ] = useState(0);

  const stopRequestedRef =
    useRef(false);

  /* =======================================================
     LOAD MONITORING
  ======================================================= */

  const loadMonitoring = useCallback(
    async (
      showLoading: boolean = true,
    ) => {

      if (showLoading) {
        setLoading(true);
      }

      try {

        setError(null);

        const response =
          await api.get(
            "/numbers/backfill/status",
          ) as NumbersBackfillStatusResponse;

        setMonitoring(
          response.result,
        );

      } catch (requestError) {

        setError(
          requestError instanceof Error
            ? requestError.message
            : "Unable to load Numbers monitoring.",
        );

      } finally {

        if (showLoading) {
          setLoading(false);
        }

      }

    },
    [],
  );

  /* =======================================================
     EXECUTE ONE BATCH
  ======================================================= */

  const executeBatch = useCallback(
    async (
      retryFailed: boolean,
    ) => {

      const response =
        await api.post(
          (
            "/numbers/backfill"
            + `?limit=${BATCH_SIZE}`
            + `&retry_failed=${retryFailed}`
          ),
          {},
        ) as NumbersBackfillResponse;

      setLastRun(
        response.result,
      );

      await loadMonitoring(
        false,
      );

      return response.result;

    },
    [
      loadMonitoring,
    ],
  );

  /* =======================================================
     MANUAL BATCH
  ======================================================= */

  const runBatch = useCallback(
    async (
      retryFailed: boolean,
    ) => {

      setAction(
        retryFailed
          ? "retry"
          : "continue",
      );

      setError(null);

      try {

        return await executeBatch(
          retryFailed,
        );

      } catch (requestError) {

        setError(
          requestError instanceof Error
            ? requestError.message
            : "Unable to run Numbers backfill.",
        );

        return null;

      } finally {

        setAction(null);

      }

    },
    [
      executeBatch,
    ],
  );

  /* =======================================================
     CONTINUOUS BACKFILL
  ======================================================= */

  const startContinuousBackfill =
    useCallback(
      async () => {

        stopRequestedRef.current = false;

        setContinuousProcessed(0);

        setAction(
          "continuous",
        );

        setError(null);

        try {

          while (
            !stopRequestedRef.current
          ) {

            const result =
              await executeBatch(false);

            setContinuousProcessed(
              (current) =>
                current
                + result.processed_count,
            );

            if (
              result.selected_count === 0
            ) {
              break;
            }

            if (
              !stopRequestedRef.current
            ) {

              await wait(
                BATCH_PAUSE_MS,
              );

            }

          }

        } catch (requestError) {

          stopRequestedRef.current = true;

          setError(
            requestError instanceof Error
              ? requestError.message
              : "Continuous Numbers backfill failed.",
          );

        } finally {

          setAction(null);

        }

      },
      [
        executeBatch,
      ],
    );

  /* =======================================================
     STOP CONTINUOUS BACKFILL
  ======================================================= */

  const stopContinuousBackfill =
    useCallback(
      () => {

        stopRequestedRef.current = true;

      },
      [],
    );

  /* =======================================================
     INITIAL LOAD / CLEANUP
  ======================================================= */

  useEffect(
    () => {

      loadMonitoring();

      return () => {

        stopRequestedRef.current = true;

      };

    },
    [
      loadMonitoring,
    ],
  );

  return {
    monitoring,
    lastRun,

    loading,
    action,
    error,

    continuousRunning:
      action === "continuous",

    continuousProcessed,

    reload: loadMonitoring,

    continueBackfill: () =>
      runBatch(false),

    retryFailed: () =>
      runBatch(true),

    startContinuousBackfill,
    stopContinuousBackfill,
  };
}
