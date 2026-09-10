"use client";

import Link from "next/link";

import {
  useNumbersKnowledge,
} from "@/hooks/useNumbersKnowledge";

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
   PROGRESS
========================================================= */

function ProgressBar({
  value,
}: {
  value: number;
}) {

  const progress = Math.max(
    0,
    Math.min(
      value,
      100,
    ),
  );

  return (

    <div>

      <div
        className="
          h-2
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

      <p className="mt-1 text-right text-xs text-gray-500">
        {progress.toFixed(2)} %
      </p>

    </div>
  );
}

/* =========================================================
   COMPONENT
========================================================= */

export default function NumbersOperationsPanel() {

  const {
    monitoring:
      transformationMonitoring,

    action:
      transformationAction,

    error:
      transformationError,

    continuousRunning:
      transformationRunning,

    continuousProcessed,

    retryFailed,

    startContinuousBackfill,
    stopContinuousBackfill,
  } = useNumbersMonitoring();

  const {
    monitoring:
      knowledgeMonitoring,

    action:
      knowledgeAction,

    error:
      knowledgeError,

    continuousRunning:
      knowledgeRunning,

    continuousBuilt,

    startContinuous:
      startKnowledge,

    stopContinuous:
      stopKnowledge,
  } = useNumbersKnowledge();

  const transformationBusy =
    transformationAction !== null;

  const knowledgeBusy =
    knowledgeAction !== null;

  return (

    <section className="space-y-4">

      {/* HEADER */}

      <div
        className="
          flex
          items-center
          justify-between
          gap-4
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
            Numbers
          </h2>

          <p className="mt-1 text-sm text-gray-500">
            Transform article Numbers, then update selected Knowledge entities.
          </p>

        </div>

        <Link
          href="/admin/numbers"
          className="
            text-sm
            font-medium
            text-ratecard-blue
            hover:underline
          "
        >
          Open Numbers
        </Link>

      </div>

      {/* CARDS */}

      <div
        className="
          grid
          grid-cols-1
          gap-4
          xl:grid-cols-2
        "
      >

        {/* TRANSFORMATION */}

        <article
          className="
            rounded-xl
            border
            border-gray-200
            bg-white
            p-5
          "
        >

          <div
            className="
              flex
              items-start
              justify-between
              gap-4
            "
          >

            <div>

              <h3 className="font-semibold text-gray-900">
                Numbers transformation
              </h3>

              <p className="mt-1 text-sm text-gray-500">
                Normalize and validate Numbers from published contents.
              </p>

            </div>

            <Link
              href="/admin/numbers"
              className="
                shrink-0
                text-xs
                font-medium
                text-ratecard-blue
                hover:underline
              "
            >
              Details
            </Link>

          </div>

          {transformationMonitoring ? (

            <>

              <div
                className="
                  mt-5
                  grid
                  grid-cols-3
                  gap-3
                "
              >

                <div>

                  <p className="text-xs text-gray-500">
                    Pending
                  </p>

                  <p className="mt-1 text-xl font-semibold text-amber-700">
                    {formatNumber(
                      transformationMonitoring.pending_contents,
                    )}
                  </p>

                </div>

                <div>

                  <p className="text-xs text-gray-500">
                    Completed
                  </p>

                  <p className="mt-1 text-xl font-semibold text-emerald-700">
                    {formatNumber(
                      transformationMonitoring.completed_contents,
                    )}
                  </p>

                </div>

                <div>

                  <p className="text-xs text-gray-500">
                    Failed
                  </p>

                  <p
                    className={`
                      mt-1
                      text-xl
                      font-semibold
                      ${
                        transformationMonitoring.failed_contents > 0
                          ? "text-red-700"
                          : "text-gray-700"
                      }
                    `}
                  >
                    {formatNumber(
                      transformationMonitoring.failed_contents,
                    )}
                  </p>

                </div>

              </div>

              <div className="mt-5">

                <ProgressBar
                  value={
                    transformationMonitoring.progress_percent
                  }
                />

              </div>

              {transformationRunning && (

                <div
                  className="
                    mt-4
                    rounded-lg
                    border
                    border-emerald-200
                    bg-emerald-50
                    p-3
                    text-sm
                    text-emerald-800
                  "
                >
                  Continuous processing ·{" "}
                  {formatNumber(
                    continuousProcessed,
                  )}{" "}
                  contents processed during this session
                </div>
              )}

              {transformationError && (

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
                  {transformationError}
                </div>
              )}

              <div
                className="
                  mt-5
                  flex
                  flex-wrap
                  gap-2
                "
              >

                {transformationRunning ? (

                  <button
                    type="button"
                    onClick={
                      stopContinuousBackfill
                    }
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
                    onClick={
                      startContinuousBackfill
                    }
                    disabled={
                      transformationBusy
                      || knowledgeBusy
                      || transformationMonitoring.pending_contents === 0
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
                    Continue Numbers
                  </button>

                )}

                <button
                  type="button"
                  onClick={retryFailed}
                  disabled={
                    transformationBusy
                    || knowledgeBusy
                    || transformationMonitoring.failed_contents === 0
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
                  Retry failures
                </button>

              </div>

            </>

          ) : (

            <p className="mt-5 text-sm text-gray-500">
              Loading transformation monitoring…
            </p>

          )}

        </article>

        {/* KNOWLEDGE */}

        <article
          className="
            rounded-xl
            border
            border-gray-200
            bg-white
            p-5
          "
        >

          <div
            className="
              flex
              items-start
              justify-between
              gap-4
            "
          >

            <div>

              <h3 className="font-semibold text-gray-900">
                Numbers Knowledge
              </h3>

              <p className="mt-1 text-sm text-gray-500">
                Update the Numbers notebook of selected Knowledge entities.
              </p>

            </div>

            <Link
              href="/admin/knowledge"
              className="
                shrink-0
                text-xs
                font-medium
                text-ratecard-blue
                hover:underline
              "
            >
              Details
            </Link>

          </div>

          {knowledgeMonitoring ? (

            <>

              <div
                className="
                  mt-5
                  grid
                  grid-cols-3
                  gap-3
                "
              >

                <div>

                  <p className="text-xs text-gray-500">
                    Pending entities
                  </p>

                  <p className="mt-1 text-xl font-semibold text-amber-700">
                    {formatNumber(
                      knowledgeMonitoring.pending_entities,
                    )}
                  </p>

                </div>

                <div>

                  <p className="text-xs text-gray-500">
                    Up to date
                  </p>

                  <p className="mt-1 text-xl font-semibold text-emerald-700">
                    {formatNumber(
                      knowledgeMonitoring.up_to_date_entities,
                    )}
                  </p>

                </div>

                <div>

                  <p className="text-xs text-gray-500">
                    Pending observations
                  </p>

                  <p className="mt-1 text-xl font-semibold text-gray-900">
                    {formatNumber(
                      knowledgeMonitoring.pending_observations,
                    )}
                  </p>

                </div>

              </div>

              <div className="mt-5">

                <ProgressBar
                  value={
                    knowledgeMonitoring.progress_percent
                  }
                />

              </div>

              {knowledgeRunning && (

                <div
                  className="
                    mt-4
                    rounded-lg
                    border
                    border-emerald-200
                    bg-emerald-50
                    p-3
                    text-sm
                    text-emerald-800
                  "
                >
                  Continuous update ·{" "}
                  {formatNumber(
                    continuousBuilt,
                  )}{" "}
                  entities built during this session
                </div>
              )}

              {knowledgeError && (

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
                  {knowledgeError}
                </div>
              )}

              <div
                className="
                  mt-5
                  flex
                  flex-wrap
                  gap-2
                "
              >

                {knowledgeRunning ? (

                  <button
                    type="button"
                    onClick={
                      stopKnowledge
                    }
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
                    onClick={
                      startKnowledge
                    }
                    disabled={
                      transformationBusy
                      || knowledgeBusy
                      || knowledgeMonitoring.pending_entities === 0
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

            </>

          ) : (

            <p className="mt-5 text-sm text-gray-500">
              Loading Numbers Knowledge monitoring…
            </p>

          )}

        </article>

      </div>

    </section>
  );
}
