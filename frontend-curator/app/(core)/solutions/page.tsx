"use client";

import {
  useEffect,
  useState,
} from "react";

import {
  useSearchParams,
} from "next/navigation";

import {
  useEntityDrawer,
} from "@/hooks/useEntityDrawer";

import SolutionCard from "@/components/solutions/SolutionCard";
import FavoritesStrip from "@/components/favorites/FavoritesStrip";

import {
  api,
} from "@/lib/api";

export const dynamic =
  "force-dynamic";

const MAX_FAVORITES = 10;

/* =========================================================
   TYPES
========================================================= */

type Solution = {

  id_solution: string;

  name: string;

  media_logo_rectangle_id?:
    string | null;

  logo_type?:
    "solution" | "company";

  content_count: number;

  is_partner?: boolean;

  universes: string[];

};

/* =========================================================
   FETCH
========================================================= */

async function fetchSolutions():
  Promise<Solution[]> {

  try {

    const json =
      await api.get(
        "/solution/list-curator",
      );

    const data =
      json?.solutions ?? [];

    if (!Array.isArray(data)) {

      return [];

    }

    return data.map(
      (solution: any) => ({

        id_solution:
          solution.id_solution,

        name:
          solution.name,

        media_logo_rectangle_id:
          solution.media_logo_rectangle_id,

        logo_type:
          solution.logo_type,

        content_count:
          solution.content_count ?? 0,

        is_partner:
          solution.is_partner ?? false,

        universes:
          solution.universes ?? [],

      }),
    );

  } catch (e) {

    console.error(
      "❌ fetchSolutions error:",
      e,
    );

    return [];

  }

}

/* =========================================================
   SORT
========================================================= */

function sortSolutions(
  solutions: Solution[],
): Solution[] {

  return [...solutions].sort(
    (a, b) =>
      a.name.localeCompare(
        b.name,
        "fr",
        {
          sensitivity:
            "base",
        },
      ),
  );

}

/* =========================================================
   GROUP
========================================================= */

function groupByUniverse(
  solutions: Solution[],
) {

  const map:
    Record<
      string,
      Solution[]
    > = {};

  solutions.forEach(
    (solution) => {

      (
        solution.universes
        || []
      ).forEach(
        (universe) => {

          if (!map[universe]) {

            map[universe] = [];

          }

          map[universe].push(
            solution,
          );

        },
      );

    },
  );

  Object.keys(
    map,
  ).forEach(
    (universe) => {

      map[universe] =
        sortSolutions(
          map[universe],
        );

    },
  );

  return map;

}

/* =========================================================
   PAGE
========================================================= */

