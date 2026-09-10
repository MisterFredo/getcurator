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
  NumbersKnowledgeContinueResponse,
  NumbersKnowledgeContinueResult,
  NumbersKnowledgeStatus,
  NumbersKnowledgeStatusResponse,
} from "@/types/numbers";

/* =========================================================
   TYPES
========================================================= */

type KnowledgeNumbersAction =
  | "batch"
  | "continuous"
  | null;

/* =========================================================
   CONFIG
========================================================= */

const ENTITY_BATCH_SIZE = 5;
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

export function useNumbersKnowledge() {

  const [
    monitoring,
    setMonitoring,
  ] = useState<NumbersKnowledgeStatus | null>(
    null,
  );

  const [
    lastRun,
    setLastRun,
  ] = useState<NumbersKnowledgeContinueResult | null>(
    null,
  );

  const [
    loading,
    setLoading,
  ] = useState(true);

  const [
    action,
    setAction,
  ] = useState<KnowledgeNumbersAction>(
    null,
  );

  const [
    error,
    setError,
  ] = useState<string | null>(
    null,
  );

  const [
    continuousBuilt,
    setContinuousBuilt,
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
            "/numbers/knowledge/status",
          ) as NumbersKnowledgeStatusResponse;

        setMonitoring(
          response.result,
        );

      } catch (requestError) {

        setError(
          requestError instanceof Error
            ? requestError.message
            : "Unable to load Numbers Knowledge monitoring.",
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
    async () => {

      const response =
        await api.post(
          (
            "/numbers/knowledge/continue"
            + `?limit=${ENTITY_BATCH_SIZE}`
          ),
          {},
        ) as NumbersKnowledgeContinueResponse;

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
    async () => {

      setAction(
        "batch",
      );

      setError(null);

      try {

        return await executeBatch();

      } catch (requestError) {

        setError(
          requestError instanceof Error
            ? requestError.message
            : "Unable to update Numbers Knowledge.",
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
     CONTINUOUS BUILD
  ======================================================= */

  const startContinuous = useCallback(
    async () => {

      stopRequestedRef.current = false;

      setContinuousBuilt(0);

      setAction(
        "continuous",
      );

      setError(null);

      try {

        while (
          !stopRequestedRef.current
        ) {

          const result =
            await executeBatch();

          setContinuousBuilt(
            (current) =>
              current
              + result.built_entities,
          );

          if (
            result.selected_entities === 0
          ) {
            break;
          }

          /*
           * Stop on an entity failure to avoid
           * selecting the same failing entity
           * indefinitely.
           */
          if (
            result.failed_entities > 0
          ) {

            setError(
              "The continuous Numbers Knowledge build stopped because "
              + `${result.failed_entities} entity build failed.`
            );

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
            : "Continuous Numbers Knowledge build failed.",
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
     STOP
  ======================================================= */

  const stopContinuous = useCallback(
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

    continuousBuilt,

    reload: loadMonitoring,
    runBatch,

    startContinuous,
    stopContinuous,
  };
}
