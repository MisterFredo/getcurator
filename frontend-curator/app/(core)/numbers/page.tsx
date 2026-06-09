"use client";

import { useState, useEffect } from "react";

import { api } from "@/lib/api";

import NumberCard from "@/components/numbers/NumberCard";
import NumbersHeader from "@/components/numbers/NumbersHeader";

import { useWorkspace } from "@/contexts/WorkspaceContext";

/* ========================================================= */

type NumberItem = {
  ID_NUMBER: string;
  TYPE?: string;
  [key: string]: any;
};

type Universe = {
  id_universe: string;
  label: string;
};

/* ========================================================= */

export default function NumbersPage() {

  const LIMIT = 100;

  /* =========================================================
     WORKSPACE
  ========================================================= */

  const {
    selectedNumberItems,
    toggleNumber,
  } = useWorkspace();

  const selectedIds =
    selectedNumberItems.map(
      (i) => i.ID_NUMBER
    );

  /* =========================================================
     UNIVERSE
  ========================================================= */

  const [universes, setUniverses] =
    useState<Universe[]>([]);

  const [activeUniverse, setActiveUniverse] =
    useState<string | null>(null);

  /* =========================================================
     DATA
  ========================================================= */

  const [items, setItems] =
    useState<NumberItem[]>([]);

  const [loading, setLoading] =
    useState(true);

  const [query, setQuery] =
    useState("");

  /* =========================================================
     LOAD UNIVERS
  ========================================================= */

  useEffect(() => {

    async function loadUniverses() {

      try {

        const res = await api.get(
          "/universe/list-for-user"
        );

        setUniverses(
          res?.universes || []
        );

      } catch (e) {

        console.error(
          "❌ universe load error",
          e
        );
      }
    }

    loadUniverses();

  }, []);

  /* =========================================================
     LOAD
  ========================================================= */

  async function load(q?: string) {

    const finalQuery =
      (q ?? query)?.trim();

    setLoading(true);

    try {

      const res = await api.get(
        `/numbers/feed?limit=${LIMIT}${
          finalQuery
            ? `&query=${encodeURIComponent(
                finalQuery
              )}`
            : ""
        }${
          activeUniverse
            ? `&universe_id=${activeUniverse}`
            : ""
        }`
      );

      const data =
        res?.items ?? [];

      setItems(data);

    } catch (e) {

      console.error(
        "❌ Numbers load error",
        e
      );

      setItems([]);

    } finally {

      setLoading(false);

    }
  }

  /* ========================================================= */

  useEffect(() => {
    load();
  }, [activeUniverse]);

  /* =========================================================
     SELECTION
  ========================================================= */

  function toggleSelect(
    item: NumberItem
  ) {
    toggleNumber(item);
  }

  /* =========================================================
     GROUP BY TYPE
  ========================================================= */

  function groupByType(
    items: NumberItem[]
  ) {

    const map:
      Record<
        string,
        NumberItem[]
      > = {};

    items.forEach((item) => {

      const key =
        item.TYPE ?? "Autres";

      if (!map[key]) {
        map[key] = [];
      }

      map[key].push(item);
    });

    return Object.fromEntries(
      Object.entries(map).sort(
        ([a], [b]) =>
          a.localeCompare(
            b,
            "fr",
            {
              sensitivity:
                "base",
            }
          )
      )
    );
  }

  /* ========================================================= */

  const grouped =
    groupByType(items);

  const hasContent =
    items.length > 0;

  /* =========================================================
     RENDER
  ========================================================= */

  return (

    <div className="
      grid
      grid-cols-1
      gap-8
      items-start
    ">

      <div className="
        space-y-6
      ">

        {/* ===================================================
            TITLE
        =================================================== */}

        <div>

          <h1 className="
            text-2xl
            font-semibold
            tracking-tight
            text-[#111827]
          ">
            Numbers
          </h1>

        </div>

        {/* ===================================================
            UNIVERSE FILTERS
        =================================================== */}

        {universes.length > 0 && (

          <div className="
            flex
            flex-wrap
            gap-2
          ">

            <button
              onClick={() =>
                setActiveUniverse(null)
              }
              className={`
                px-3
                py-1.5
                rounded-full
                text-xs
                font-medium
                transition

                ${
                  !activeUniverse
                    ? `
                      bg-gray-900
                      text-white
                    `
                    : `
                      bg-gray-100
                      text-gray-600
                      hover:bg-gray-200
                    `
                }
              `}
            >
              All
            </button>

            {universes.map((u) => (

              <button
                key={u.id_universe}
                onClick={() =>
                  setActiveUniverse(
                    u.id_universe
                  )
                }
                className={`
                  px-3
                  py-1.5
                  rounded-full
                  text-xs
                  font-medium
                  transition

                  ${
                    activeUniverse ===
                    u.id_universe

                      ? `
                        bg-gray-900
                        text-white
                      `

                      : `
                        bg-gray-100
                        text-gray-600
                        hover:bg-gray-200
                      `
                  }
                `}
              >
                {u.label}
              </button>

            ))}

          </div>

        )}

        {/* ===================================================
            SEARCH
        =================================================== */}

        <NumbersHeader
          query={query}
          setQuery={setQuery}
          onSearch={(q) =>
            load(q)
          }
        />

        {/* ===================================================
            LOADING
        =================================================== */}

        {loading && (
          <p className="
            text-sm
            text-gray-400
          ">
            Chargement des chiffres...
          </p>
        )}

        {/* ===================================================
            EMPTY
        =================================================== */}

        {!loading &&
          !hasContent && (
            <p className="
              text-sm
              text-gray-400
            ">
              Aucun chiffre disponible.
            </p>
          )}

        {/* ===================================================
            CONTENT
        =================================================== */}

        {!loading &&
          hasContent &&
          Object.entries(
            grouped
          ).map(
            ([
              type,
              groupItems,
            ]) => (
              <section
                key={type}
                className="space-y-4"
              >

                <div className="
                  flex
                  items-center
                  justify-between
                ">

                  <h2 className="
                    text-xs
                    font-semibold
                    uppercase
                    tracking-wide
                    text-gray-400
                  ">
                    {type}
                  </h2>

                  <span className="
                    text-xs
                    text-gray-300
                  ">
                    {
                      groupItems.length
                    }
                  </span>

                </div>

                <div
                  className="
                    grid
                    grid-cols-2
                    sm:grid-cols-3
                    md:grid-cols-4
                    lg:grid-cols-5
                    gap-3
                  "
                >

                  {groupItems.map(
                    (item) => {

                      const selected =
                        selectedIds.includes(
                          item.ID_NUMBER
                        );

                      return (

                        <NumberCard
                          key={
                            item.ID_NUMBER
                          }

                          item={item}

                          selected={
                            selected
                          }

                          onClick={() =>
                            toggleSelect(
                              item
                            )
                          }
                        />

                      );
                    }
                  )}

                </div>

              </section>
            )
          )}

      </div>

    </div>
  );
}
