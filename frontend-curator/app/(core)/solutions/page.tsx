"use client";

import { useEffect, useState } from "react";
import { useSearchParams } from "next/navigation";
import { useEntityDrawer } from "@/hooks/useEntityDrawer";
import SolutionCard from "@/components/solutions/SolutionCard";
import FavoritesStrip from "@/components/favorites/FavoritesStrip";
import { api } from "@/lib/api"; // 🔥 NEW

export const dynamic = "force-dynamic";

/* ========================================================= */

type Solution = {
  id_solution: string;
  name: string;
  media_logo_rectangle_id?: string | null;
  nb_analyses: number;
  delta_30d: number;
  is_partner?: boolean;
  universes?: string[];
};

type SortMode = "alpha" | "activity" | "growth";

/* =========================================================
   SORT
========================================================= */

function sortSolutions(items: Solution[], mode: SortMode, favorites: string[]) {
  const copy = [...items];

  // 🔥 PRIORITÉ FAVORIS
  copy.sort((a, b) => {
    const aFav = favorites.includes(a.id_solution);
    const bFav = favorites.includes(b.id_solution);

    if (aFav && !bFav) return -1;
    if (!aFav && bFav) return 1;
    return 0;
  });

  // 🔥 TRI CLASSIQUE
  switch (mode) {
    case "activity":
      return copy.sort((a, b) => (b.nb_analyses ?? 0) - (a.nb_analyses ?? 0));
    case "growth":
      return copy.sort((a, b) => (b.delta_30d ?? 0) - (a.delta_30d ?? 0));
    default:
      return copy.sort((a, b) =>
        a.name.localeCompare(b.name, "fr", { sensitivity: "base" })
      );
  }
}

/* =========================================================
   GROUP
========================================================= */

function groupByUniverse(solutions: Solution[], mode: SortMode, favorites: string[]) {
  const map: Record<string, Solution[]> = {};

  solutions.forEach((s) => {
    (s.universes || []).forEach((u) => {
      if (!map[u]) map[u] = [];
      map[u].push(s);
    });
  });

  Object.keys(map).forEach((u) => {
    map[u] = sortSolutions(map[u], mode, favorites);
  });

  return map;
}

/* =========================================================
   FETCH
========================================================= */

async function fetchSolutions(): Promise<Solution[]> {
  try {
    const userId = localStorage.getItem("user_id");

    if (!userId) {
      window.location.href = "/login";
      return [];
    }

    const res = await fetch(
      `${process.env.NEXT_PUBLIC_API_URL}/solution/list-curator`,
      {
        method: "GET",
        headers: {
          "Content-Type": "application/json",
          "x-user-id": userId,
        },
        cache: "no-store",
      }
    );

    if (!res.ok) return [];

    const json = await res.json();
    if (json.status !== "ok") return [];

    return (json.solutions || []).map((s: any) => ({
      id_solution: s.id_solution ?? s.ID_SOLUTION,
      name: s.name ?? s.NAME,
      media_logo_rectangle_id:
        s.media_logo_rectangle_id ?? s.MEDIA_LOGO_RECTANGLE_ID,
      nb_analyses: s.nb_analyses ?? s.NB_ANALYSES ?? 0,
      delta_30d: s.delta_30d ?? s.DELTA_30D ?? 0,
      is_partner: s.is_partner ?? s.IS_PARTNER ?? false,
      universes: s.universes ?? [],
    }));

  } catch (e) {
    console.error("❌ fetchSolutions error:", e);
    return [];
  }
}

/* =========================================================
   PAGE
========================================================= */