export default function SolutionsPage() {

  const [
    solutions,
    setSolutions,
  ] = useState<Solution[]>([]);

  const [
    favorites,
    setFavorites,
  ] = useState<string[]>([]);

  const [
    totalFavorites,
    setTotalFavorites,
  ] = useState(0);

  const [
    favoriteMessage,
    setFavoriteMessage,
  ] = useState<string | null>(
    null,
  );

  const [
    loading,
    setLoading,
  ] = useState(true);

  const [
    openUniverses,
    setOpenUniverses,
  ] = useState<
    Record<string, boolean>
  >({});

  const searchParams =
    useSearchParams();

  const {
    loadingId,
    setLoadingId,
  } = useEntityDrawer(
    "solution",
    "solution_id",
  );

  /* =========================================================
     LOAD
  ========================================================= */

  useEffect(() => {

    async function load() {

      setLoading(
        true,
      );

      try {

        const [
          data,
          prefsRes,
        ] = await Promise.all([

          fetchSolutions(),

          api.get(
            "/user/preferences",
          ),

        ]);

        setSolutions(
          data,
        );

        const companyPrefs =
          Array.isArray(
            prefsRes?.preferences?.COMPANY,
          )
            ? prefsRes.preferences.COMPANY
            : [];

        const topicPrefs =
          Array.isArray(
            prefsRes?.preferences?.TOPIC,
          )
            ? prefsRes.preferences.TOPIC
            : [];

        const solutionPrefs =
          Array.isArray(
            prefsRes?.preferences?.SOLUTION,
          )
            ? prefsRes.preferences.SOLUTION
            : [];

        setFavorites(
          solutionPrefs,
        );

        setTotalFavorites(
          companyPrefs.length +
          topicPrefs.length +
          solutionPrefs.length,
        );

      } catch (e) {

        console.error(
          "❌ Solutions load error:",
          e,
        );

        setSolutions(
          [],
        );

        setFavorites(
          [],
        );

        setTotalFavorites(
          0,
        );

      } finally {

        setLoading(
          false,
        );

      }

    }

    load();

  }, []);

  /* =========================================================
     AUTO OPEN CURRENT UNIVERSE
  ========================================================= */

  useEffect(() => {

    const solutionId =
      searchParams.get(
        "solution_id",
      );

    if (!solutionId) {

      return;

    }

    const solution =
      solutions.find(
        (item) =>
          item.id_solution
          === solutionId,
      );

    if (!solution) {

      return;

    }

    const universe =
      solution.universes?.[0];

    if (!universe) {

      return;

    }

    setOpenUniverses(
      (previous) => ({

        ...previous,

        [universe]:
          true,

      }),
    );

  }, [
    solutions,
    searchParams,
  ]);

  /* =========================================================
     FAVORITE LIMIT MESSAGE
  ========================================================= */

  function showFavoriteLimitMessage() {

    setFavoriteMessage(
      `You can select up to ${MAX_FAVORITES} favorites.`,
    );

    window.setTimeout(
      () => {

        setFavoriteMessage(
          null,
        );

      },
      2500,
    );

  }

  /* =========================================================
     TOGGLE FAVORITE
  ========================================================= */

  async function handleToggleFavorite(
    id: string,
    isFavorite: boolean,
  ) {

    try {

      if (isFavorite) {

        await api.post(
          "/user/preferences/remove",
          {
            type: "SOLUTION",
            value_id: id,
          },
        );

      } else {

        if (
          totalFavorites >=
          MAX_FAVORITES
        ) {

          showFavoriteLimitMessage();

          return;

        }

        await api.post(
          "/user/preferences/add",
          {
            type: "SOLUTION",
            value_id: id,
          },
        );

      }

      setFavorites(
        (previous) =>
          isFavorite
            ? previous.filter(
                (value) =>
                  value !== id,
              )
            : [
                ...previous,
                id,
              ],
      );

      setTotalFavorites(
        (previous) =>
          isFavorite
            ? Math.max(
                0,
                previous - 1,
              )
            : Math.min(
                MAX_FAVORITES,
                previous + 1,
              ),
      );

    } catch (e) {

      console.error(
        "❌ favorite error",
        e,
      );

    }

  }

  /* =========================================================
     HELPERS
  ========================================================= */

  function toggleUniverse(
    universe: string,
  ) {

    setOpenUniverses(
      (previous) => ({

        ...previous,

        [universe]:
          !previous[universe],

      }),
    );

  }

  /* =========================================================
     DATA
  ========================================================= */

  const maxFavoritesReached =
    totalFavorites >= MAX_FAVORITES;

  const favoriteSolutions =
    sortSolutions(
      solutions.filter(
        (solution) =>
          favorites.includes(
            solution.id_solution,
          ),
      ),
    );

  const otherSolutions =
    solutions.filter(
      (solution) =>
        !favorites.includes(
          solution.id_solution,
        ),
    );

  const groupedSolutions =
    groupByUniverse(
      otherSolutions,
    );

  const hasContent =
    solutions.length > 0;

  /* =========================================================
     RENDER
  ========================================================= */

  return (

    <div className="
      space-y-8
    ">

      {/* =====================================================
          HEADER
      ===================================================== */}

      <div>

        <h1 className="
          text-lg
          font-semibold
          text-gray-900
        ">
          Solutions
        </h1>

      </div>

      {/* =====================================================
          FAVORITE MESSAGE
      ===================================================== */}

      {favoriteMessage && (

        <div className="
          rounded-lg
          border
          border-amber-200
          bg-amber-50
          px-4
          py-3
          text-sm
          text-amber-700
        ">

          {favoriteMessage}

        </div>

      )}

      {/* =====================================================
          LOADING
      ===================================================== */}

      {loading && (

        <p className="
          text-sm
          text-gray-400
        ">
          Loading solutions...
        </p>

      )}

      {/* =====================================================
          FAVORITES
      ===================================================== */}

      {!loading
        && favoriteSolutions.length > 0
        && (

        <FavoritesStrip>

          <div className="
            grid
            grid-cols-3
            sm:grid-cols-4
            md:grid-cols-6
            lg:grid-cols-7
            xl:grid-cols-8
            gap-3
          ">

            {favoriteSolutions.map(
              (solution) => (

                <SolutionCard

                  key={
                    solution.id_solution
                  }

                  id={
                    solution.id_solution
                  }

                  name={
                    solution.name
                  }

                  visualRectId={
                    solution.media_logo_rectangle_id
                  }

                  contentCount={
                    solution.content_count
                  }

                  visualType={
                    solution.logo_type
                  }

                  isPartner={
                    solution.is_partner
                  }

                  isLoading={
                    loadingId
                    === solution.id_solution
                  }

                  onClick={() =>
                    setLoadingId(
                      solution.id_solution,
                    )
                  }

                  isFavorite

                  onToggleFavorite={() =>
                    handleToggleFavorite(
                      solution.id_solution,
                      true,
                    )
                  }

                />

              ),
            )}

          </div>

        </FavoritesStrip>

      )}

      {/* =====================================================
          OTHER SOLUTIONS
      ===================================================== */}

      {!loading
        && hasContent
        && Object.entries(
          groupedSolutions,
        )
          .sort(
            ([a], [b]) =>
              a.localeCompare(
                b,
              ),
          )
          .map(
            ([
              universe,
              items,
            ]) => (

              <section

                key={
                  universe
                }

                className="
                  space-y-2
                "

              >

                <div

                  onClick={() =>
                    toggleUniverse(
                      universe,
                    )
                  }

                  className="
                    flex
                    items-center
                    justify-between
                    cursor-pointer
                    py-2
                    px-1
                    border-b
                    border-gray-100
                    hover:bg-gray-50
                  "

                >

                  <h2 className="
                    text-xs
                    font-semibold
                    uppercase
                    text-gray-500
                  ">

                    {universe}

                  </h2>

                  <span className="
                    text-xs
                    text-gray-400
                  ">

                    {items.length}

                  </span>

                </div>

                {openUniverses[
                  universe
                ] && (

                  <div className="
                    grid
                    grid-cols-3
                    sm:grid-cols-4
                    md:grid-cols-6
                    lg:grid-cols-7
                    xl:grid-cols-8
                    gap-3
                    pt-2
                  ">

                    {items.map(
                      (solution) => {

                        const isFavorite =
                          favorites.includes(
                            solution.id_solution,
                          );

                        return (

                          <SolutionCard

                            key={
                              solution.id_solution
                            }

                            id={
                              solution.id_solution
                            }

                            name={
                              solution.name
                            }

                            contentCount={
                              solution.content_count
                            }

                            visualRectId={
                              solution.media_logo_rectangle_id
                            }

                            visualType={
                              solution.logo_type
                            }

                            isPartner={
                              solution.is_partner
                            }

                            isLoading={
                              loadingId
                              === solution.id_solution
                            }

                            onClick={() =>
                              setLoadingId(
                                solution.id_solution,
                              )
                            }

                            isFavorite={
                              isFavorite
                            }

                            maxFavoritesReached={
                              maxFavoritesReached
                            }

                            onFavoriteLimitReached={
                              showFavoriteLimitMessage
                            }

                            onToggleFavorite={() =>
                              handleToggleFavorite(
                                solution.id_solution,
                                isFavorite,
                              )
                            }

                          />

                        );

                      },
                    )}

                  </div>

                )}

              </section>

            ),
          )}

    </div>

  );

}
