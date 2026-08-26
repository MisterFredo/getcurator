"use client";

import {
  useEffect,
  useState,
} from "react";

import type {
  ReactNode,
} from "react";

import type {
  WatchFilterOption,
} from "@/types/watch";

/* =========================================================
   TYPES
========================================================= */

type WatchPeriod =
  | "7d"
  | "30d"
  | "3m"
  | "12m"
  | "all";


type Props = {

  query: string;

  onSearch: (
    query: string,
  ) => void;

  period: WatchPeriod;

  onSelectPeriod: (
    period: WatchPeriod,
  ) => void;

  universes: WatchFilterOption[];

  companies: WatchFilterOption[];

  solutions: WatchFilterOption[];

  topics: WatchFilterOption[];

  selectedUniverse: string | null;

  selectedCompany: string | null;

  selectedSolution: string | null;

  selectedTopic: string | null;

  selectedUniverseOption:
    WatchFilterOption | null;

  selectedCompanyOption:
    WatchFilterOption | null;

  selectedSolutionOption:
    WatchFilterOption | null;

  selectedTopicOption:
    WatchFilterOption | null;

  onSelectUniverse: (
    id: string | null,
  ) => void;

  onSelectCompany: (
    id: string | null,
  ) => void;

  onSelectSolution: (
    id: string | null,
  ) => void;

  onSelectTopic: (
    id: string | null,
  ) => void;

  onClearFilters: () => void;

  loading?: boolean;

  filtersLoading?: boolean;

};


type PillButtonProps = {

  active: boolean;

  disabled?: boolean;

  children: ReactNode;

  onClick: () => void;

};


type FilterSelectProps = {

  label: string;

  value: string | null;

  options: WatchFilterOption[];

  disabled?: boolean;

  onChange: (
    id: string | null,
  ) => void;

};


type ActiveChipProps = {

  label: string;

  onRemove: () => void;

};

/* =========================================================
   PERIODS
========================================================= */

const PERIODS: Array<{

  id: WatchPeriod;

  label: string;

}> = [

  {
    id: "7d",
    label: "7 days",
  },

  {
    id: "30d",
    label: "30 days",
  },

  {
    id: "3m",
    label: "3 months",
  },

  {
    id: "12m",
    label: "12 months",
  },

  {
    id: "all",
    label: "All time",
  },

];

/* =========================================================
   PILL BUTTON
========================================================= */

function PillButton({

  active,

  disabled = false,

  children,

  onClick,

}: PillButtonProps) {

  return (

    <button

      type="button"

      onClick={
        onClick
      }

      disabled={
        disabled
      }

      className={`
        whitespace-nowrap
        rounded-full
        border
        px-3
        py-1.5
        text-xs
        transition-all

        ${

          active

            ? `
              border-gray-900
              bg-gray-900
              text-white
            `

            : `
              border-gray-200
              bg-white
              text-gray-600
              hover:border-gray-300
              hover:bg-gray-50
              hover:text-gray-900
            `

        }

        ${

          disabled

            ? `
              cursor-not-allowed
              opacity-50
            `

            : ""

        }
      `}
    >

      {children}

    </button>

  );

}

/* =========================================================
   FILTER SELECT
========================================================= */

function FilterSelect({

  label,

  value,

  options,

  disabled = false,

  onChange,

}: FilterSelectProps) {

  return (

    <div
      className="
        relative
        min-w-[160px]
        flex-1
      "
    >

      <select

        value={
          value ?? ""
        }

        disabled={
          disabled
        }

        onChange={event =>

          onChange(
            event.target.value
              || null,
          )

        }

        className={`
          h-9
          w-full
          appearance-none
          rounded-lg
          border
          bg-white
          pl-3
          pr-9
          text-xs
          outline-none
          transition

          ${

            value

              ? `
                border-gray-400
                text-gray-900
              `

              : `
                border-gray-200
                text-gray-600
              `

          }

          hover:border-gray-300

          focus:border-gray-400
          focus:ring-2
          focus:ring-gray-100

          disabled:
          cursor-not-allowed

          disabled:
          opacity-50
        `}
      >

        <option value="">

          {label}

        </option>

        {options.map(
          option => (

            <option

              key={
                option.id
              }

              value={
                option.id
              }

            >

              {option.label}
              {" "}
              ({option.count})

            </option>

          ),
        )}

      </select>

      <span
        className="
          pointer-events-none
          absolute
          right-3
          top-1/2
          -translate-y-1/2
          text-[10px]
          text-gray-400
        "
      >
        ▼
      </span>

    </div>

  );

}

