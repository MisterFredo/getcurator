"use client";

import { useState, useEffect } from "react";

import {
  searchCurator,
  getLatestCurator,
} from "@/lib/search";

import type {
  FeedItem,
  FeedBadge,
} from "@/types/feed";

import { api } from "@/lib/api";

import { useWorkspace } from "@/contexts/WorkspaceContext";

import NewsList from "@/components/news/NewsList";

/* ========================================================= */

type Universe = {
  id_universe: string;
  label: string;
};

/* ========================================================= */

export default function NewsPage() {

  const LIMIT = 20;

  /* =========================================================
     WORKSPACE
  ========================================================= */

  const {
    selectedContentItems,
    toggleContent,
  } = useWorkspace();

  const selectedIds =
    selectedContentItems.map(
      (i) => i.id
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
    useState<FeedItem[]>([]);

  const [loading, setLoading] =
    useState(false);

  const [total, setTotal] =
    useState(0);

  const [query, setQuery] =
    useState("");

  const [offset, setOffset] =
    useState(0);

  const [hasMore, setHasMore] =
    useState(true);

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
     LOAD NEWS
  ========================================================= */

  async function load(
    reset = false,
    q?: string
  ) {

    if (loading && !reset) return;

    const finalQuery =
      q !== undefined
        ? q.trim()
        : query.trim();

    const currentOffset =
      reset
        ? 0
        : offset;

    if (reset) {

      setItems([]);
      setOffset(0);
      setHasMore(true);

    }

    setLoading(true);

    try {

      const res = finalQuery

        ? await searchCurator({

            query: finalQuery,

            limit: LIMIT,

            offset: currentOffset,

            universe_id:
              activeUniverse || undefined,

            content_type: "NEWS",
          })

        : await getLatestCurator({

            limit: LIMIT,

            offset: currentOffset,

            universe_id:
              activeUniverse || undefined,

            content_type: "NEWS",
          });

      if (reset) {

        setItems(res.items);

        setOffset(
          res.items.length
        );

      } else {

        setItems((prev) => [
          ...prev,
          ...res.items,
        ]);

        setOffset(
          (prev) =>
            prev + res.items.length
        );
      }

      setTotal(
        res.count ?? 0
      );

      setHasMore(
        res.items.length === LIMIT
      );

    } catch (e) {

      console.error(
        "❌ news load error",
        e
      );

    } finally {

      setLoading(false);

    }
  }

  /* =========================================================
     INIT
  ========================================================= */

  useEffect(() => {

    load(true);

  }, [activeUniverse]);

  /* =========================================================
     BADGES
  ========================================================= */

  function handleBadgeClick(
    badge: FeedBadge
  ) {

    const value =
      badge.label;

    if (!value) return;

    setQuery(value);

    window.scrollTo({
      top: 0,
    });

    load(true, value);
  }

  /* =========================================================
     SELECTION
  ========================================================= */

  function toggleSelect(
    item: FeedItem
  ) {

    toggleContent(item);
  }

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
            News
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
              Tous
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

        <div className="
          flex
          items-center
          gap-3
        ">

          <input
            value={query}
            onChange={(e) =>
              setQuery(
                e.target.value
              )
            }
            onKeyDown={(e) => {

              if (e.key === "Enter") {

                load(
                  true,
                  query
                );
              }
            }}
            placeholder="
              Rechercher (Amazon, CTV, Retail media...)
            "
            className="
              flex-1
              h-11
              border
              border-gray-200
              rounded-xl
              px-4
              text-sm
              bg-white
              focus:outline-none
              focus:ring-2
              focus:ring-gray-200
            "
          />

          <button
            onClick={() =>
              load(true, query)
            }
            className="
              h-11
              px-5
              rounded-xl
              bg-black
              text-white
              text-sm
              font-medium
              hover:opacity-90
              transition
            "
          >
            Rechercher
          </button>

        </div>

        {/* ===================================================
            RESULTS
        =================================================== */}

        <div className="
          flex
          items-center
          justify-between
        ">

          <div className="
            text-sm
            font-semibold
            text-gray-700
          ">
            Results
          </div>

          <div className="
            text-xs
            text-gray-400
          ">
            {total} results
          </div>

        </div>

        {/* ===================================================
            NEWS LIST
        =================================================== */}

        <NewsList
          items={items}
          loading={loading}
          hasMore={hasMore}
          selectedIds={selectedIds}
          onToggleSelect={
            toggleSelect
          }
          onClickBadge={
            handleBadgeClick
          }
          onLoadMore={() =>
            load(false)
          }
        />

      </div>

    </div>
  );
}
