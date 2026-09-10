"use client";

import {
  useNumbersKnowledge,
} from "@/hooks/useNumbersKnowledge";

/* =========================================================
   HELPERS
========================================================= */

function formatNumber(
  value: number,
) {

  return new Intl.NumberFormat(
    "fr-FR",
  ).format(value);

}

/* =========================================================
   CARD
========================================================= */

function Metric({
  label,
  value,
}: {
  label: string;
  value: number | string;
}) {

  return (

    <div
      className="
        rounded-lg
        border
        border-gray-200
        bg-gray-50
        p-3
      "
    >

      <p
        className="
          text-xs
          font-medium
          uppercase
          tracking-wide
          text-gray-500
        "
      >
        {label}
      </p>

      <p
        className="
          mt-1
          text-xl
          font-semibold
          text-gray-900
        "
      >
        {value}
      </p>

    </div>
  );
}

/* =========================================================
   COMPONENT
========================================================= */

export default function NumbersKnowledgeOperations() {

  const {
    monitoring,
    lastRun,

    loading,
    action,
    error,

    continuousRunning,
    continuousBuilt,

    reload,
    runBatch,

    startContinuous,
    stopContinuous,
  } = useNumbersKnowledge();

  if (
    loading
    && !monitoring
  ) {

    return (

      <div
        className="
          rounded-xl
          border
          border-gray-200
          bg-white
          p-6
          text-sm
          text-gray-500
        "
      >
        Loading Numbers Knowledge…
      </div>
    );
  }

  if (!monitoring) {

    return (

      <div
        className="
          rounded-xl
          border
          border-red-200
          bg-red-50
          p-6
          text-sm
          text-red-700
        "
      >
        {error || "Numbers Knowledge monitoring unavailable."}
      </div>
    );
  }

  const busy =
    action !== null;

  const progress = Math.max(
    0,
    Math.min(
      monitoring.progress_percent,
      100,
    ),
  );

  return (

    <section
      className="
        rounded-xl
        border
        border-gray-200
        bg-white
        p-6
      "
    >

      {/* HEADER */}

      <div
        className="
          flex
          flex-col
          gap-4
          lg:flex-row
          lg:items-start
          lg:justify-between
        "
      >

        <div>

          <h2
            className="
              text-lg
              font-semibold
              text-gray-900
            "
          >
            Numbers Knowledge
          </h2>

          <p className="mt-1 text-sm text-gray-500">
            Build and update the Numbers notebook for selected Knowledge
            entities.
          </p>

        </div>

        <div className="text-left lg:text-right">

          <p
            className="
              text-2xl
              font-semibold
              text-ratecard-blue
            "
          >
            {progress.toFixed(2)} %
          </p>

          <p className="text-xs text-gray-500">
            {formatNumber(
              monitoring.processed_observations,
            )}
            {" / "}
            {formatNumber(
              monitoring.total_observations,
            )}
            {" observations"}
          </p>

        </div>

      </div>

      {/* PROGRESS */}

      <div
        className="
          mt-5
          h-3
          overflow-hidden
          rounded-full
          bg-gray-100
        "
      >

        <div
          className="
            h-full
            rounded-full
            bg-ratecard-blue
            transition-all
            duration-300
          "
          style={{
            width: `${progress}%`,
          }}
        />

      </div>

      {/* METRICS */}

      <div
        className="
          mt-5
          grid
          grid-cols-2
          gap-3
          lg:grid-cols-5
        "
      >

        <Metric
          label="Entités"
          value={formatNumber(
            monitoring.total_entities,
          )}
        />

        <Metric
          label="À jour"
          value={formatNumber(
            monitoring.up_to_date_entities,
          )}
        />

        <Metric
          label="À traiter"
          value={formatNumber(
            monitoring.pending_entities,
          )}
        />

        <Metric
          label="Non commencées"
          value={formatNumber(
            monitoring.not_started_entities,
          )}
        />

        <Metric
          label="Observations en attente"
          value={formatNumber(
            monitoring.pending_observations,
          )}
        />

      </div>

      {/* ACTIONS */}

      <div
        className="
          mt-6
          flex
          flex-col
          gap-4
          border-t
          border-gray-100
          pt-5
          lg:flex-row
          lg:items-center
          lg:justify-between
        "
      >

        <div className="text-sm text-gray-500">

          {continuousRunning ? (

            <span className="text-emerald-700">
              Continuous update running ·{" "}
              {formatNumber(
                continuousBuilt,
              )}{" "}
              entities built during this session
            </span>

          ) : (

            <span>
              Each batch processes up to five eligible entities.
            </span>

          )}

        </div>

        <div className="flex flex-wrap gap-2">

          <button
            type="button"
            onClick={() => reload()}
            disabled={busy}
            className="
              rounded-lg
              border
              border-gray-300
              bg-white
              px-4
              py-2
              text-sm
              font-medium
              text-gray-700
              hover:bg-gray-50
              disabled:opacity-50
            "
          >
            Refresh
          </button>

          <button
            type="button"
            onClick={runBatch}
            disabled={
              busy
              || monitoring.pending_entities === 0
            }
            className="
              rounded-lg
              border
              border-ratecard-blue
              bg-white
              px-4
              py-2
              text-sm
              font-medium
              text-ratecard-blue
              hover:bg-blue-50
              disabled:cursor-not-allowed
              disabled:opacity-50
            "
          >
            {action === "batch"
              ? "Updating…"
              : "Update 5 entities"
            }
          </button>

          {continuousRunning ? (

            <button
              type="button"
              onClick={stopContinuous}
              className="
                rounded-lg
                border
                border-amber-300
                bg-amber-50
                px-4
                py-2
                text-sm
                font-medium
                text-amber-800
                hover:bg-amber-100
              "
            >
              Stop after current batch
            </button>

          ) : (

            <button
              type="button"
              onClick={startContinuous}
              disabled={
                busy
                || monitoring.pending_entities === 0
              }
              className="
                rounded-lg
                bg-emerald-600
                px-4
                py-2
                text-sm
                font-medium
                text-white
                hover:bg-emerald-700
                disabled:cursor-not-allowed
                disabled:opacity-50
              "
            >
              Continue Numbers Knowledge
            </button>

          )}

        </div>

      </div>

      {/* ERROR */}

      {error && (

        <div
          className="
            mt-4
            rounded-lg
            border
            border-red-200
            bg-red-50
            p-3
            text-sm
            text-red-700
          "
        >
          {error}
        </div>
      )}

      {/* LAST RUN */}

      {lastRun && (

        <div
          className="
            mt-4
            rounded-lg
            border
            border-gray-200
            bg-gray-50
            p-3
            text-sm
            text-gray-600
          "
        >
          Last batch:{" "}
          <strong>
            {lastRun.built_entities}
          </strong>
          {" built · "}
          <strong>
            {lastRun.failed_entities}
          </strong>
          {" failed"}
        </div>
      )}

    </section>
  );
}