/* =========================================================
   ACTIVE CHIP
========================================================= */

function ActiveChip({

  label,

  onRemove,

}: ActiveChipProps) {

  return (

    <div
      className="
        inline-flex
        items-center
        gap-1.5
        rounded-full
        bg-gray-100
        px-3
        py-1.5
        text-xs
        text-gray-700
      "
    >

      <span>

        {label}

      </span>

      <button

        type="button"

        onClick={
          onRemove
        }

        aria-label={
          `Remove ${label}`
        }

        className="
          text-gray-400
          transition
          hover:text-gray-900
        "
      >
        ×
      </button>

    </div>

  );

}

/* =========================================================
   COMPONENT
========================================================= */

export default function WatchHeader({

  query,

  onSearch,

  period,

  onSelectPeriod,

  universes,

  companies,

  solutions,

  topics,

  selectedUniverse,

  selectedCompany,

  selectedSolution,

  selectedTopic,

  selectedUniverseOption,

  selectedCompanyOption,

  selectedSolutionOption,

  selectedTopicOption,

  onSelectUniverse,

  onSelectCompany,

  onSelectSolution,

  onSelectTopic,

  onClearFilters,

  loading = false,

  filtersLoading = false,

}: Props) {

  const [
    input,
    setInput,
  ] = useState(
    query,
  );

  useEffect(() => {

    setInput(
      query,
    );

  }, [
    query,
  ]);

  /* =======================================================
     SEARCH
  ======================================================= */

  function triggerSearch() {

    if (loading) {

      return;

    }

    onSearch(
      input.trim(),
    );

  }

  /* =======================================================
     ACTIVE FILTERS
  ======================================================= */

  const hasActiveFilters = Boolean(

    query

    || period !== "30d"

    || selectedUniverse

    || selectedCompany

    || selectedSolution

    || selectedTopic

  );

  /* =======================================================
     RENDER
  ======================================================= */

  return (

    <div
      className="
        sticky
        top-0
        z-20
        space-y-4
        border-b
        border-gray-100
        bg-white/95
        py-4
        backdrop-blur
      "
    >

      {/* ===================================================
          SEARCH
      =================================================== */}

      <div
        className="
          flex
          items-center
          gap-3
          px-1
        "
      >

        <div
          className="
            relative
            flex-1
          "
        >

          <span
            className="
              pointer-events-none
              absolute
              left-4
              top-1/2
              -translate-y-1/2
              text-sm
              text-gray-400
            "
          >
            ⌕
          </span>

          <input

            value={
              input
            }

            onChange={event =>

              setInput(
                event.target.value,
              )

            }

            onKeyDown={event => {

              if (
                event.key ===
                "Enter"
              ) {

                triggerSearch();

              }

            }}

            placeholder={
              "Search companies, topics, solutions or signals..."
            }

            className="
              h-11
              w-full
              rounded-xl
              border
              border-gray-200
              bg-white
              pl-10
              pr-4
              text-sm
              outline-none
              transition
              placeholder:text-gray-400
              hover:border-gray-300
              focus:border-gray-400
              focus:ring-2
              focus:ring-gray-100
            "
          />

        </div>

        <button

          type="button"

          onClick={
            triggerSearch
          }

          disabled={
            loading
          }

          className="
            h-11
            rounded-xl
            bg-gray-900
            px-5
            text-sm
            font-medium
            text-white
            transition
            hover:bg-black
            disabled:cursor-not-allowed
            disabled:opacity-50
          "
        >

          {loading
            ? "Loading..."
            : "Search"}

        </button>

      </div>

      {/* ===================================================
          PERIOD + UNIVERSES
      =================================================== */}
      
      <div
        className="
          flex
          items-center
          gap-4
          overflow-x-auto
          px-1
          scrollbar-none
        "
      >
      
        {/* PERIOD */}
      
        <div
          className="
            flex
            shrink-0
            items-center
            gap-2
          "
        >
      
          <span
            className="
              mr-1
              whitespace-nowrap
              text-[11px]
              font-medium
              uppercase
              tracking-wide
              text-gray-400
            "
          >
            Period
          </span>
      
          {PERIODS.map(
            option => (
      
              <PillButton
      
                key={
                  option.id
                }
      
                active={
                  period === option.id
                }
      
                onClick={() =>
      
                  onSelectPeriod(
                    option.id,
                  )
      
                }
      
              >
      
                {option.label}
      
              </PillButton>
      
            ),
          )}
      
        </div>
      
        {/* SEPARATOR */}
      
        <div
          className="
            h-5
            w-px
            shrink-0
            bg-gray-200
          "
        />
      
        {/* UNIVERSES */}
      
        <div
          className="
            flex
            shrink-0
            items-center
            gap-2
          "
        >
      
          <span
            className="
              mr-1
              whitespace-nowrap
              text-[11px]
              font-medium
              uppercase
              tracking-wide
              text-gray-400
            "
          >
            Universe
          </span>
      
          <PillButton
      
            active={
              selectedUniverse === null
            }
      
            disabled={
              filtersLoading
            }
      
            onClick={() =>
      
              onSelectUniverse(
                null,
              )
      
            }
      
          >
            All
          </PillButton>
      
          {universes.map(
            universe => {
      
              const active =
                selectedUniverse ===
                universe.id;
      
              return (
      
                <PillButton
      
                  key={
                    universe.id
                  }
      
                  active={
                    active
                  }
      
                  disabled={
                    filtersLoading
                  }
      
                  onClick={() =>
      
                    onSelectUniverse(
                      universe.id,
                    )
      
                  }
      
                >
      
                  <span
                    className="
                      inline-flex
                      items-center
                      gap-1.5
                    "
                  >
      
                    <span>
      
                      {universe.label}
      
                    </span>
      
                    <span
                      className={`
                        rounded-full
                        px-1.5
                        py-0.5
                        text-[9px]
      
                        ${
      
                          active
      
                            ? `
                              bg-white/20
                              text-white
                            `
      
                            : `
                              bg-gray-100
                              text-gray-500
                            `
      
                        }
                      `}
                    >
      
                      {universe.count}
      
                    </span>
      
                  </span>
      
                </PillButton>
      
              );
      
            },
          )}
      
        </div>
      
      </div>

      {/* ===================================================
          ENTITY FILTERS
      =================================================== */}

      <div
        className="
          flex
          flex-col
          gap-2
          px-1
          sm:flex-row
          sm:items-center
        "
      >

        <FilterSelect

          label="All companies"

          value={
            selectedCompany
          }

          options={
            companies
          }

          disabled={
            filtersLoading
          }

          onChange={
            onSelectCompany
          }

        />

        <FilterSelect

          label="All topics"

          value={
            selectedTopic
          }

          options={
            topics
          }

          disabled={
            filtersLoading
          }

          onChange={
            onSelectTopic
          }

        />

        <FilterSelect

          label="All solutions"

          value={
            selectedSolution
          }

          options={
            solutions
          }

          disabled={
            filtersLoading
          }

          onChange={
            onSelectSolution
          }

        />

        {hasActiveFilters && (

          <button

            type="button"

            onClick={
              onClearFilters
            }

            className="
              h-9
              shrink-0
              px-3
              text-xs
              font-medium
              text-gray-500
              transition
              hover:text-gray-900
            "
          >
            Clear all
          </button>

        )}

      </div>

      {/* ===================================================
          ACTIVE FILTERS
      =================================================== */}

      {(

        selectedUniverseOption

        || selectedCompanyOption

        || selectedSolutionOption

        || selectedTopicOption

      ) && (

        <div
          className="
            flex
            flex-wrap
            items-center
            gap-2
            px-1
          "
        >

          <span
            className="
              mr-1
              text-[11px]
              text-gray-400
            "
          >
            Active filters
          </span>

          {selectedUniverseOption && (

            <ActiveChip

              label={
                selectedUniverseOption.label
              }

              onRemove={() =>

                onSelectUniverse(
                  null,
                )

              }

            />

          )}

          {selectedCompanyOption && (

            <ActiveChip

              label={
                selectedCompanyOption.label
              }

              onRemove={() =>

                onSelectCompany(
                  null,
                )

              }

            />

          )}

          {selectedTopicOption && (

            <ActiveChip

              label={
                selectedTopicOption.label
              }

              onRemove={() =>

                onSelectTopic(
                  null,
                )

              }

            />

          )}

          {selectedSolutionOption && (

            <ActiveChip

              label={
                selectedSolutionOption.label
              }

              onRemove={() =>

                onSelectSolution(
                  null,
                )

              }

            />

          )}

        </div>

      )}

    </div>

  );

}
