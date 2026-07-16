"use client";

import { useCallback, useEffect, useState } from "react";

import { api } from "@/lib/api";

import type {
  CockpitMonitoring,
} from "@/types/cockpit";

/* ========================================================= */

export function useCockpitMonitoring() {

  const [
    loading,
    setLoading,
  ] = useState(true);

  const [
    monitoring,
    setMonitoring,
  ] =
    useState<CockpitMonitoring | null>(
      null,
    );

  /* ======================================================= */

  const refresh =
    useCallback(async () => {

      try {

        setLoading(true);

        const res =
          await api.get(
            "/cockpit/monitoring",
          );

        setMonitoring(
          res.monitoring,
        );

      } catch (e) {

        console.error(
          "Unable to load monitoring",
          e,
        );

      } finally {

        setLoading(false);

      }

    }, []);

  /* ======================================================= */

  useEffect(() => {

    refresh();

  }, [refresh]);

  /* ======================================================= */

  return {

    loading,

    monitoring,

    refresh,

  };

}
