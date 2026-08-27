"use client";

import {
  RefreshCw,
} from "lucide-react";

import {
  useCockpitMonitoring,
} from "@/hooks/useCockpitMonitoring";


/* ========================================================= */

export default function MonitoringPanel() {

  const {
    loading,
    monitoring,
    refresh,
  } = useCockpitMonitoring();


  /* ========================================================
     VALUES
  ======================================================== */

  const destock = (
    monitoring?.destock
  );

  const translation = (
    monitoring?.translation
  );

  const destockProgress = (
    destock?.progress_pct
    ?? 0
  );

  const translationProgress = (
    translation?.pct_fully_translated
    ?? 0
  );


  /* ========================================================
     RENDER
  ======================================================== */

  return (

    <div className="rounded-xl border bg-white p-6">

      {/* ================================================= */}
      {/* HEADER */}
      {/* ================================================= */}

      <div className="mb-6 flex items-center justify-between">

        <div>

          <h2 className="text-xl font-semibold">

            Monitoring

          </h2>

          <p className="text-sm text-gray-500">

            Live platform status.

          </p>

        </div>

        <button
          type="button"
          onClick={
            refresh
          }
          disabled={
            loading
          }
          className="rounded border px-3 py-2 hover:bg-gray-50 disabled:opacity-50"
        >

          <RefreshCw
            size={16}
            className={
              loading
                ? "animate-spin"
                : ""
            }
          />

        </button>

      </div>


      {/* ================================================= */}
      {/* LOADING */}
      {/* ================================================= */}

      {loading && !monitoring && (

        <div className="text-gray-500">

          Loading...

        </div>

      )}


      {/* ================================================= */}
      {/* MONITORING */}
      {/* ================================================= */}

      {monitoring && (

        <div className="grid gap-4 md:grid-cols-2">

          {/* ============================================= */}
          {/* DESTOCK */}
          {/* ============================================= */}

          <div className="rounded-lg border p-5">

            <div className="text-sm text-gray-500">

              Destock

            </div>

            <div className="mt-3 text-3xl font-semibold">

              {destockProgress}%

            </div>

            <div className="mt-3 h-2 overflow-hidden rounded-full bg-gray-100">

              <div
                className="h-full rounded-full bg-ratecard-blue transition-all"
                style={{
                  width:
                    `${Math.min(
                      Math.max(
                        destockProgress,
                        0,
                      ),
                      100,
                    )}%`,
                }}
              />

            </div>

            <div className="mt-3 text-sm text-gray-500">

              {destock?.processed ?? 0}

              {" / "}

              {destock?.total ?? 0}

              {" processed"}

            </div>

            <div className="mt-2 flex flex-wrap gap-x-4 gap-y-1 text-xs text-gray-400">

              <span>

                {destock?.stored ?? 0}
                {" stored"}

              </span>

              <span>

                {destock?.processing ?? 0}
                {" processing"}

              </span>

              <span
                className={
                  (destock?.errors ?? 0) > 0
                    ? "text-red-600"
                    : ""
                }
              >

                {destock?.errors ?? 0}
                {" errors"}

              </span>

            </div>

          </div>


          {/* ============================================= */}
          {/* TRANSLATION */}
          {/* ============================================= */}

          <div className="rounded-lg border p-5">

            <div className="text-sm text-gray-500">

              Translation EN → FR

            </div>

            <div className="mt-3 text-3xl font-semibold">

              {translationProgress}%

            </div>

            <div className="mt-3 h-2 overflow-hidden rounded-full bg-gray-100">

              <div
                className="h-full rounded-full bg-green-600 transition-all"
                style={{
                  width:
                    `${Math.min(
                      Math.max(
                        translationProgress,
                        0,
                      ),
                      100,
                    )}%`,
                }}
              />

            </div>

            <div className="mt-3 text-sm text-gray-500">

              {translation?.fully_translated ?? 0}

              {" / "}

              {translation?.english_source_ready ?? 0}

              {" translated"}

            </div>

            <div className="mt-2 flex flex-wrap gap-x-4 gap-y-1 text-xs text-gray-400">

              <span
                className={
                  (
                    translation
                      ?.missing_translation
                    ?? 0
                  ) > 0

                    ? "text-amber-600"

                    : ""
                }
              >

                {translation?.missing_translation ?? 0}

                {" remaining"}

              </span>

              <span
                className={
                  (
                    translation
                      ?.english_source_missing
                    ?? 0
                  ) > 0

                    ? "text-red-600"

                    : ""
                }
              >

                {translation?.english_source_missing ?? 0}

                {" without English source"}

              </span>

            </div>

          </div>

        </div>

      )}

    </div>

  );

}
