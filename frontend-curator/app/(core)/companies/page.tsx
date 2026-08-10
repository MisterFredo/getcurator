"use client";

import { useEffect, useState } from "react";
import { useSearchParams } from "next/navigation";
import { useEntityDrawer } from "@/hooks/useEntityDrawer";
import CompanyCard from "@/components/companies/CompanyCard";
import FavoritesStrip from "@/components/favorites/FavoritesStrip";
import { api } from "@/lib/api";

export const dynamic = "force-dynamic";
export const fetchCache = "force-no-store";

/* ========================================================= */

type Company = {
  id_company: string;
  name: string;
  media_logo_rectangle_id?: string | null;
  nb_analyses: number;
  delta_30d: number;
  universes: string[];
};

type SortMode = "alpha" | "activity" | "growth";

/* =========================================================
   FETCH
========================================================= */

async function fetchCompanies(): Promise<Company[]> {
  try {
    const json = await api.get("/company/list-curator");

    const data = json?.companies ?? [];

    if (!Array.isArray(data)) return [];

    return data.map((c: any) => ({
      id_company: c.id_company,
      name: c.name,
      media_logo_rectangle_id: c.media_logo_rectangle_id,
      nb_analyses: c.nb_analyses ?? 0,
      delta_30d: c.delta_30d ?? 0,
      universes: c.universes ?? [],
    }));

  } catch (e: any) {
    console.error("❌ fetchCompanies error:", e);

    if (e?.message?.includes("401")) {
      window.location.href = "/login";
    }

    return [];
  }
}

/* =========================================================
   SORT
========================================================= */

function sortCompanies(companies: Company[], mode: SortMode): Company[] {
  const copy = [...companies];

  switch (mode) {
    case "activity":
      return copy.sort((a, b) => b.nb_analyses - a.nb_analyses);
    case "growth":
      return copy.sort((a, b) => b.delta_30d - a.delta_30d);
    default:
      return copy.sort((a, b) => a.name.localeCompare(b.name));
  }
}

/* =========================================================
   GROUP
========================================================= */

function groupByUniverse(companies: Company[], mode: SortMode) {
  const map: Record<string, Company[]> = {};

  companies.forEach((c) => {
    (c.universes || []).forEach((u) => {
      if (!map[u]) map[u] = [];
      map[u].push(c);
    });
  });

  Object.keys(map).forEach((u) => {
    map[u] = sortCompanies(map[u], mode);
  });

  return map;
}

/* =========================================================
   PAGE
========================================================= */