export default function SolutionsPage() {

  const [solutions, setSolutions] = useState<Solution[]>([]);
  const [loading, setLoading] = useState(true);
  const [sortMode, setSortMode] = useState<SortMode>("alpha");

  const [openUniverses, setOpenUniverses] = useState<Record<string, boolean>>({});

  // 🔥 NEW
  const [favorites, setFavorites] = useState<string[]>([]);

  const searchParams = useSearchParams();

  const { loadingId, setLoadingId } = useEntityDrawer(
    "solution",
    "solution_id"
  );

  /* ---------------------------------------------------------
     LOAD DATA
  --------------------------------------------------------- */

  useEffect(() => {
    async function load() {
      setLoading(true);
      const data = await fetchSolutions();
      setSolutions(data);
      setLoading(false);
    }

    load();
  }, []);

  /* ---------------------------------------------------------
     LOAD PREFS
  --------------------------------------------------------- */

  useEffect(() => {
    async function loadPrefs() {
      try {
        const res = await api.get("/user/preferences");

        const solPrefs =
          Array.isArray(res?.preferences?.SOLUTION)
            ? res.preferences.SOLUTION
            : [];

        setFavorites(solPrefs);

      } catch (e) {
        console.error("❌ prefs error", e);
      }
    }

    loadPrefs();
  }, []);

  /* ---------------------------------------------------------
     AUTO OPEN CURRENT
  --------------------------------------------------------- */

  useEffect(() => {
    const solutionId = searchParams.get("solution_id");
    if (!solutionId) return;

    const sol = solutions.find((s) => s.id_solution === solutionId);
    if (!sol) return;

    const universe = sol.universes?.[0];
    if (!universe) return;

    setOpenUniverses((prev) => ({
      ...prev,
      [universe]: true,
    }));
  }, [solutions, searchParams]);

  /* ---------------------------------------------------------
     FAVORITE TOGGLE
  --------------------------------------------------------- */

  async function handleToggleFavorite(id: string, isFav: boolean) {

    try {

      if (isFav) {
        await api.post("/user/preferences/remove", {
          type: "SOLUTION",
          value_id: id,
        });
      } else {
        await api.post("/user/preferences/add", {
          type: "SOLUTION",
          value_id: id,
        });
      }

      setFavorites((prev) =>
        isFav
          ? prev.filter((p) => p !== id)
          : [...prev, id]
      );

    } catch (e) {
      console.error("❌ favorite error", e);
    }
  }

  /* ---------------------------------------------------------
     HELPERS
  --------------------------------------------------------- */

  function toggleUniverse(u: string) {
    setOpenUniverses((prev) => ({
      ...prev,
      [u]: !prev[u],
    }));
  }

  /* ---------------------------------------------------------
     DATA
  --------------------------------------------------------- */

  const favoriteSolutions = solutions.filter((s) =>
    favorites.includes(s.id_solution)
  );

  const otherSolutions = solutions.filter((s) =>
    !favorites.includes(s.id_solution)
  );

  const grouped = groupByUniverse(otherSolutions, sortMode, favorites);
  const hasContent = solutions.length > 0;

  /* =========================================================
     RENDER
  ========================================================= */

  return (
    <div className="space-y-8">

      {/* HEADER */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-lg font-semibold text-gray-900">
            Solutions
          </h1>
        </div>

        <div className="flex gap-2 text-xs">
          {[
            { key: "alpha", label: "A → Z" },
            { key: "activity", label: "Activité" },
            { key: "growth", label: "Croissance" },
          ].map((s) => (
            <button
              key={s.key}
              onClick={() => setSortMode(s.key as SortMode)}
              className={`
                px-3 py-1 rounded border
                ${
                  sortMode === s.key
                    ? "bg-teal-600 text-white border-teal-600"
                    : "bg-white text-gray-600 border-gray-200 hover:bg-gray-50"
                }
              `}
            >
              {s.label}
            </button>
          ))}
        </div>
      </div>

      {/* ⭐ FAVORITES */}

      {!loading && favoriteSolutions.length > 0 && (
        <section className="space-y-2">

          <h2 className="text-xs font-semibold uppercase text-gray-500">
            Favoris
          </h2>

          <div className="grid grid-cols-3 sm:grid-cols-4 md:grid-cols-6 lg:grid-cols-7 xl:grid-cols-8 gap-3">

            {sortSolutions(
              favoriteSolutions,
              sortMode,
              favorites
            ).map((s) => {

              const isFav =
                favorites.includes(s.id_solution);

              return (
                <SolutionCard
                  key={s.id_solution}
                  id={s.id_solution}
                  name={s.name}
                  visualRectId={s.media_logo_rectangle_id}
                  nbAnalyses={s.nb_analyses}
                  delta30d={s.delta_30d}
                  isPartner={s.is_partner}
                  isLoading={loadingId === s.id_solution}
                  onClick={() =>
                    setLoadingId(s.id_solution)
                  }

                  isFavorite={isFav}

                  onToggleFavorite={() =>
                    handleToggleFavorite(
                      s.id_solution,
                      isFav
                    )
                  }
                />
              );
            })}

          </div>

        </section>
      )}

      {/* CONTENT */}
      {!loading && hasContent &&
        Object.entries(grouped)
          .sort(([a], [b]) => a.localeCompare(b))
          .map(([universe, items]) => (
            <section key={universe} className="space-y-2">

              <div
                onClick={() => toggleUniverse(universe)}
                className="
                  flex items-center justify-between
                  cursor-pointer
                  py-2 px-1
                  border-b border-gray-100
                  hover:bg-gray-50
                "
              >
                <h2 className="text-xs font-semibold uppercase text-gray-500">
                  {universe}
                </h2>

                <div className="flex items-center gap-2 text-xs text-gray-400">
                  <span>{items.length}</span>
                </div>
              </div>

              {openUniverses[universe] && (
                <div className="pt-2">
                  <div className="grid grid-cols-3 sm:grid-cols-4 md:grid-cols-6 lg:grid-cols-7 xl:grid-cols-8 gap-3">
                    {items.map((s) => {

                      const isFav = favorites.includes(s.id_solution);

                      return (
                        <SolutionCard
                          key={s.id_solution}
                          id={s.id_solution}
                          name={s.name}
                          visualRectId={s.media_logo_rectangle_id}
                          nbAnalyses={s.nb_analyses}
                          delta30d={s.delta_30d}
                          isPartner={s.is_partner}
                          isLoading={loadingId === s.id_solution}
                          onClick={() => setLoadingId(s.id_solution)}

                          // 🔥 NEW
                          isFavorite={isFav}
                          onToggleFavorite={() =>
                            handleToggleFavorite(s.id_solution, isFav)
                          }
                        />
                      );
                    })}
                  </div>
                </div>
              )}

            </section>
          ))}

    </div>
  );
}
