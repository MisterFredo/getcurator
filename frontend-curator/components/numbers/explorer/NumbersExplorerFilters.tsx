"use client";

import {
  FormEvent,
  useEffect,
  useState,
} from "react";

import type {
  PublicNumberFilters,
} from "@/types/numbers";


/* ============================================================
   TYPES
============================================================ */

export type NumbersExplorerFilterState = {

  universeId: string;

  metricType: string;

  year: string;

  zone: string;

  valueStatus: string;

};


type Universe = {

  id_universe: string;

  label: string;

};


type Props = {

  query: string;

  value:
    NumbersExplorerFilterState;

  universes:
    Universe[];

  filters:
    PublicNumberFilters | null;

  loading?: boolean;

  onSearch: (
    query: string,
  ) => void;

  onChange: (
    value: NumbersExplorerFilterState,
  ) => void;

  onReset: () => void;

};


/* ============================================================
   COMPONENT
============================================================ */

export default function NumbersExplorerFilters({

  query,

  value,

  universes,

  filters,

  loading = false,

  onSearch,

  onChange,

  onReset,

}: Props) {

  const [
    searchInput,
    setSearchInput,
  ] = useState(
    query,
  );


  /* ========================================================
     SYNCHRONIZE QUERY
  ======================================================== */

  useEffect(() => {

    setSearchInput(
      query,
    );

  }, [
    query,
  ]);


  /* ========================================================
     UPDATE FILTER
  ======================================================== */

  function updateFilter<
    Key extends keyof NumbersExplorerFilterState
  >(
    key: Key,
    nextValue: NumbersExplorerFilterState[Key],
  ) {

    onChange({
      ...value,
      [key]: nextValue,
    });

  }


  /* ========================================================
     SEARCH
  ======================================================== */

  function handleSubmit(
    event: FormEvent<HTMLFormElement>,
  ) {

    event.preventDefault();

    if (loading) {
      return;
    }

    onSearch(
      searchInput.trim(),
    );

  }


  /* ========================================================
     RESET
  ======================================================== */

  function handleReset() {

    setSearchInput("");

    onReset();

  }


  /* ========================================================
     ACTIVE FILTERS
  ======================================================== */

  const hasActiveFilters = Boolean(

    query

    || value.universeId

    || value.metricType

    || value.year

    || value.zone

    || value.valueStatus

  );


  /* ========================================================
     RENDER
  ======================================================== */

  return (

    <section
      className="
        rounded-xl
        border
        border-gray-200
        bg-white
        p-4
      "
    >

      {/* ================================================= */}
      {/* SEARCH */}
      {/* ================================================= */}

      <form
        onSubmit={handleSubmit}
        className="
          flex
          items-center
          gap-2
        "
      >

        <input
          type="search"
          value={searchInput}
          disabled={loading}
          onChange={event =>
            setSearchInput(
              event.target.value,
            )
          }
          placeholder="Search a metric, company, topic or source..."
          className="
            min-w-0
            flex-1
            rounded-lg
            border
            border-gray-200
            px-3
            py-2.5
            text-sm
            text-gray-900
            outline-none
            transition
            placeholder:text-gray-400
            focus:border-gray-400
            focus:ring-2
            focus:ring-gray-100
            disabled:bg-gray-50
          "
        />

        <button
          type="submit"
          disabled={loading}
          className="
            rounded-lg
            bg-gray-900
            px-4
            py-2.5
            text-sm
            font-medium
            text-white
            transition
            hover:bg-gray-800
            disabled:cursor-not-allowed
            disabled:opacity-50
          "
        >
          Search
        </button>

      </form>


      {/* ================================================= */}
      {/* FILTERS */}
      {/* ================================================= */}

      <div
        className="
          mt-4
          grid
          grid-cols-1
          gap-3
          sm:grid-cols-2
          lg:grid-cols-5
        "
      >

        {/* UNIVERSE */}

        <label className="space-y-1">

          <span
            className="
              text-[10px]
              font-semibold
              uppercase
              tracking-wide
              text-gray-400
            "
          >
            Universe
          </span>

          <select
            value={value.universeId}
            disabled={loading}
            onChange={event =>
              updateFilter(
                "universeId",
                event.target.value,
              )
            }
            className="
              w-full
              rounded-lg
              border
              border-gray-200
              bg-white
              px-3
              py-2
              text-xs
              text-gray-700
              outline-none
              focus:border-gray-400
              disabled:bg-gray-50
            "
          >

            <option value="">
              All universes
            </option>

            {universes.map(
              universe => (

                <option
                  key={universe.id_universe}
                  value={universe.id_universe}
                >
                  {universe.label}
                </option>

              ),
            )}

          </select>

        </label>


        {/* METRIC TYPE */}

        <label className="space-y-1">

          <span
            className="
              text-[10px]
              font-semibold
              uppercase
              tracking-wide
              text-gray-400
            "
          >
            Metric
          </span>

          <select
            value={value.metricType}
            disabled={loading}
            onChange={event =>
              updateFilter(
                "metricType",
                event.target.value,
              )
            }
            className="
              w-full
              rounded-lg
              border
              border-gray-200
              bg-white
              px-3
              py-2
              text-xs
              text-gray-700
              outline-none
              focus:border-gray-400
              disabled:bg-gray-50
            "
          >

            <option value="">
              All metrics
            </option>

            {(filters?.metric_types ?? []).map(
              option => (

                <option
                  key={option.value}
                  value={option.value}
                >
                  {option.label} ({option.count})
                </option>

              ),
            )}

          </select>

        </label>


        {/* YEAR */}

        <label className="space-y-1">

          <span
            className="
              text-[10px]
              font-semibold
              uppercase
              tracking-wide
              text-gray-400
            "
          >
            Year
          </span>

          <select
            value={value.year}
            disabled={loading}
            onChange={event =>
              updateFilter(
                "year",
                event.target.value,
              )
            }
            className="
              w-full
              rounded-lg
              border
              border-gray-200
              bg-white
              px-3
              py-2
              text-xs
              text-gray-700
              outline-none
              focus:border-gray-400
              disabled:bg-gray-50
            "
          >

            <option value="">
              All years
            </option>

            {(filters?.years ?? []).map(
              option => (

                <option
                  key={option.value}
                  value={option.value}
                >
                  {option.value} ({option.count})
                </option>

              ),
            )}

          </select>

        </label>


        {/* ZONE */}

        <label className="space-y-1">

          <span
            className="
              text-[10px]
              font-semibold
              uppercase
              tracking-wide
              text-gray-400
            "
          >
            Geography
          </span>

          <select
            value={value.zone}
            disabled={loading}
            onChange={event =>
              updateFilter(
                "zone",
                event.target.value,
              )
            }
            className="
              w-full
              rounded-lg
              border
              border-gray-200
              bg-white
              px-3
              py-2
              text-xs
              text-gray-700
              outline-none
              focus:border-gray-400
              disabled:bg-gray-50
            "
          >

            <option value="">
              All geographies
            </option>

            {(filters?.zones ?? []).map(
              option => (

                <option
                  key={option.value}
                  value={option.value}
                >
                  {option.label} ({option.count})
                </option>

              ),
            )}

          </select>

        </label>


        {/* VALUE STATUS */}

        <label className="space-y-1">

          <span
            className="
              text-[10px]
              font-semibold
              uppercase
              tracking-wide
              text-gray-400
            "
          >
            Status
          </span>

          <select
            value={value.valueStatus}
            disabled={loading}
            onChange={event =>
              updateFilter(
                "valueStatus",
                event.target.value,
              )
            }
            className="
              w-full
              rounded-lg
              border
              border-gray-200
              bg-white
              px-3
              py-2
              text-xs
              text-gray-700
              outline-none
              focus:border-gray-400
              disabled:bg-gray-50
            "
          >

            <option value="">
              All statuses
            </option>

            {(filters?.value_statuses ?? []).map(
              option => (

                <option
                  key={option.value}
                  value={option.value}
                >
                  {option.label} ({option.count})
                </option>

              ),
            )}

          </select>

        </label>

      </div>


      {/* ================================================= */}
      {/* RESET */}
      {/* ================================================= */}

      {hasActiveFilters && (

        <div
          className="
            mt-3
            flex
            justify-end
          "
        >

          <button
            type="button"
            disabled={loading}
            onClick={handleReset}
            className="
              text-xs
              font-medium
              text-gray-400
              transition
              hover:text-gray-700
              disabled:opacity-50
            "
          >
            Reset filters
          </button>

        </div>

      )}

    </section>

  );

}
