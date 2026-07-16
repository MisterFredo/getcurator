"use client";

import { RefreshCw } from "lucide-react";

import { useCockpitMonitoring } from "@/hooks/useCockpitMonitoring";

export default function MonitoringPanel() {

  const {
    loading,
    monitoring,
    refresh,
  } = useCockpitMonitoring();

  return (

    <div className="border rounded-xl bg-white p-6">

      <div className="flex items-center justify-between mb-6">

        <div>

          <h2 className="text-xl font-semibold">
            Monitoring
          </h2>

          <p className="text-sm text-gray-500">
            Live platform status.
          </p>

        </div>

        <button
          onClick={refresh}
          className="border rounded px-3 py-2 hover:bg-gray-50"
        >
          <RefreshCw size={16} />
        </button>

      </div>

      {loading && (

        <div className="text-gray-500">
          Loading...
        </div>

      )}

      {!loading && monitoring && (

        <div className="grid md:grid-cols-2 gap-4">

          <div className="border rounded-lg p-5">

            <div className="text-sm text-gray-500">
              Destock
            </div>

            <div className="mt-3 text-3xl font-semibold">
              {monitoring.destock.progress_pct}%
            </div>

            <div className="mt-2 text-sm text-gray-500">

              {monitoring.destock.processed}

              {" / "}

              {monitoring.destock.total}

              {" processed"}

            </div>

          </div>

          <div className="border rounded-lg p-5">

            <div className="text-sm text-gray-500">
              Translation
            </div>

            <div className="mt-3 text-3xl font-semibold">

              {monitoring.translation.pct_fully_translated}%

            </div>

            <div className="mt-2 text-sm text-gray-500">

              {monitoring.translation.missing_translation}

              {" remaining"}

            </div>

          </div>

        </div>

      )}

    </div>

  );

}
