"use client";

import { useState } from "react";

import { api } from "@/lib/api";

import type {
  QualityRow,
} from "@/types/cockpit";

/* ========================================================= */

export function useCockpitQuality() {

  const [
    loading,
    setLoading,
  ] = useState(false);

  const [
    rows,
    setRows,
  ] = useState<QualityRow[]>([]);

  /* ======================================================= */

  async function load(
    endpoint: string,
  ) {

    try {

      setLoading(true);

      const res =
        await api.get(
          `/cockpit/quality/${endpoint}`,
        );

      setRows(
        res.results || [],
      );

    } catch (e) {

      console.error(
        "Unable to load quality report",
        e,
      );

      setRows([]);

    } finally {

      setLoading(false);

    }

  }

  /* ======================================================= */

  return {

    loading,

    rows,

    load,

  };

}
