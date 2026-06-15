"use client";

import { useState, useEffect } from "react";

/* ========================================================= */

type Universe = {
  id: string;
  label: string;
  count?: number;
};

type Props = {

  query: string;

  setQuery: (
    q: string
  ) => void;

  onSearch: (
    q: string
  ) => void;

  universes: Universe[];

  selectedUniverse:
    string | null;

  onSelectUniverse: (
    id: string | null
  ) => void;

  selectedType: string;

  onSelectType: (
    type: string
  ) => void;

  // 🔥 NEW
  feedMode:
    "all" | "mine" | "keywords";

  onSelectFeedMode: (
    mode:
      | "all"
      | "mine"
      | "keywords"
  ) => void;

  loading?: boolean;
};

/* ========================================================= */

function PillButton({
  active,
  disabled,
  children,
  onClick,
}: any) {

  return (

    <button
      onClick={onClick}
      disabled={disabled}
      className={`
        whitespace-nowrap
        px-3
        py-1.5
        rounded-full
        text-xs
        border
        transition-all

        ${
          active
            ? `
              bg-black
              text-white
              border-black
              shadow-sm
            `
            : `
              bg-white
              text-gray-600
              border-gray-200
              hover:bg-gray-50
            `
        }

        ${
          disabled
            ? `
              opacity-50
              cursor-not-allowed
            `
            : ""
        }
      `}
    >
      {children}
    </button>

  );
}

/* ========================================================= */

function Separator() {

  return (

    <div className="
      h-5
      w-px
      bg-gray-200
      shrink-0
    " />

  );
}

/* ========================================================= */

export default function FeedHeader({

  query,
  setQuery,
  onSearch,

  universes,
  selectedUniverse,
  onSelectUniverse,

  selectedType,
  onSelectType,

  // 🔥 NEW
  feedMode,
  onSelectFeedMode,

  loading = false,

}: Props) {

  const [input, setInput] =
    useState(query);

  useEffect(() => {
    setInput(query);
  }, [query]);

  /* =========================================================
     SEARCH
  ========================================================= */

  function triggerSearch() {

    if (loading) return;

    const value =
      input.trim();

    setQuery(value);

    onSearch(value);
  }

  /* =========================================================
     RENDER
  ========================================================= */

  return (

    <div className="
      sticky
      top-0
      z-20
      bg-white/90
      backdrop-blur
      border-b
      border-gray-100
      py-4
      space-y-4
    ">

      {/* =====================================================
          FILTER BAR
      ===================================================== */}

      <div className="
        flex
        items-center
        gap-3
        overflow-x-auto
        scrollbar-none
        px-1
      ">

        {/* =================================================
            FEED MODE
        ================================================= */}

        <div className="
          flex
          items-center
          gap-2
          shrink-0
        ">

          <PillButton
            active={
              feedMode === "all"
            }
            disabled={loading}
            onClick={() =>
              !loading &&
              onSelectFeedMode("all")
            }
          >
            All Feed
          </PillButton>

          <PillButton
            active={
              feedMode === "mine"
            }
            disabled={loading}
            onClick={() =>
              !loading &&
              onSelectFeedMode("mine")
            }
          >
            Favorites
          </PillButton>

          <PillButton
            active={
              feedMode === "keywords"
            }
            disabled={loading}
            onClick={() =>
              !loading &&
              onSelectFeedMode("keywords")
            }
          >
            Keywords
          </PillButton>

        </div>

        <Separator />

        {/* =================================================
            TYPE
        ================================================= */}

        <div className="
          flex
          items-center
          gap-2
          shrink-0
        ">

          {[
            {
              value: "all",
              label: "All",
            },
            {
              value: "news",
              label: "News",
            },
            {
              value: "analysis",
              label: "Analysis",
            },
          ].map((t) => {

            const active =
              selectedType === t.value;

            return (

              <PillButton
                key={t.value}
                active={active}
                disabled={loading}
                onClick={() =>
                  !loading &&
                  onSelectType(t.value)
                }
              >
                {t.label}
              </PillButton>

            );
          })}

        </div>

        <Separator />

        {/* =================================================
            UNIVERS
        ================================================= */}

        <div className="
          flex
          items-center
          gap-2
          shrink-0
        ">

          <PillButton
            active={
              selectedUniverse === null
            }
            disabled={loading}
            onClick={() =>
              !loading &&
              onSelectUniverse(null)
            }
          >
            All
          </PillButton>

          {universes.map((u) => {

            const active =
              selectedUniverse === u.id;

            return (

              <PillButton
                key={u.id}
                active={active}
                disabled={loading}
                onClick={() =>
                  !loading &&
                  onSelectUniverse(u.id)
                }
              >

                <div className="
                  flex
                  items-center
                  gap-1
                ">

                  <span>
                    {u.label}
                  </span>

                  {u.count !== undefined && (

                    <span
                      className={`
                        text-[9px]
                        px-1
                        py-0.5
                        rounded-full

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
                      {u.count}
                    </span>

                  )}

                </div>

              </PillButton>

            );
          })}

        </div>

      </div>

      {/* =====================================================
          SEARCH
      ===================================================== */}

      <div className="
        flex
        items-center
        gap-3
        px-1
      ">

        <input
          value={input}
          disabled={loading}
          onChange={(e) =>
            setInput(e.target.value)
          }
          onKeyDown={(e) => {

            if (e.key === "Enter") {
              triggerSearch();
            }
          }}
          placeholder="
            Search
            (Amazon, CTV,
            Retail media…)
          "
          className="
            flex-1
            border
            border-gray-200
            rounded-lg
            px-4
            py-2
            text-sm
            bg-white
            focus:outline-none
            focus:ring-2
            focus:ring-black
            disabled:opacity-50
          "
        />

        <button
          onClick={triggerSearch}
          disabled={loading}
          className="
            px-4
            py-2
            rounded-lg
            bg-black
            text-white
            text-sm
            hover:opacity-90
            transition
            disabled:opacity-50
            disabled:cursor-not-allowed
            whitespace-nowrap
          "
        >
          {loading
            ? "..."
            : "Search"}
        </button>

      </div>

    </div>
  );
}
