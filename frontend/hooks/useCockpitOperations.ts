"use client";

import { useState } from "react";
import { api } from "@/lib/api";
import { digestBatchMessage, generateUserDigestsV2 } from "@/lib/digest-v2";

const DIGEST_OPERATION_ROUTES: Record<string, string> = {
  "initialize-digest-histories": "/digest/bootstrap-all",
};
const TOUCH_OPERATION_MONTHS: Record<string, number> = {
  "initialize-touch-histories": 3,
  "prepare-latest-touch-editions": 1,
};

export function useCockpitOperations() {
  const [loading, setLoading] = useState(false);
  const [success, setSuccess] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);

  async function run(operation: string) {
    setLoading(true);
    setSuccess(null);
    setError(null);
    try {
      if (operation === "generate-all-digests" || operation === "generate-user-digests-v2") {
        const result = await generateUserDigestsV2(undefined, setSuccess);
        setSuccess(digestBatchMessage(result));
        if (result.errors.length) setError(result.errors.join(" · "));
        return result;
      }
      const months = TOUCH_OPERATION_MONTHS[operation];
      const endpoint = months ? "/touch/editions/prepare"
        : DIGEST_OPERATION_ROUTES[operation] || "/cockpit/operations/" + operation;
      const result = await api.post(endpoint, months ? { months_count: months } : {});
      if (months) {
        const preparation = result.preparation ?? {};
        const prefix = preparation.status === "failed" ? "Preparation failed — "
          : preparation.status === "partial" ? "Preparation partially completed — " : "";
        setSuccess(prefix + [
          `${preparation.processed_count ?? 0} experts processed`,
          `${preparation.prepared_count ?? 0} editions ready for review`,
          `${preparation.skipped_count ?? 0} existing editions preserved`,
          `${preparation.failed_count ?? 0} failed`,
        ].join(" · "));
      } else if (operation === "initialize-digest-histories") {
        setSuccess([
          `${result.processed_count ?? 0} profiles processed`,
          `${result.generated_count ?? 0} Digests generated`,
          `${result.skipped_count ?? 0} already available`,
          `${result.failed_count ?? 0} failed`,
        ].join(" · "));
      } else {
        setSuccess(result.message || "Operation completed.");
      }
      return result;
    } catch (failure) {
      setError(failure instanceof Error ? failure.message : "Operation failed.");
      throw failure;
    } finally {
      setLoading(false);
    }
  }

  function reset() {
    setSuccess(null);
    setError(null);
  }
  return { loading, success, error, run, reset };
}