export default function CompaniesPage() {
  const [companies, setCompanies] = useState<Company[]>([]);
  const [preferences, setPreferences] = useState<string[]>([]);
  const [loading, setLoading] = useState(true);
  const [ready, setReady] = useState(false);
  const [sortMode, setSortMode] = useState<SortMode>("alpha");

  const [openUniverses, setOpenUniverses] = useState<Record<string, boolean>>({});

  const searchParams = useSearchParams();

  const { loadingId } = useEntityDrawer(
    "company",
    "company_id"
  );

  /* ---------------------------------------------------------
     AUTH
  --------------------------------------------------------- */

  useEffect(() => {
    const userId = localStorage.getItem("user_id");

    if (!userId) {
      window.location.href = "/login";
      return;
    }

    setReady(true);
  }, []);

  /* ---------------------------------------------------------
     LOAD
  --------------------------------------------------------- */

  useEffect(() => {
    if (!ready) return;

    const userId = localStorage.getItem("user_id");
    if (!userId) return;

    async function load() {
      setLoading(true);

      try {
        const [data, prefsRes] = await Promise.all([
          fetchCompanies(),
          api.get("/user/preferences"),
        ]);

        setCompanies(data);

        const companyPrefs =
          Array.isArray(prefsRes?.preferences?.COMPANY)
            ? prefsRes.preferences.COMPANY
            : [];

        setPreferences(companyPrefs);

      } catch (e) {
        console.error("❌ load error:", e);
        setCompanies([]);
        setPreferences([]);
      }

      setLoading(false);
    }

    load();
  }, [ready]);

  /* ---------------------------------------------------------
     AUTO OPEN CURRENT UNIVERSE
  --------------------------------------------------------- */

  useEffect(() => {
    const companyId = searchParams.get("company_id");
    if (!companyId) return;

    const comp = companies.find((c) => c.id_company === companyId);
    if (!comp) return;

    const universe = comp.universes?.[0];
    if (!universe) return;

    setOpenUniverses((prev) => ({
      ...prev,
      [universe]: true,
    }));
  }, [companies, searchParams]);

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
     DATA (🔥 FIX UX)
  --------------------------------------------------------- */

  const favorites = companies.filter(c =>
    preferences.includes(c.id_company)
  );

  const others = companies.filter(c =>
    !preferences.includes(c.id_company)
  );

  const groupedOthers = groupByUniverse(others, sortMode);

  const hasContent = companies.length > 0;

  if (!ready) {
    return (
      <div className="p-6 text-sm text-gray-400">
        Chargement…
      </div>
    );
  }

  /* =========================================================
     RENDER
  ========================================================= */

  return (
    <div className="space-y-8">

      {/* HEADER */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-lg font-semibold text-gray-900">
            Companies
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

      {/* LOADING */}
      {loading && (
        <p className="text-sm text-gray-400">
          Chargement des sociétés...
        </p>
      )}

      {/* ⭐ FAVORITES */}
      {!loading && favorites.length > 0 && (
        <FavoritesStrip>
          <div className="grid grid-cols-3 sm:grid-cols-4 md:grid-cols-6 lg:grid-cols-7 xl:grid-cols-8 gap-3">
            {sortCompanies(favorites, sortMode).map((c) => (
              <CompanyCard
                key={c.id_company}
                id={c.id_company}
                name={c.name}
                visualRectId={c.media_logo_rectangle_id}
                totalAnalyses={c.nb_analyses}
                delta30d={c.delta_30d}
                isLoading={loadingId === c.id_company}
                isFavorite
                onToggleFavorite={(id, isFav) => {
                  setPreferences((prev) =>
                    isFav
                      ? prev.filter((p) => p !== id)
                      : [...prev, id]
                  );
                }}
              />
            ))}
          </div>
        </FavoritesStrip>
      )}

      {/* AUTRES */}
      {!loading && hasContent &&
        Object.entries(groupedOthers)
          .sort(([a], [b]) => a.localeCompare(b))
          .map(([universe, items]) => (
            <section key={universe} className="space-y-2">

              <div
                onClick={() => toggleUniverse(universe)}
                className="flex items-center justify-between cursor-pointer py-2 px-1 border-b border-gray-100 hover:bg-gray-50"
              >
                <h2 className="text-xs font-semibold uppercase text-gray-500">
                  {universe}
                </h2>

                <span>{items.length}</span>
              </div>

              {openUniverses[universe] && (
                <div className="grid grid-cols-3 sm:grid-cols-4 md:grid-cols-6 lg:grid-cols-7 xl:grid-cols-8 gap-3 pt-2">
                  {items.map((c) => (
                    <CompanyCard
                      key={c.id_company}
                      id={c.id_company}
                      name={c.name}
                      visualRectId={c.media_logo_rectangle_id}
                      totalAnalyses={c.nb_analyses}
                      delta30d={c.delta_30d}
                      isLoading={loadingId === c.id_company}
                      isFavorite={preferences.includes(c.id_company)}
                      onToggleFavorite={(id, isFav) => {
                        setPreferences((prev) =>
                          isFav
                            ? prev.filter((p) => p !== id)
                            : [...prev, id]
                        );
                      }}
                    />
                  ))}
                </div>
              )}

            </section>
          ))}

    </div>
  );
}
