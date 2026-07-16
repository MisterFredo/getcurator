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
  ): Promise<QualityRow[]> {

    try {

      setLoading(true);

      const res =
        await api.get(
          `/cockpit/quality/${endpoint}`,
        );

      const data =
        res.results || [];

      setRows(data);

      return data;

    } catch (e) {

      console.error(
        "Unable to load quality report",
        e,
      );

      setRows([]);

      return [];

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
