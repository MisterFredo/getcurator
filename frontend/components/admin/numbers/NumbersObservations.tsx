"use client";

import {
  FormEvent,
  useState,
} from "react";

import {
  useNumberObservations,
} from "@/hooks/useNumberObservations";

import type {
  NumberObservation,
  NumberStatus,
} from "@/types/numbers";

/* =========================================================
   CONFIG
========================================================= */

const STATUS_TABS: Array<{
  status: NumberStatus;
  label: string;
}> = [
  {
    status: "ACCEPTED",
    label: "Acceptés",
  },
  {
    status: "REVIEW",
    label: "À vérifier",
  },
  {
    status: "REJECTED",
    label: "Mis de côté",
  },
];

/* =========================================================
   HELPERS
========================================================= */

function formatNumber(
  value: number,
) {

  return new Intl.NumberFormat(
    "fr-FR",
    {
      maximumFractionDigits: 4,
    },
  ).format(value);

}

function formatObservationValue(
  observation: NumberObservation,
) {

  let value = "—";

  if (
    observation.value_min !== null
    && observation.value_max !== null
  ) {

    value = (
      `${formatNumber(observation.value_min)}`
      + " – "
      + `${formatNumber(observation.value_max)}`
    );

  } else if (
    observation.value !== null
  ) {

    value = formatNumber(
      observation.value,
    );

  }

  const parts = [
    value,
  ];

  if (
    observation.scale
    && observation.scale !== "NONE"
  ) {

    parts.push(
      observation.scale,
    );

  }

  if (observation.unit) {

    parts.push(
      observation.unit,
    );

  }

  return parts.join(" ");

}

function formatDate(
  value: string | null,
) {

  if (!value) {
    return "Date inconnue";
  }

  return new Intl.DateTimeFormat(
    "fr-FR",
    {
      day: "2-digit",
      month: "2-digit",
      year: "numeric",
    },
  ).format(
    new Date(value),
  );

}

/* =========================================================
   STATUS BADGE
========================================================= */

function StatusBadge({
  status,
}: {
  status: NumberStatus;
}) {

  const config = {

    ACCEPTED: {
      label: "Accepté",
      className:
        "border-emerald-200 bg-emerald-50 text-emerald-700",
    },

    REVIEW: {
      label: "À vérifier",
      className:
        "border-amber-200 bg-amber-50 text-amber-700",
    },

    REJECTED: {
      label: "Mis de côté",
      className:
        "border-gray-200 bg-gray-100 text-gray-600",
    },

  }[status];

  return (

    <span
      className={`
        inline-flex
        rounded-full
        border
        px-2.5
        py-1
        text-xs
        font-medium
        ${config.className}
      `}
    >
      {config.label}
    </span>
  );
}

/* =========================================================
   OBSERVATION ROW
========================================================= */

