"use client";

import {
  useState,
} from "react";

import {
  api,
} from "@/lib/api";


/* =========================================================
   DIGEST ROUTES
========================================================= */

const DIGEST_OPERATION_ROUTES:
  Record<string, string> = {

    "initialize-digest-histories":
      "/digest/bootstrap-all",

    "generate-all-digests":
      "/digest/campaigns/generate-all",

  };


/* ========================================================= */

export function useCockpitOperations() {

  const [
    loading,
    setLoading,
  ] = useState(false);

  const [
    success,
    setSuccess,
  ] = useState<string | null>(
    null,
  );

  const [
    error,
    setError,
  ] = useState<string | null>(
    null,
  );


  /* =====================================================
     RUN
  ===================================================== */

  async function run(
    operation: string,
  ) {

    try {

      setLoading(true);

      setSuccess(null);

      setError(null);

      const endpoint = (

        DIGEST_OPERATION_ROUTES[
          operation
        ]

        || `/cockpit/operations/${operation}`

      );

      const res =
        await api.post(
          endpoint,
          {},
        );

      setSuccess(
        buildSuccessMessage(
          operation,
          res,
        ),
      );

      return res;

    } catch (e: any) {

      console.error(
        "Cockpit operation failed",
        e,
      );

      setError(
        e?.message
        || "Operation failed.",
      );

      throw e;

    } finally {

      setLoading(false);

    }

  }


  /* =====================================================
     RESET
  ===================================================== */

  function reset() {

    setSuccess(null);

    setError(null);

  }


  /* =====================================================
     RETURN
  ===================================================== */

  return {

    loading,

    success,

    error,

    run,

    reset,

  };

}


/* =========================================================
   SUCCESS MESSAGE
========================================================= */

function buildSuccessMessage(
  operation: string,
  result: any,
): string {

  if (
    operation
    === "initialize-digest-histories"
  ) {

    return [

      `${result.processed_count ?? 0} profiles processed`,

      `${result.generated_count ?? 0} Digests generated`,

      `${result.skipped_count ?? 0} already available`,

      `${result.failed_count ?? 0} failed`,

    ].join(" · ");

  }

  if (
    operation
    === "generate-all-digests"
  ) {

    return [

      `${result.campaigns_count ?? 0} Campaigns processed`,

      `${result.generated_count ?? 0} Digests generated`,

      `${result.failed_count ?? 0} failed`,

    ].join(" · ");

  }

  return (
    result.message
    || "Operation completed."
  );

}
