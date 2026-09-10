"use client";

import {
  useNumbersMonitoring,
} from "@/hooks/useNumbersMonitoring";

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
   STAT CARD
========================================================= */

function StatCard({
  label,
  value,
  tone = "default",
}: {
  label: string;
  value: number | string;
  tone?:
    | "default"
    | "success"
    | "warning"
    | "danger";
}) {

  const toneClass = {

    default:
      "border-gray-200 bg-white text-gray-900",

    success:
      "border-emerald-200 bg-emerald-50 text-emerald-900",

    warning:
      "border-amber-200 bg-amber-50 text-amber-900",

    danger:
      "border-red-200 bg-red-50 text-red-900",

  }[tone];

  return (

    <div
      className={`
        rounded-xl
        border
        p-4
        ${toneClass}
      `}
    >

      <p className="text-xs font-medium uppercase tracking-wide opacity-70">
        {label}
      </p>

      <p className="mt-2 text-2xl font-semibold">
        {value}
      </p>

    </div>
  );
}

/* =========================================================
   COMPONENT
========================================================= */

export default function NumbersTransformation() {

  const {
    monitoring,
    lastRun,

    loading,
    action,
    error,

    reload,
    continueBackfill,
    retryFailed,
  } = useNumbersMonitoring();

  /* =======================================================
     LOADING
  ======================================================= */

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
        Chargement du monitoring Numbers…
      </div>
    );
  }

  /* =======================================================
     NO DATA
  ======================================================= */

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
        {error || "Monitoring Numbers indisponible."}
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

  /* =======================================================
     RENDER
  ======================================================= */

  return (

    <div className="space-y-6">

      {/* PROGRESS */}

      <section
        className="
          rounded-xl
          border
          border-gray-200
          bg-white
          p-6
        "
      >

        <div
          className="
            flex
            flex-col
            gap-4
            md:flex-row
            md:items-center
            md:justify-between
          "
        >

          <div>

            <h2 className="text-lg font-semibold text-gray-900">
              Transformation des Numbers
            </h2>

            <p className="mt-1 text-sm text-gray-500">
              Normalisation, validation et association aux entités officielles.
            </p>

          </div>

          <div className="text-left md:text-right">

            <p className="text-2xl font-semibold text-ratecard-blue">
              {progress.toFixed(2)} %
            </p>

            <p className="text-xs text-gray-500">
              Version {monitoring.transformer_version}
            </p>

          </div>

        </div>

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

        <div
          className="
            mt-3
            flex
            flex-wrap
            gap-x-6
            gap-y-2
            text-sm
            text-gray-600
          "
        >

          <span>
            {formatNumber(
              monitoring.completed_contents,
            )}
            {" / "}
            {formatNumber(
              monitoring.total_contents,
            )}
            {" contenus terminés"}
          </span>

          <span>
            {formatNumber(
              monitoring.pending_contents,
            )}
            {" en attente"}
          </span>

          <span>
            {formatNumber(
              monitoring.total_raw_numbers,
            )}
            {" Numbers bruts"}
          </span>

        </div>

      </section>

      {/* CONTENT STATUS */}

      <section>

        <h2 className="mb-3 text-sm font-semibold text-gray-700">
          Contenus
        </h2>

        <div
          className="
            grid
            grid-cols-1
            gap-4
            sm:grid-cols-2
            xl:grid-cols-4
          "
        >

          <StatCard
            label="Terminés"
            value={formatNumber(
              monitoring.completed_contents,
            )}
            tone="success"
          />

          <StatCard
            label="En attente"
            value={formatNumber(
              monitoring.pending_contents,
            )}
            tone="warning"
          />

          <StatCard
            label="En cours"
            value={formatNumber(
              monitoring.processing_contents,
            )}
          />

          <StatCard
            label="En erreur"
            value={formatNumber(
              monitoring.failed_contents,
            )}
            tone={
              monitoring.failed_contents > 0
                ? "danger"
                : "default"
            }
          />

        </div>

      </section>

      {/* OBSERVATIONS */}

      <section>

        <h2 className="mb-3 text-sm font-semibold text-gray-700">
          Observations produites
        </h2>

        <div
          className="
            grid
            grid-cols-1
            gap-4
            sm:grid-cols-2
            xl:grid-cols-4
          "
        >

          <StatCard
            label="Total"
            value={formatNumber(
              monitoring.total_observations,
            )}
          />

          <StatCard
            label="Acceptées"
            value={formatNumber(
              monitoring.accepted_observations,
            )}
            tone="success"
          />

          <StatCard
            label="À vérifier"
            value={formatNumber(
              monitoring.review_observations,
            )}
            tone="warning"
          />

          <StatCard
            label="Rejetées"
            value={formatNumber(
              monitoring.rejected_observations,
            )}
          />

        </div>

      </section>

      {/* ACTIONS */}

      <section
        className="
          rounded-xl
          border
          border-gray-200
          bg-white
          p-6
        "
      >

        <div
          className="
            flex
            flex-col
            gap-4
            lg:flex-row
            lg:items-center
            lg:justify-between
          "
        >

          <div>

            <h2 className="text-base font-semibold text-gray-900">
              Actions
            </h2>

            <p className="mt-1 text-sm text-gray-500">
              Chaque exécution traite au maximum cinq contenus.
            </p>

          </div>

          <div className="flex flex-wrap gap-3">

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
                disabled:cursor-not-allowed
                disabled:opacity-50
              "
            >
              Actualiser
            </button>

            <button
              type="button"
              onClick={retryFailed}
              disabled={
                busy
                || monitoring.failed_contents === 0
              }
              className="
                rounded-lg
                border
                border-red-300
                bg-white
                px-4
                py-2
                text-sm
                font-medium
                text-red-700
                hover:bg-red-50
                disabled:cursor-not-allowed
                disabled:opacity-50
              "
            >
              {action === "retry"
                ? "Retraitement…"
                : `Retraiter les erreurs (${monitoring.failed_contents})`
              }
            </button>

            <button
              type="button"
              onClick={continueBackfill}
              disabled={
                busy
                || monitoring.pending_contents === 0
              }
              className="
                rounded-lg
                bg-ratecard-blue
                px-4
                py-2
                text-sm
                font-medium
                text-white
                hover:opacity-90
                disabled:cursor-not-allowed
                disabled:opacity-50
              "
            >
              {action === "continue"
                ? "Transformation…"
                : "Traiter 5 contenus"
              }
            </button>

          </div>

        </div>

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

      </section>

      {/* LAST RUN */}

      {lastRun && (

        <section
          className="
            rounded-xl
            border
            border-gray-200
            bg-white
            p-6
          "
        >

          <h2 className="text-base font-semibold text-gray-900">
            Dernière exécution
          </h2>

          <div
            className="
              mt-4
              grid
              grid-cols-2
              gap-4
              md:grid-cols-4
            "
          >

            <div>

              <p className="text-xs text-gray-500">
                Sélectionnés
              </p>

              <p className="mt-1 font-semibold text-gray-900">
                {lastRun.selected_count}
              </p>

            </div>

            <div>

              <p className="text-xs text-gray-500">
                Traités
              </p>

              <p className="mt-1 font-semibold text-emerald-700">
                {lastRun.processed_count}
              </p>

            </div>

            <div>

              <p className="text-xs text-gray-500">
                Observations
              </p>

              <p className="mt-1 font-semibold text-gray-900">
                {lastRun.storage.observations_saved}
              </p>

            </div>

            <div>

              <p className="text-xs text-gray-500">
                Erreurs
              </p>

              <p
                className={`
                  mt-1
                  font-semibold
                  ${
                    lastRun.failed_count > 0
                      ? "text-red-700"
                      : "text-gray-900"
                  }
                `}
              >
                {lastRun.failed_count}
              </p>

            </div>

          </div>

          {lastRun.failures.length > 0 && (

            <div className="mt-5 space-y-2">

              {lastRun.failures.map(
                (failure) => (

                  <div
                    key={failure.id_content}
                    className="
                      rounded-lg
                      border
                      border-red-200
                      bg-red-50
                      p-3
                      text-sm
                      text-red-700
                    "
                  >

                    <p className="font-medium">
                      {failure.id_content}
                    </p>

                    <p className="mt-1">
                      {failure.error}
                    </p>

                  </div>
                ),
              )}

            </div>
          )}

        </section>
      )}

    </div>
  );
}