function ObservationRow({
  observation,
  selected,
  onToggle,
}: {
  observation: NumberObservation;
  selected: boolean;
  onToggle: () => void;
}) {

  return (

    <div
      className={`
        rounded-xl
        border
        p-4
        transition-colors
        ${
          selected
            ? "border-ratecard-blue bg-blue-50/40"
            : "border-gray-200 bg-white"
        }
      `}
    >

      <div
        className="
          flex
          items-start
          gap-4
        "
      >

        {/* CHECKBOX */}

        <input
          type="checkbox"
          checked={selected}
          onChange={onToggle}
          className="
            mt-1
            h-4
            w-4
            rounded
            border-gray-300
            text-ratecard-blue
            focus:ring-ratecard-blue
          "
          aria-label={
            `Sélectionner ${observation.label || observation.raw_line}`
          }
        />

        {/* CONTENT */}

        <div className="min-w-0 flex-1">

          <div
            className="
              flex
              flex-col
              gap-3
              lg:flex-row
              lg:items-start
              lg:justify-between
            "
          >

            <div className="min-w-0">

              <div
                className="
                  flex
                  flex-wrap
                  items-center
                  gap-2
                "
              >

                <StatusBadge
                  status={
                    observation.effective_status
                  }
                />

                {observation.metric_type && (

                  <span
                    className="
                      rounded-full
                      bg-blue-50
                      px-2.5
                      py-1
                      text-xs
                      font-medium
                      text-ratecard-blue
                    "
                  >
                    {observation.metric_type}
                  </span>
                )}

                {observation.value_status && (
                  observation.value_status
                  !== "UNKNOWN"
                ) && (

                  <span
                    className="
                      rounded-full
                      bg-purple-50
                      px-2.5
                      py-1
                      text-xs
                      font-medium
                      text-purple-700
                    "
                  >
                    {observation.value_status}
                  </span>
                )}

                {observation.manual_decision && (

                  <span
                    className="
                      rounded-full
                      bg-gray-100
                      px-2.5
                      py-1
                      text-xs
                      text-gray-600
                    "
                  >
                    Décision manuelle
                  </span>
                )}

              </div>

              <h3
                className="
                  mt-3
                  text-base
                  font-semibold
                  text-gray-900
                "
              >
                {observation.label || "Number sans label"}
              </h3>

              <p
                className="
                  mt-1
                  text-sm
                  text-gray-500
                "
              >
                {observation.raw_line}
              </p>

            </div>

            {/* VALUE */}

            <div
              className="
                shrink-0
                text-left
                lg:text-right
              "
            >

              <p
                className="
                  text-xl
                  font-semibold
                  text-gray-900
                "
              >
                {formatObservationValue(
                  observation,
                )}
              </p>

              <p className="mt-1 text-xs text-gray-500">
                {observation.zone || "Zone inconnue"}
                {" · "}
                {observation.period_label || "Période inconnue"}
              </p>

            </div>

          </div>

          {/* ENTITIES */}

          <div
            className="
              mt-4
              flex
              flex-wrap
              gap-2
            "
          >

            {observation.entities.length > 0 ? (

              observation.entities.map(
                (entity) => (

                  <span
                    key={
                      `${entity.entity_type}-${entity.entity_id}`
                    }
                    className="
                      rounded-md
                      border
                      border-gray-200
                      bg-gray-50
                      px-2.5
                      py-1
                      text-xs
                      text-gray-700
                    "
                  >
                    {entity.entity_label}
                    {" · "}
                    {entity.entity_type}
                  </span>
                ),
              )

            ) : (

              <span
                className="
                  rounded-md
                  border
                  border-amber-200
                  bg-amber-50
                  px-2.5
                  py-1
                  text-xs
                  text-amber-700
                "
              >
                Aucune entité associée
              </span>

            )}

          </div>

          {/* SOURCE */}

          <div
            className="
              mt-4
              border-t
              border-gray-100
              pt-3
            "
          >

            <p
              className="
                text-sm
                font-medium
                text-gray-700
              "
            >
              {observation.content_title || "Contenu sans titre"}
            </p>

            <p className="mt-1 text-xs text-gray-500">
              Publié le {formatDate(observation.published_at)}
              {" · "}
              Confiance{" "}
              {Math.round(
                observation.confidence * 100,
              )}
              %
            </p>

          </div>

          {/* REASON */}

          {(
            observation.reason
            || observation.review_reason
          ) && (

            <div
              className="
                mt-3
                rounded-lg
                bg-gray-50
                p-3
                text-xs
                text-gray-600
              "
            >

              {observation.review_reason
                || observation.reason
              }

            </div>
          )}

        </div>

      </div>

    </div>
  );
}

/* =========================================================
   COMPONENT
========================================================= */

