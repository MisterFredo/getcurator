"use client";

import {
  useEffect,
  useState,
} from "react";

import NumbersExplorerRow from "@/components/numbers/explorer/NumbersExplorerRow";

import type {
  PublicNumber,
} from "@/types/numbers";


/* ============================================================
   PROPS
============================================================ */

type Props = {

  items: PublicNumber[];

  loading?: boolean;

  onOpenContent?: (
    contentId: string,
  ) => void;

};


/* ============================================================
   COMPONENT
============================================================ */

export default function NumbersExplorerTable({

  items,

  loading = false,

  onOpenContent,

}: Props) {

  const [
    expandedId,
    setExpandedId,
  ] = useState<string | null>(
    null,
  );


  /* ========================================================
     RESET EXPANDED ROW
  ======================================================== */

  useEffect(() => {

    setExpandedId(
      null,
    );

  }, [
    items,
  ]);


  /* ========================================================
     TOGGLE ROW
  ======================================================== */

  function toggleRow(
    idNumber: string,
  ) {

    setExpandedId(
      current =>
        current === idNumber
          ? null
          : idNumber,
    );

  }


  /* ========================================================
     RENDER
  ======================================================== */

  return (

    <section
      className="
        overflow-hidden
        rounded-xl
        border
        border-gray-200
        bg-white
      "
    >

      <div className="overflow-x-auto">

        {/* ================================================= */}
        {/* HEADER */}
        {/* ================================================= */}

        <div
          className="
            grid
            min-w-[950px]
            grid-cols-[180px_minmax(240px,1.8fr)_minmax(180px,1.2fr)_150px_140px_32px]
            items-center
            gap-4
            border-b
            border-gray-200
            bg-gray-50
            px-4
            py-2.5
            text-[10px]
            font-semibold
            uppercase
            tracking-wide
            text-gray-400
          "
        >

          <div>
            Value
          </div>

          <div>
            Indicator
          </div>

          <div>
            Entity
          </div>

          <div>
            Geography
          </div>

          <div>
            Period
          </div>

          <div />

        </div>


        {/* ================================================= */}
        {/* LOADING */}
        {/* ================================================= */}

        {loading && (

          <div>

            {Array.from({
              length: 8,
            }).map(
              (_, index) => (

                <div
                  key={index}
                  className="
                    grid
                    min-w-[950px]
                    grid-cols-[180px_minmax(240px,1.8fr)_minmax(180px,1.2fr)_150px_140px_32px]
                    items-center
                    gap-4
                    border-b
                    border-gray-100
                    px-4
                    py-3
                    last:border-b-0
                  "
                >

                  {/* VALUE */}

                  <div
                    className="
                      h-4
                      w-24
                      animate-pulse
                      rounded
                      bg-gray-100
                    "
                  />


                  {/* INDICATOR */}

                  <div className="space-y-1.5">

                    <div
                      className="
                        h-3.5
                        w-48
                        animate-pulse
                        rounded
                        bg-gray-100
                      "
                    />

                    <div
                      className="
                        h-2.5
                        w-20
                        animate-pulse
                        rounded
                        bg-gray-100
                      "
                    />

                  </div>


                  {/* ENTITY */}

                  <div
                    className="
                      h-5
                      w-24
                      animate-pulse
                      rounded-full
                      bg-gray-100
                    "
                  />


                  {/* GEOGRAPHY */}

                  <div
                    className="
                      h-3
                      w-20
                      animate-pulse
                      rounded
                      bg-gray-100
                    "
                  />


                  {/* PERIOD */}

                  <div
                    className="
                      h-3
                      w-16
                      animate-pulse
                      rounded
                      bg-gray-100
                    "
                  />


                  {/* EXPAND */}

                  <div
                    className="
                      h-4
                      w-4
                      animate-pulse
                      rounded
                      bg-gray-100
                    "
                  />

                </div>

              ),
            )}

          </div>

        )}


        {/* ================================================= */}
        {/* EMPTY */}
        {/* ================================================= */}

        {!loading
          && items.length === 0
          && (

            <div
              className="
                px-6
                py-12
                text-center
              "
            >

              <div
                className="
                  text-sm
                  font-medium
                  text-gray-700
                "
              >
                No validated Number found.
              </div>

              <div
                className="
                  mt-1
                  text-xs
                  text-gray-400
                "
              >
                Try changing your search or filters.
              </div>

            </div>

          )}


        {/* ================================================= */}
        {/* ROWS */}
        {/* ================================================= */}

        {!loading
          && items.length > 0
          && (

            <div>

              {items.map(
                item => (

                  <NumbersExplorerRow
                    key={item.id_number}
                    item={item}
                    expanded={
                      expandedId
                      === item.id_number
                    }
                    onToggle={() =>
                      toggleRow(
                        item.id_number,
                      )
                    }
                    onOpenContent={
                      onOpenContent
                    }
                  />

                ),
              )}

            </div>

          )}

      </div>

    </section>

  );

}
