"use client";

import CockpitHeader from "@/components/cockpit/CockpitHeader";
import MonitoringPanel from "@/components/cockpit/MonitoringPanel";
import OperationsPanel from "@/components/cockpit/OperationsPanel";
import QualityPanel from "@/components/cockpit/QualityPanel";

export default function CockpitPage() {

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

      <QualityPanel />

    </div>

  );

}
