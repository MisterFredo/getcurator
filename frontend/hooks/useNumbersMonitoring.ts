"use client";

import {
  useCallback,
  useEffect,
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
  | null;

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
     RUN BATCH
  ======================================================= */

  const runBatch = useCallback(
    async (
      retryFailed: boolean = false,
    ) => {

      setAction(
        retryFailed
          ? "retry"
          : "continue",
      );

      setError(null);

      try {

        const response =
          await api.post(
            (
              "/numbers/backfill"
              + "?limit=5"
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

      } catch (requestError) {

        const message =
          requestError instanceof Error
            ? requestError.message
            : "Unable to run Numbers backfill.";

        setError(message);

        throw requestError;

      } finally {

        setAction(null);

      }

    },
    [
      loadMonitoring,
    ],
  );

  /* =======================================================
     INITIAL LOAD
  ======================================================= */

  useEffect(
    () => {

      loadMonitoring();

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

    reload: loadMonitoring,

    continueBackfill: () =>
      runBatch(false),

    retryFailed: () =>
      runBatch(true),
  };
}