export default function NumbersObservations() {

  const {
    status,
    query,
    offset,

    items,
    total,
    counts,

    selectedIds,
    selectedCount,
    allPageSelected,

    loading,
    moderating,
    error,
    lastModeration,

    pageSize,

    setStatus,
    setQuery,

    toggleSelection,
    selectAllPage,
    clearSelection,

    applyDecision,

    previousPage,
    nextPage,

    reload,
  } = useNumberObservations();

  const [
    searchValue,
    setSearchValue,
  ] = useState(
    query,
  );

  /* =======================================================
     SEARCH
  ======================================================= */

  function handleSearch(
    event: FormEvent,
  ) {

    event.preventDefault();

    setQuery(
      searchValue,
    );

  }

  function clearSearch() {

    setSearchValue("");

    setQuery("");

  }

  const firstVisible = (
    total === 0
      ? 0
      : offset + 1
  );

  const lastVisible = Math.min(
    offset + items.length,
    total,
  );

  const hasPrevious =
    offset > 0;

  const hasNext =
    offset + pageSize < total;

  /* =======================================================
     RENDER
  ======================================================= */

  return (

    <div className="space-y-5">

      {/* STATUS TABS */}

      <div
        className="
          flex
          flex-wrap
          gap-2
          border-b
          border-gray-200
          pb-3
        "
      >

        {STATUS_TABS.map(
          (tab) => {

            const active =
              status === tab.status;

            return (

              <button
                key={tab.status}
                type="button"
                onClick={() =>
                  setStatus(tab.status)
                }
                className={`
                  rounded-lg
                  px-4
                  py-2
                  text-sm
                  font-medium
                  transition-colors
                  ${
                    active
                      ? "bg-ratecard-blue text-white"
                      : "bg-gray-100 text-gray-700 hover:bg-gray-200"
                  }
                `}
              >
                {tab.label}
                {" "}
                ({counts[tab.status]})
              </button>
            );

          },
        )}

      </div>

      {/* SEARCH */}

      <form
        onSubmit={handleSearch}
        className="
          flex
          flex-col
          gap-3
          sm:flex-row
        "
      >

        <input
          type="search"
          value={searchValue}
          onChange={(event) =>
            setSearchValue(
              event.target.value,
            )
          }
          placeholder="Rechercher un chiffre, un contenu ou une entité…"
          className="
            min-w-0
            flex-1
            rounded-lg
            border
            border-gray-300
            px-4
            py-2
            text-sm
            outline-none
            focus:border-ratecard-blue
            focus:ring-1
            focus:ring-ratecard-blue
          "
        />

        <button
          type="submit"
          disabled={loading}
          className="
            rounded-lg
            bg-ratecard-blue
            px-4
            py-2
            text-sm
            font-medium
            text-white
            hover:opacity-90
            disabled:opacity-50
          "
        >
          Rechercher
        </button>

        {query && (

          <button
            type="button"
            onClick={clearSearch}
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
            "
          >
            Effacer
          </button>
        )}

      </form>

      {/* BULK TOOLBAR */}

      <div
        className="
          flex
          flex-col
          gap-3
          rounded-xl
          border
          border-gray-200
          bg-white
          p-4
          lg:flex-row
          lg:items-center
          lg:justify-between
        "
      >

        <div
          className="
            flex
            flex-wrap
            items-center
            gap-3
          "
        >

          <button
            type="button"
            onClick={
              allPageSelected
                ? clearSelection
                : selectAllPage
            }
            disabled={
              loading
              || items.length === 0
              || moderating
            }
            className="
              rounded-lg
              border
              border-gray-300
              bg-white
              px-3
              py-2
              text-sm
              font-medium
              text-gray-700
              hover:bg-gray-50
              disabled:opacity-50
            "
          >
            {allPageSelected
              ? "Tout désélectionner"
              : "Tout sélectionner sur la page"
            }
          </button>

          {selectedCount > 0 && (

            <button
              type="button"
              onClick={clearSelection}
              disabled={moderating}
              className="
                text-sm
                text-gray-500
                hover:text-gray-900
                disabled:opacity-50
              "
            >
              Effacer la sélection
            </button>
          )}

          <span className="text-sm text-gray-600">
            {selectedCount} sélectionné
            {selectedCount > 1 ? "s" : ""}
          </span>

        </div>

        <div className="flex flex-wrap gap-2">

          {status === "REVIEW" && (

            <button
              type="button"
              onClick={() =>
                applyDecision(
                  "ACCEPTED",
                )
              }
              disabled={
                selectedCount === 0
                || moderating
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
              {moderating
                ? "Traitement…"
                : "Accepter la sélection"
              }
            </button>
          )}

          {(
            status === "ACCEPTED"
            || status === "REVIEW"
          ) && (

            <button
              type="button"
              onClick={() =>
                applyDecision(
                  "REJECTED",
                )
              }
              disabled={
                selectedCount === 0
                || moderating
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
              {moderating
                ? "Traitement…"
                : "Mettre de côté"
              }
            </button>
          )}

          {status === "REJECTED" && (

            <button
              type="button"
              onClick={() =>
                applyDecision(
                  "REVIEW",
                )
              }
              disabled={
                selectedCount === 0
                || moderating
              }
              className="
                rounded-lg
                bg-amber-500
                px-4
                py-2
                text-sm
                font-medium
                text-white
                hover:bg-amber-600
                disabled:cursor-not-allowed
                disabled:opacity-50
              "
            >
              {moderating
                ? "Traitement…"
                : "Restaurer en À vérifier"
              }
            </button>
          )}

          <button
            type="button"
            onClick={reload}
            disabled={
              loading
              || moderating
            }
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
            Actualiser
          </button>

        </div>

      </div>

      {/* MODERATION RESULT */}

      {lastModeration && (

        <div
          className={`
            rounded-lg
            border
            p-4
            text-sm
            ${
              lastModeration.skipped_count > 0
                ? "border-amber-200 bg-amber-50 text-amber-800"
                : "border-emerald-200 bg-emerald-50 text-emerald-800"
            }
          `}
        >

          <p className="font-medium">
            {lastModeration.updated} Number
            {lastModeration.updated > 1 ? "s" : ""}
            {" mis à jour"}
            {lastModeration.skipped_count > 0
              ? (
                ` · ${lastModeration.skipped_count} non modifié`
                + (
                  lastModeration.skipped_count > 1
                    ? "s"
                    : ""
                )
              )
              : ""
            }
          </p>

          {lastModeration.skipped.length > 0 && (

            <div className="mt-2 space-y-1">

              {lastModeration.skipped.map(
                (skipped) => (

                  <p
                    key={skipped.id_number}
                    className="text-xs"
                  >
                    {skipped.id_number}
                    {" : "}
                    {skipped.reason}
                  </p>
                ),
              )}

            </div>
          )}

        </div>
      )}

      {/* ERROR */}

      {error && (

        <div
          className="
            rounded-lg
            border
            border-red-200
            bg-red-50
            p-4
            text-sm
            text-red-700
          "
        >
          {error}
        </div>
      )}

      {/* SUMMARY */}

      <div
        className="
          flex
          flex-wrap
          items-center
          justify-between
          gap-3
          text-sm
          text-gray-600
        "
      >

        <span>
          {firstVisible}
          {" – "}
          {lastVisible}
          {" sur "}
          {total}
        </span>

        {query && (

          <span>
            Recherche : “{query}”
          </span>
        )}

      </div>

      {/* LOADING */}

      {loading ? (

        <div
          className="
            rounded-xl
            border
            border-gray-200
            bg-white
            p-8
            text-center
            text-sm
            text-gray-500
          "
        >
          Chargement des observations…
        </div>

      ) : items.length === 0 ? (

        <div
          className="
            rounded-xl
            border
            border-gray-200
            bg-white
            p-8
            text-center
            text-sm
            text-gray-500
          "
        >
          Aucun Number dans cette catégorie.
        </div>

      ) : (

        <div className="space-y-3">

          {items.map(
            (observation) => (

              <ObservationRow
                key={
                  observation.id_number
                }
                observation={
                  observation
                }
                selected={
                  selectedIds.has(
                    observation.id_number,
                  )
                }
                onToggle={() =>
                  toggleSelection(
                    observation.id_number,
                  )
                }
              />

            ),
          )}

        </div>
      )}

      {/* PAGINATION */}

      <div
        className="
          flex
          items-center
          justify-between
          border-t
          border-gray-200
          pt-4
        "
      >

        <button
          type="button"
          onClick={previousPage}
          disabled={
            !hasPrevious
            || loading
            || moderating
          }
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
          Précédent
        </button>

        <span className="text-sm text-gray-500">
          Page{" "}
          {Math.floor(
            offset / pageSize,
          ) + 1}
        </span>

        <button
          type="button"
          onClick={nextPage}
          disabled={
            !hasNext
            || loading
            || moderating
          }
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
          Suivant
        </button>

      </div>

    </div>
  );
}
