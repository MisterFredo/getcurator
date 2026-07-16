"use client";

import { useState } from "react";

import { api } from "@/lib/api";

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

  /* ======================================================= */

  async function run(
    operation: string,
  ) {

    try {

      setLoading(true);

      setSuccess(null);

      setError(null);

      const res =
        await api.post(
          `/cockpit/operations/${operation}`,
        );

      setSuccess(
        res.message ||
        "Operation completed.",
      );

      return res;

    } catch (e: any) {

      console.error(
        "Cockpit operation failed",
        e,
      );

      setError(
        e?.message ||
        "Operation failed.",
      );

      throw e;

    } finally {

      setLoading(false);

    }

  }

  /* ======================================================= */

  function reset() {

    setSuccess(null);

    setError(null);

  }

  /* ======================================================= */

  return {

    loading,

    success,

    error,

    run,

    reset,

  };

}
