"use client";

import { useEffect, useRef, useState } from "react";
import { useSearchParams } from "next/navigation";
import { useDrawer } from "@/contexts/DrawerContext";
import SolutionCard from "@/components/solutions/SolutionCard";

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

function sortSolutions(items: Solution[], mode: SortMode) {
  const copy = [...items];

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

function groupByUniverse(solutions: Solution[], mode: SortMode) {
  const map: Record<string, Solution[]> = {};

  solutions.forEach((s) => {
    (s.universes || []).forEach((u) => {
      if (!map[u]) map[u] = [];
      map[u].push(s);
    });
  });

  Object.keys(map).forEach((u) => {
    map[u] = sortSolutions(map[u], mode);
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
  const [loadingId, setLoadingId] = useState<string | null>(null);

  const { openLeftDrawer, setOnLeftClose } = useDrawer();
  const searchParams = useSearchParams();

  const lastOpenedId = useRef<string | null>(null);

  /* ---------------------------------------------------------
     LOAD
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
     DRAWER OPEN
  --------------------------------------------------------- */

  useEffect(() => {
    const solutionId = searchParams.get("solution_id");

    if (!solutionId) {
      lastOpenedId.current = null;
      return;
    }

    if (lastOpenedId.current === solutionId) return;

    lastOpenedId.current = solutionId;
    openLeftDrawer("solution", solutionId);
  }, [searchParams, openLeftDrawer]);

  /* ---------------------------------------------------------
     🔥 RESET LOADING (FIX CRITIQUE)
  --------------------------------------------------------- */

  useEffect(() => {
    setOnLeftClose(() => {
      setLoadingId(null);
    });

    return () => setOnLeftClose(null);
  }, [setOnLeftClose]);

  /* ---------------------------------------------------------
     AUTO OPEN
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

  const grouped = groupByUniverse(solutions, sortMode);
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
            Produits
          </h1>
          <p className="text-sm text-gray-500">
            Explore les produits du marché
          </p>
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

      {loading && (
        <p className="text-sm text-gray-400">
          Chargement des produits...
        </p>
      )}

      {!loading && !hasContent && (
        <p className="text-sm text-gray-400">
          Aucune solution disponible.
        </p>
      )}

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
                  <span className={`
                    transition-transform
                    ${openUniverses[universe] ? "rotate-90" : ""}
                  `}>
                    ▶
                  </span>
                </div>
              </div>

              {openUniverses[universe] && (
                <div className="pt-2">
                  <div className="grid grid-cols-3 sm:grid-cols-4 md:grid-cols-6 lg:grid-cols-7 xl:grid-cols-8 gap-3">
                    {items.map((s) => (
                      <SolutionCard
                        key={s.id_solution}
                        id={s.id_solution}
                        name={s.name}
                        visualRectId={s.media_logo_rectangle_id}
                        nbAnalyses={s.nb_analyses}
                        delta30d={s.delta_30d}
                        isPartner={s.is_partner}

                        // 🔥 NEW
                        isLoading={loadingId === s.id_solution}
                        onClick={() => setLoadingId(s.id_solution)}
                      />
                    ))}
                  </div>
                </div>
              )}

            </section>
          ))}

    </div>
  );
}
