"use client";

import { useState } from "react";

import type {
  QualityRow,
} from "@/types/cockpit";

import CockpitHeader from "@/components/cockpit/CockpitHeader";
import MonitoringPanel from "@/components/cockpit/MonitoringPanel";
import OperationsPanel from "@/components/cockpit/OperationsPanel";
import QualityPanel from "@/components/cockpit/QualityPanel";
import ResultsPanel from "@/components/cockpit/ResultsPanel";

/* ========================================================= */

export default function CockpitPage() {

  const [
    resultsTitle,
    setResultsTitle,
  ] = useState("");

  const [
    results,
    setResults,
  ] = useState<QualityRow[]>([]);

  /* ======================================================= */

  return (

    <div className="space-y-8">

      {/* ===================================================== */}
      {/* HEADER */}
      {/* ===================================================== */}

      <CockpitHeader />

      {/* ===================================================== */}
      {/* MONITORING + OPERATIONS */}
      {/* ===================================================== */}

      <div className="grid gap-6 xl:grid-cols-2">

        <MonitoringPanel />

        <OperationsPanel />

      </div>

      {/* ===================================================== */}
      {/* QUALITY */}
      {/* ===================================================== */}

      <QualityPanel

        onResults={(
          title,
          rows,
        ) => {

          setResultsTitle(
            title,
          );

          setResults(
            rows,
          );

        }}

      />

      {/* ===================================================== */}
      {/* RESULTS */}
      {/* ===================================================== */}

      <ResultsPanel

        title={resultsTitle}

        rows={results}

      />

    </div>

  );

}
