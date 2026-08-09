// frontend-curator/components/watch/WatchHeader.tsx

"use client";

import { useEffect, useState } from "react";

/* ========================================================= */

type Universe = {

  id: string;

  label: string;

  count?: number;

};

/* ========================================================= */

type Props = {

  query: string;

  onSearch: (
    query: string,
  ) => void;

  universes: Universe[];

  selectedUniverse: string | null;

  onSelectUniverse: (
    id: string | null,
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

export default function WatchHeader({

  query,

  onSearch,

  universes,

  selectedUniverse,

  onSelectUniverse,

  loading = false,

}: Props) {

  const [

    input,

    setInput,

  ] = useState(query);

  useEffect(() => {

    setInput(query);

  }, [

    query,

  ]);

  /* ===================================================== */

  function triggerSearch() {

    if (loading) {

      return;

    }

    onSearch(

      input.trim(),

    );

  }

  /* ===================================================== */

  return (

    <div
      className="
        sticky
        top-0
        z-20
        bg-white/90
        backdrop-blur
        border-b
        border-gray-100
        py-4
        space-y-4
      "
    >

      {/* ================================================
          SEARCH
      ================================================ */}

      <div
        className="
          flex
          items-center
          gap-3
          px-1
        "
      >

        <input

          value={input}

          disabled={loading}

          onChange={(e) =>

            setInput(

              e.target.value,

            )

          }

          onKeyDown={(e) => {

            if (

              e.key === "Enter"

            ) {

              triggerSearch();

            }

          }}

          placeholder="
            Search
            (Amazon,
            Retail Media,
            CTV...)
          "

          className="
            flex-1
            rounded-lg
            border
            border-gray-200
            bg-white
            px-4
            py-2
            text-sm
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
            rounded-lg
            bg-black
            px-4
            py-2
            text-sm
            text-white
            transition
            hover:opacity-90
            disabled:opacity-50
            disabled:cursor-not-allowed
          "
        >

          {loading

            ? "..."

            : "Search"}

        </button>

      </div>

      {/* ================================================
          UNIVERSES
      ================================================ */}

      <div
        className="
          flex
          items-center
          gap-2
          overflow-x-auto
          scrollbar-none
          px-1
        "
      >

        <PillButton

          active={
            selectedUniverse === null
          }

          disabled={loading}

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

                key={universe.id}

                active={active}

                disabled={loading}

                onClick={() =>

                  onSelectUniverse(
                    universe.id,
                  )

                }

              >

                <div
                  className="
                    flex
                    items-center
                    gap-1
                  "
                >

                  <span>

                    {universe.label}

                  </span>

                  {universe.count !==
                    undefined && (

                    <span
                      className={`
                        rounded-full
                        px-1
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

                  )}

                </div>

              </PillButton>

            );

          }

        )}

      </div>

    </div>

  );

}
