"use client";

import type {
  AdminDigestSearchFilters,
  DigestAudience,
  DigestStatus,
} from "@/types/digest";


/* =========================================================
   TYPES
========================================================= */

type Props = {

  filters: AdminDigestSearchFilters;

  onChange: (
    filters: AdminDigestSearchFilters,
  ) => void;

};


/* =========================================================
   COMPONENT
========================================================= */

export default function DigestFilters({

  filters,

  onChange,

}: Props) {

  /* =====================================================
     UPDATE
  ===================================================== */

  function updateFilter(
    patch: Partial<
      AdminDigestSearchFilters
    >,
  ) {

    onChange({

      ...filters,

      ...patch,

      offset: 0,

    });

  }


  /* =====================================================
     RESET
  ===================================================== */

  function resetFilters() {

    onChange({

      query: "",

      audience:
        undefined,

      status:
        undefined,

      period_start:
        undefined,

      period_end:
        undefined,

      limit:
        filters.limit
        ?? 50,

      offset:
        0,

    });

  }


  /* =====================================================
     ACTIVE FILTERS
  ===================================================== */

  const hasActiveFilters = Boolean(

    filters.query

    || filters.audience

    || filters.status

    || filters.period_start

    || filters.period_end

  );


  /* =====================================================
     RENDER
  ===================================================== */

  return (

    <div
      className="
        rounded-lg
        border
        bg-white
        p-4
      "
    >

      <div
        className="
          grid
          grid-cols-1
          gap-4
          md:grid-cols-2
          xl:grid-cols-5
        "
      >

        {/* ================================================= */}
        {/* SEARCH */}
        {/* ================================================= */}

        <div className="xl:col-span-2">

          <label
            htmlFor="digest-search"
            className="
              mb-1
              block
              text-xs
              font-medium
              uppercase
              tracking-wide
              text-gray-500
            "
          >
            Search
          </label>

          <input
            id="digest-search"
            type="search"
            value={
              filters.query
              ?? ""
            }
            onChange={(
              event,
            ) => {

              updateFilter({

                query:
                  event.target.value,

              });

            }}
            placeholder={
              "Name, email or company..."
            }
            className="
              h-10
              w-full
              rounded-md
              border
              border-gray-300
              bg-white
              px-3
              text-sm
              outline-none
              transition
              focus:border-blue-500
              focus:ring-2
              focus:ring-blue-100
            "
          />

        </div>


        {/* ================================================= */}
        {/* AUDIENCE */}
        {/* ================================================= */}

        <div>

          <label
            htmlFor="digest-audience"
            className="
              mb-1
              block
              text-xs
              font-medium
              uppercase
              tracking-wide
              text-gray-500
            "
          >
            Audience
          </label>

          <select
            id="digest-audience"
            value={
              filters.audience
              ?? ""
            }
            onChange={(
              event,
            ) => {

              updateFilter({

                audience:
                  event.target.value

                    ? event.target.value
                      as DigestAudience

                    : undefined,

              });

            }}
            className="
              h-10
              w-full
              rounded-md
              border
              border-gray-300
              bg-white
              px-3
              text-sm
              outline-none
              transition
              focus:border-blue-500
              focus:ring-2
              focus:ring-blue-100
            "
          >

            <option value="">
              All audiences
            </option>

            <option value="user">
              Users
            </option>

            <option value="expert">
              Experts
            </option>

          </select>

        </div>


        {/* ================================================= */}
        {/* STATUS */}
        {/* ================================================= */}

        <div>

          <label
            htmlFor="digest-status"
            className="
              mb-1
              block
              text-xs
              font-medium
              uppercase
              tracking-wide
              text-gray-500
            "
          >
            Status
          </label>

          <select
            id="digest-status"
            value={
              filters.status
              ?? ""
            }
            onChange={(
              event,
            ) => {

              updateFilter({

                status:
                  event.target.value

                    ? event.target.value
                      as DigestStatus

                    : undefined,

              });

            }}
            className="
              h-10
              w-full
              rounded-md
              border
              border-gray-300
              bg-white
              px-3
              text-sm
              outline-none
              transition
              focus:border-blue-500
              focus:ring-2
              focus:ring-blue-100
            "
          >

            <option value="">
              All statuses
            </option>

            <option value="created">
              Created
            </option>

            <option value="generating">
              Generating
            </option>

            <option value="generated">
              Generated
            </option>

            <option value="sending">
              Sending
            </option>

            <option value="sent">
              Sent
            </option>

            <option value="failed">
              Failed
            </option>

          </select>

        </div>


        {/* ================================================= */}
        {/* RESET */}
        {/* ================================================= */}

        <div className="flex items-end">

          <button
            type="button"
            disabled={
              !hasActiveFilters
            }
            onClick={
              resetFilters
            }
            className="
              h-10
              w-full
              rounded-md
              border
              border-gray-300
              bg-white
              px-4
              text-sm
              font-medium
              text-gray-700
              transition
              hover:bg-gray-50
              disabled:cursor-not-allowed
              disabled:opacity-40
            "
          >
            Reset filters
          </button>

        </div>

      </div>


      {/* =================================================== */}
      {/* PERIOD */}
      {/* =================================================== */}

      <div
        className="
          mt-4
          grid
          grid-cols-1
          gap-4
          border-t
          pt-4
          md:grid-cols-2
          xl:max-w-2xl
        "
      >

        <div>

          <label
            htmlFor="digest-period-start"
            className="
              mb-1
              block
              text-xs
              font-medium
              uppercase
              tracking-wide
              text-gray-500
            "
          >
            Period from
          </label>

          <input
            id="digest-period-start"
            type="date"
            value={
              filters.period_start
              ?? ""
            }
            max={
              filters.period_end
              ?? undefined
            }
            onChange={(
              event,
            ) => {

              updateFilter({

                period_start:
                  event.target.value
                  || undefined,

              });

            }}
            className="
              h-10
              w-full
              rounded-md
              border
              border-gray-300
              bg-white
              px-3
              text-sm
              outline-none
              transition
              focus:border-blue-500
              focus:ring-2
              focus:ring-blue-100
            "
          />

        </div>

        <div>

          <label
            htmlFor="digest-period-end"
            className="
              mb-1
              block
              text-xs
              font-medium
              uppercase
              tracking-wide
              text-gray-500
            "
          >
            Period to
          </label>

          <input
            id="digest-period-end"
            type="date"
            value={
              filters.period_end
              ?? ""
            }
            min={
              filters.period_start
              ?? undefined
            }
            onChange={(
              event,
            ) => {

              updateFilter({

                period_end:
                  event.target.value
                  || undefined,

              });

            }}
            className="
              h-10
              w-full
              rounded-md
              border
              border-gray-300
              bg-white
              px-3
              text-sm
              outline-none
              transition
              focus:border-blue-500
              focus:ring-2
              focus:ring-blue-100
            "
          />

        </div>

      </div>

    </div>

  );

}
